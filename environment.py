import time, sys
import numpy as np
import pygame

class Environment(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.type_num = 4
        self.spaces = np.zeros((height, width))
    
    def generate_new_block(self):
        block_type = np.random.randint(self.type_num)
        direction = np.random.randint(4)
        x = self.width / 2
        y = 0
        block = LongBlock(x, y, direction)
        return block
    
    def updateSpace(self, block):
        # update spaces
        pass

    def eliminate(self):
        for i in range(self.height):
            row = self.height - i - 1
            if self._check_full(row):
                # eliminate
                up = self.spaces[0: row, :]
                down = self.spaces[row+1: , :]
                self.spaces = np.concatenate((up, down), axis=0)
            else:
                break
        
        rows = self.height - self.spaces.shape[0]
        self.spaces = np.array((np.zeros(rows, self.width), self.spaces))
    
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
    
    def move(self, action):
        # 0: left, 1: right
        if action == 0 :
            self.x -= 1
        elif action == 1:
            self.x += 1

        if self.y != 0:
            self.y -= 1

    def transform(self):
        self.direction += 1
    
    def getRealValue(self):
        # delete empty row
        realValues = None
        for i in range(5):
            if (self.values[i] == np.zeros((1, 5))).all():
                continue
            else:
                if realValues:
                    realValues = np.concatenate(realValues,
                                                self.values[i])
                else:
                    realValues = self.values[i]
        # delete empty columns
        self.realValues = None
        for j in range(5):
            if (self.values[:, j] == np.zeros((5, 1))).all():
                continue
            else:
                if self.realValues:
                    self.realValues = np.concatenate(self.realValues,
                                                     realValues[:, j])
                else:
                    realValues = self.values[:, j]

class LongBlock(Block):
    def __init__(self, x, y, direction):
        super(LongBlock, self).__init__(blockType=1, x=x, y=y, direction=direction)
        # when direction is 0
        self.values = np.array(((0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0),
                                (0, 0, 1, 0, 0)))
        self.__init_values()

    def __init_values(self):
        for i in range(self.direction):
            self.values = np.transpose(self.values)
    
    def changeDirection(self):
        self.direction += 1
        self.values = np.transpose(self.values)
        if self.direction == 4:
            self.direction = 0


class Visualize(object):
    def __init__(self):
        pygame.init()
        self.color_map = ((255, 255, 0), (255, 0, 0), (0, 255, 255))
    
    def showBackground(self, matrix):
        height, width = matrix.shape
        size = height * 100, width * 100 
        screen = pygame.display.set_mode(size)
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        action = 0
                    elif event.key == pygame.K_RIGHT:
                        action = 1

            screen.fill((0, 0, 0))

            # draw matrix
            for row in range(height):
                for column in range(width):
                    value = matrix[row, column]
                    if value != 0:
                        baseRect = (row * 100, column * 100, 100, 100)
                        print baseRect
                        color = self.color_map[value]
                        print color
                        pygame.draw.rect(screen, color, baseRect)
            pygame.display.update()
            time.sleep(1)
    

vis = Visualize()
matrix = np.array(((1,0,0,0),(2,0,0,0), (0,1,0,0), (0,0,2,0)))
vis.showBackground(matrix)