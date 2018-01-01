import numpy as np
import pygame
import threading
from enum import Enum
import sys

class ActionMap(Enum):
    left = 0
    right = 1
    rotate = 2
    speedup = 3
    noAction = 4


class Environment(object):
    '''
    1. recieve block
    2. check if rows of block'position is full, if full, eliminate and update
    3. check if block has reach bottom
    '''
    def __init__(self, height, width, updatecallback):
        self.width = width
        self.height = height
        self.type_num = 6
        self.background = np.zeros((height, width), dtype=int) # except current block
        self.spaces = np.zeros((height, width), dtype=int) # add block when it reaches floor
        self.moving_block = False
        self.scores = 0
        self.network_scores = 0
        self.gameover = False
        self.timer = None
        self.lock = threading.Lock()
        self.fall_period = 0.03
        self.block = None
        self.updatecallback = updatecallback
        self.generate_new_block()

    def generate_new_block(self):
        if self.timer:
            self.timer.cancel()
        block_type = np.random.randint(self.type_num)
        direction = np.random.randint(5)
        if block_type == 0:
            self.block = LongBlock(self.width / 2, 2, direction)
        elif block_type == 1:
            self.block = SquareBlock(self.width / 2, 2, direction)
        elif block_type == 2:
            self.block = FBlock(self.width / 2, 2, direction)
        elif block_type == 3:
            self.block = ZBlock(self.width / 2, 2, direction)
        elif block_type == 4:
            self.block = TBlock(self.width / 2, 2, direction)
        elif block_type == 5:
            self.block = LBlock(self.width / 2, 2, direction)
        self._falldown()

    def takeAction(self, action):
        '''
        1. move the block according action
        2. update matrix
        '''
        if action == ActionMap.noAction:
            return 
        if action == ActionMap.speedup:
            for _ in range(3):
                if self.falldown():
                    break
        else:
            self.network_scores -= 20
            self.lock.acquire()
            self.move_collision_check(self.block, action)
            self.lock.release()
        self.updateEnvironment()
        
    def updateEnvironment(self):
        # update callback
        self.updatecallback(self.spaces)
    
    def getGameState(self):
        return self.spaces, self.network_scores, self.gameover 
        
    def falldown(self):
        """
        return True if block has reached bottom
        """
        self.lock.acquire()
        self.block.y -= 1

        flag = False
        if self.check_reach_bottom():
            # has reached bottom, restore y
            self.block.y += 1
            print self.block.y
            self.network_scores -= 2 * (self.block.y)
            # eliminate only when block reach bottom!!
            last_row = self.block.centor[0] -self.block.y

            self.check_and_eliminate(range(last_row, last_row - self.block.realValues.shape[0], -1))

            self.background = np.copy(self.spaces)
            # check game over or not
            for j in range(self.width):
                if self.background[0, j] != 0:
                    self.gameover = True
                    self.timer.cancel()
                    print '--------game over--------------'
                    break
            self.lock.release()
            if self.gameover is False:
                self.generate_new_block()
            flag = True

        if self.gameover is False:
            self.updateSpace(self.block)
            self.updateEnvironment()

        if flag is False:
            self.lock.release()
        return flag

    def move_collision_check(self, block, action):
        # take action, check if two matrix collapse
        # return 1 if collision, return 0 if not
        if action == ActionMap.left or action == ActionMap.right:
            block.move(action)
        elif action == ActionMap.rotate:
            block.changeDirection(1)
        elif action == ActionMap.noAction:
            pass
    
        last_row = block.centor[0] -block.y
        first_row = last_row - block.realValues.shape[0] + 1
        first_col = block.x - block.centor[1]
        last_col = block.x - block.centor[1] + block.realValues.shape[1] - 1

        collapse_flag = False

        for i, row in enumerate(range(max(0, first_row), min(self.height, last_row + 1))):
            for j, col in enumerate(range(max(0, first_col), min(self.width, last_col + 1))):
                if self.background[row, col] and block.realValues[i, j]:
                    # collapse
                    collapse_flag = True
                
        # check if the action is leagal, restore
        if first_col < 0 or last_col >= self.width or last_row >= self.height or collapse_flag:
            if action == ActionMap.left:
                block.move(ActionMap.right)
            elif action == ActionMap.right:
                block.move(ActionMap.left)
            elif action == ActionMap.rotate:
                block.changeDirection(-1)
            else:
                raise Exception('Wrong action!!')
            return 1
            
        self.updateSpace(block)

    def updateSpace(self, block):
        '''
        update space matrix
        block: block array
        centor: centor of array(row, column)
        pos: block's centor position in bg(x, y)
        bg: bg array
        '''
        # block's position in background
        last_row = block.centor[0] -block.y
        first_row = last_row - block.realValues.shape[0] + 1
        first_col = block.x - block.centor[1]
        last_col = block.x - block.centor[1] + block.realValues.shape[1] - 1
        value = np.copy(self.background)

        # add to background
        for i, row in enumerate(range(first_row, last_row + 1)):
            if row < 0:
                continue
            for j, col in enumerate(range(first_col, last_col + 1)):
                if block.realValues[i, j]: 
                    value[row, col] = block.realValues[i, j] 
        self.spaces = value   

    def check_and_eliminate(self, rows):
        matrix = np.copy(self.spaces)
        for row in rows:
            if self._check_full(row) and row > 0:
                # full and eliminate
                up = matrix[0: row, :]
                if row < self.height - 1:
                    down = matrix[row+1: , :]
                    matrix = np.concatenate((up, down), axis=0)
                else:
                    matrix = np.copy(up)
        eliminated_rows = self.height - matrix.shape[0]
        self.scores += eliminated_rows * 100
        self.network_scores += eliminated_rows * 100
        if eliminated_rows: 
            print self.scores
            self.spaces = np.concatenate((np.zeros((eliminated_rows, self.width), dtype=int), matrix))
    
    def check_reach_bottom(self):
        last_row = self.block.centor[0] -self.block.y
        first_row = last_row - self.block.realValues.shape[0] + 1
        first_col = self.block.x - self.block.centor[1]
        last_col = self.block.x - self.block.centor[1] + self.block.realValues.shape[1] - 1
        if last_row >= self.height:
            return True
        for i, row in enumerate(range(max(0, first_row), min(self.height, last_row + 1))):
            for j, col in enumerate(range(max(0, first_col), min(self.width, last_col + 1))):
                if self.background[row, col] and self.block.realValues[i, j]:
                    # collapse
                    return True
            
        return False

    def _check_full(self, row):
        # return 0 if row-th is not full
        for column in range(self.width):
            if self.spaces[row, column] == 0:
                return 0
        return 1

    def _falldown(self):  
        if self.gameover is False:
            self.timer = threading.Timer(self.fall_period, self._falldown, [])
            self.timer.start()
            self.falldown()

class Block(object):
    def __init__(self, blockType, x, y, direction):
        # x, y is center coordinations according to left up corner of env
        self.blockType = blockType
        self.x = x
        self.y = y
        self.direction = direction
        self.values = np.zeros((5, 5))
        # centor is centor row, column of realValue maxtix
        self.centor = [2, 2]
    
    def _init_values(self):
        for i in range(self.direction):
            self.values = np.rot90(self.values)
    
    def _set_init_position(self):
        # set last row of block to be the first row of env,
        # so centor is self.realValues.shape[0] - self.centor[0]
        self.getRealValue()
        self.y = self.centor[0]
    
    def move(self, action):
        # -1: left, 1: right
        if action is ActionMap.left:
            self.x -= 1
        elif action is ActionMap.right:
            self.x += 1
        else:
            raise Exception('Wrong action!')

    def fall(self):
        if self.y != 0:
            self.y -= 1
    
    def getRealValue(self):
        # centor 
        #print self.values
        self.realValues = None
        self.centor = [2, 2]
        # delete empty row
        row_realValues = None
        flag = False
        for i in range(5):
            if (self.values[i] == np.zeros(5)).all():
                if flag == True:
                    break
                self.centor[0] -= 1
            else:
                flag = True
                tmp = self.values[i].reshape((1, 5))
                if row_realValues is not None:
                    row_realValues = np.concatenate((row_realValues, tmp))
                else:
                    row_realValues = tmp
        # delete empty columns
        flag = False
        for j in range(5):
            if (row_realValues[:, j] == np.zeros(row_realValues.shape[0])).all():
                if flag == True:
                    break
                self.centor[1] -= 1
            else:
                flag = True
                tmp = row_realValues[:, j].reshape((row_realValues.shape[0], 1))
                if self.realValues is not None:
                    self.realValues = np.concatenate((self.realValues,tmp), axis=1)
                else:
                    self.realValues = tmp
    
    def changeDirection(self, ang):
        self.direction += ang
        if ang == 1:
            self.values = np.rot90(self.values, k=-1)
        elif ang == -1:
            self.values = np.rot90(self.values)

        if self.direction == 4:
            self.direction = 0
        self.getRealValue()

class LongBlock(Block):
    def __init__(self, x, y, direction):
        super(LongBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class SquareBlock(Block):
    def __init__(self, x, y, direction):
        super(SquareBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 0, 0, 0),
                                (0, 2, 2, 0, 0),
                                (0, 2, 2, 0, 0),
                                (0, 0, 0, 0, 0),
                                (0, 0, 0, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class FBlock(Block):
    def __init__(self, x, y, direction):
        super(FBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 0, 0, 0),
                                (0, 0, 3, 3, 0),
                                (0, 0, 3, 0, 0),
                                (0, 0, 3, 0, 0),
                                (0, 0, 0, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class TBlock(Block):
    def __init__(self, x, y, direction):
        super(TBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 0, 0, 0),
                                (0, 0, 4, 0, 0),
                                (0, 4, 4, 4, 0),
                                (0, 0, 0, 0, 0),
                                (0, 0, 0, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class ZBlock(Block):
    def __init__(self, x, y, direction):
        super(ZBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 0, 0, 0),
                                (0, 0, 0, 0, 0),
                                (0, 5, 5, 0, 0),
                                (0, 0, 5, 5, 0),
                                (0, 0, 0, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class LBlock(Block):
    def __init__(self, x, y, direction):
        super(LBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 0, 0, 0),
                                (0, 0, 6, 0, 0),
                                (0, 0, 6, 0, 0),
                                (0, 0, 6, 6, 0),
                                (0, 0, 0, 0, 0)), dtype=int)
        self._init_values()
        self._set_init_position()


class GUI(object):
    def __init__(self, height, width):
        pygame.init()
        self.color_map = ((255, 255, 255), (50, 50, 0), (0, 10, 80), 
                          (20, 80, 10), (80, 0, 10), (70, 10, 20), (50, 50, 80))
        self.pixel_size = 20
        self.keyBoard = 0
        self.width = width
        self.height = height

        size = self.width * self.pixel_size, self.height * self.pixel_size
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption('Tetris --by Echo')
    
    def draw(self, matrix):
        self.screen.fill((0, 0, 0))

        # draw matrix
        if matrix.shape != (self.height, self.width):
            return 0
        for row in range(self.height):
            for column in range(self.width):
                value = matrix[row, column]
                if value != 0:
                    baseRect = (column * self.pixel_size, row * self.pixel_size, self.pixel_size, self.pixel_size)
                    color = self.color_map[value]
                    pygame.draw.rect(self.screen, color, baseRect)
        pygame.display.update()
