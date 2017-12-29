from environment import *
import threading
import time
import pygame


class BlockGame(object):
    def __init__(self):
        self.a = 0 # current action, left 1 or right 2
        self.vis = GUI(10, 10)
        self.env = Environment(10, 10)
        self.keyBoard = 0
 

        self.lock = threading.Lock()
        self.quit = 0

    def falldown(self):
        while True:
            if self.quit == 1:
                sys.exit()
            if self.env.moving_block:
                self.env.falldown(self.block)
            time.sleep(0.5)
            #self.lock.release()

    def control_and_show(self):
        while True and self.env.gameover == False:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.quit = 1
                    print 'exit'
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.keyBoard = -1
                    elif event.key == pygame.K_RIGHT:
                        self.keyBoard = 1
                    elif event.key == pygame.K_UP:
                        self.keyBoard = 2
                    elif event.key == pygame.K_DOWN:
                        self.keyBoard = 3

            if self.env.moving_block == False:   
                self.block = self.env.generate_new_block()
                self.block.getRealValue()
                self.env.moving_block = True
                self.env.updateSpace(self.block, self.keyBoard)
            #self.lock.acquire()
            self.env.updateSpace(self.block, self.keyBoard)
            self.vis.draw(self.env.spaces)
            self.keyBoard = 4

    def start(self):
        threads = []
        t2 = threading.Thread(target=self.control_and_show, args=(), name='control_and_show')
        t1 = threading.Thread(target=self.falldown, args=(), name='falldown')
        threads.append(t1)
        threads.append(t2)
        for t in threads:
            t.start()


game = BlockGame()
game.start()
