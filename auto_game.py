from network import DQN
from environment import *
import pygame 
import sys
import time


class DQNGame(object):
    def __init__(self, epochs = 1000):
        self.epochs = epochs
        self.network = DQN()

    def preprocess(self, matrix):
        # matrix is screen value
        size = matrix.shape

        # state(binary)
        input_matrix = (matrix != np.zeros(size)).astype(int)
        input_matrix = input_matrix.reshape((20, 16, 1))
        return input_matrix

    def start(self):
        print '---------------------------------------'
        for epoch in range(self.epochs):
            step = 0
            self.vis = GUI(20, 16)
            self.env = Environment(20, 16, self.vis.draw)
            # get initial state
            spaces, score, gameover = self.env.getGameState()
            observation = self.preprocess(spaces)
            last_score = score
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: 
                        print 'exit'
                        sys.exit()

                action = self.network.chooseAction(observation)
                print action
                #print 'action: ', action
                self.env.takeAction(action)
                spaces_, score, gameover = self.env.getGameState()
                observation_ = self.preprocess(spaces_)
                reward = score - last_score
                print 'reward: ', reward

                self.network.store(observation, action, reward, observation_)

                if (step > 200) and (step % 5 == 0):
                    self.network.learn()
                
                observation = observation_
                last_score = score
                if gameover:
                    break
                step += 1
                time.sleep(0.004)
            #env.destroy()

if __name__ == '__main__':
    game = DQNGame()
    game.start()