from network import DQN
from environment import *
import pygame 
import sys


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
            self.env = Environment(20, 16)
            # get initial state
            spaces, score, gameover = self.env.updateEnvironment(4)
            observation = self.preprocess(spaces)
            last_score = score
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: 
                        print 'exit'
                        sys.exit()
                self.vis.draw(self.env.spaces)

                action = self.network.chooseAction(observation)
                #print 'action: ', action

                spaces_, score, gameover = self.env.updateEnvironment(action)
                observation_ = self.preprocess(spaces_)
                reward = score - last_score
                #print 'reward: ', reward

                self.network.store(observation, action, reward, observation_)

                if (step > 200) and (step % 5 == 0):
                    self.network.learn()
                
                observation = observation_

                if gameover:
                    break
                step += 1
            
            #env.destroy()

if __name__ == '__main__':
    game = DQNGame()
    game.start()