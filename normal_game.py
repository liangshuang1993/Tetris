from environment import *
import threading
import time
import pygame
import sys


class BlockGame(object):
    def __init__(self):
        self.vis = GUI(20, 16)
        self.env = Environment(20, 16)

    def control_and_show(self):
        while True and self.env.gameover is False:
            keyBoard = 4
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    print 'exit'
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        keyBoard = -1
                    elif event.key == pygame.K_RIGHT:
                        keyBoard = 1
                    elif event.key == pygame.K_UP:
                        keyBoard = 2
                    elif event.key == pygame.K_DOWN:
                        keyBoard = 3

            self.env.updateEnvironment(keyBoard)
            self.vis.draw(self.env.spaces)

    def start(self):
        self.control_and_show()


game = BlockGame()
game.start()
