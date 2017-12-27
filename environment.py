import time, sys
import numpy as np
import pygame
import util

class Environment(object):
    '''
    1. recieve block
    2. check if rows of block'position is full, if full, eliminate and update
    3. check if block has reach bottom
    '''
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.type_num = 4
        self.background = np.zeros((height, width), dtype=int) # except current block
        self.spaces = np.zeros((height, width), dtype=int) # add block when it reaches floor
    
    def generate_new_block(self):
        block_type = np.random.randint(self.type_num)
        direction = np.random.randint(4)
        block = LongBlock(0, 2, direction)
        return block
    
    def updateEnv(self, block):
        # check if block reached the bottom
        # centor of bottom layer: x, y
        size = block.realValues.shape
        #print block.y, size[0] / 2

        # last row
        row = block.y - block.centor[0]
        col_left = block.x - block.centor[1]
        col_right = block.x + size[1] - block.centor[1]
        # print col_left, " ==== ", col_right
        # print '-----------'
        print np.zeros((block.realValues.shape[1]))
        print self.background[row, col_left: col_right]
        print '+++++++++++++'
        # print self.background[row, col_left: col_right] == np.zeros((block.realValues[1]))
        if not (self.background[row, col_left: col_right] == np.zeros((block.realValues.shape[1]))).all():
            # reach bottom
            # update background and send new block
            self.background = np.copy(self.spaces)

        else:
            # fall and check
            print 'fall'
            block.y -= 1
            self.updateSpace(block)
            self.check_and_eliminate(range(row, size[0], -1))
        
    def updateSpace(self, block):
        # add current block's realValues to space matrix
        size = block.realValues.shape
        self.spaces = np.copy(self.background)
        for i in range(size[0]):
            for j in range(size[1]):
                row = i
                column = (self.width - size[1]) / 2 + j + block.x
                self.spaces[row, column] = self.background[row, column] + block.realValues[i, j]

    def check_and_eliminate(self, rows):
        for row in rows:
            if self._check_full(row):
                # eliminate
                up = self.background[0: row, :]
                down = self.background[row+1: , :]
                self.background = np.concatenate((up, down), axis=0)
            else:
                break
        
        rows = self.height - self.background.shape[0]
        self.background = np.array((np.zeros((rows, self.width), dtype=int), self.background))
    
    def _check_full(self, row):
        # return 0 if row-th is not full
        for column in range(self.width):
            if self.spaces(row, column) == 0:
                return 0


class Block(object):
    def __init__(self, blockType, x, y, direction):
        # x, y is center coordinations
        self.blockType = blockType
        self.x = x
        self.y = y
        self.direction = direction
        self.values = np.zeros((5, 5))
        self.centor = [2, 2]
    
    def _set_init_position(self):
        # set last row of block to be the first row of env,
        # so centor is self.centor[0]
        self.getRealValue()
        self.y = self.centor[0]
    
    def move(self, action):
        # 1: left, 2: right
        if action == 1 :
            self.x -= 1
        elif action == 2:
            self.x += 1

    def fall(self):
        if self.y != 0:
            self.y -= 1

    def transform(self):
        self.direction += 1
        self.getRealValue()
    
    def getRealValue(self):
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
                continue
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
                continue
            else:
                tmp = row_realValues[:, j].reshape((row_realValues.shape[0], 1))
                if self.realValues is not None:
                    self.realValues = np.concatenate((self.realValues,tmp), axis=1)
                else:
                    self.realValues = tmp
    
    def changeDirection(self):
        self.direction += 1
        self.values = np.transpose(self.values)
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
        self.__init_values()
        self._set_init_position()

    def __init_values(self):
        for i in range(self.direction):
            self.values = np.transpose(self.values)
    

class GUI(object):
    def __init__(self, height, width):
        pygame.init()
        self.color_map = ((0, 0, 0), (0, 10, 80), (0, 255, 255))
        self.pixel_size = 20
        self.keyBoard = 0
        self.width = width
        self.height = height

        size = self.width * self.pixel_size, self.height * self.pixel_size
        self.screen = pygame.display.set_mode(size)
    
    def draw(self, matrix):
        #print matrix
        self.keyBoard = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.keyBoard = 1
                elif event.key == pygame.K_RIGHT:
                    self.keyBoard = 2
                elif event.key == pygame.K_UP:
                    self.keyBoard = 3

        self.screen.fill((0, 0, 0))

        # draw matrix
        # print matrix
        for row in range(self.height):
            for column in range(self.width):
                value = matrix[row, column]
                if value != 0:
                    baseRect = (column * self.pixel_size, row * self.pixel_size, self.pixel_size, self.pixel_size)
                    color = self.color_map[value]
                    pygame.draw.rect(self.screen, color, baseRect)
        pygame.display.update()
