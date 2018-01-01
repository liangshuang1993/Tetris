from environment import *
import threading
import time
import pygame
import sys


class BlockGame(object):
    def __init__(self):
        self.vis = GUI(20, 16)
        self.env = Environment(20, 16, self.vis.draw) 

    def control_and_show(self):
        while True and self.env.gameover is False:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    print 'exit'
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    keyBoard = None
                    if event.key == pygame.K_LEFT:
                        keyBoard = ActionMap.left
                    elif event.key == pygame.K_RIGHT:
                        keyBoard = ActionMap.right
                    elif event.key == pygame.K_UP:
                        keyBoard = ActionMap.rotate
                    elif event.key == pygame.K_DOWN:
                        keyBoard = ActionMap.speedup
                    self.env.takeAction(keyBoard)
            time.sleep(0.004)
            #self.vis.draw(self.env.spaces)


game = BlockGame()
game.control_and_show()