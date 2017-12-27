from environment import *
import threading
import time


class BlockGame(object):
    def __init__(self):
        self.a = 0 # current action, left 1 or right 2
        self.vis = GUI(10, 10)
        self.env = Environment(10, 10)
    
        self.block = self.env.generate_new_block()
        self.block.getRealValue()
        self.env.updateSpace(self.block)
    
    def show(self):
        #matrix = np.array(((1,0,0,0),(2,0,0,0), (0,1,0,0), (0,0,2,0)))
        while True:
            self.vis.draw(self.env.spaces)
            time.sleep(1)

    def control(self):
        while True:
            self.env.updateEnv(self.block)
            if self.vis.keyBoard:
                if self.vis.keyBoard == 1 or self.vis.keyBoard == 2:
                    self.block.move(self.vis.keyBoard)
                    #self.env.updateSpace(self.block)
                elif self.vis.keyBoard == 3:
                    self.block.changeDirection()
                    #self.env.updateSpace(self.block)
            time.sleep(1)
        

    def start(self):
        threads = []
        t1 = threading.Thread(target=self.show, args=(), name='show')
        t2 = threading.Thread(target=self.control, args=(), name='control')
        threads.append(t1)
        threads.append(t2)
        for t in threads:
            t.start()


game = BlockGame()
game.start()
