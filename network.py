import tensorflow as tf
import numpy as np
from collections import deque
from environment import ActionMap

class DQN(object):
    def __init__(self, height, width):
        #self.createNetwork()
        self.lr = 0.01
        self.gamma = 0.9
        self.epsilion = 0.9
        self.memory_size = 100
        self.memory_counter = 0
        self.replace_target_iter = 300
        self.batch_size = 32
        self.learn_step_counter = 0
        self.save_period = 1000
        self.action_num = 4 # left, right, rotate, noAction
        self.height = height
        self.width = width

        # memory restore [s, a, r, s']
        self.memory = [np.zeros((self.height, self.width, 1)), 1, 1, np.zeros((self.height, self.width, 1))] * self.memory_size
        #self.memory = np.zeros((self.memory_size, 20 * 16 * 2 + 2))

        self.cnnNetwork()

        t_params = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='target_net')
        e_params = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='eval_net')
        with tf.variable_scope('soft_replacement'):
            self.target_replace_op = [tf.assign(t, e) for t, e in zip(t_params, e_params)]

        self.sess = tf.Session()

        tf.summary.FileWriter('logs/', self.sess.graph)
        self.sess.run(tf.global_variables_initializer())
        self.saver = tf.train.Saver()
    
    def cnnNetwork(self):

        self.s = tf.placeholder(tf.float32, [None, self.height, self.width, 1], name='s')
        self.s_ = tf.placeholder(tf.float32, [None, self.height, self.width, 1], name='s')
        self.r = tf.placeholder(tf.float32, [None, ], name='s')
        self.a = tf.placeholder(tf.int32, [None, ], name='a')

        w_initializer = tf.random_normal_initializer(0, 0.3)
        b_initializer = tf.constant_initializer(0.1)

        # eval net
        with tf.variable_scope('eval_net'):
            collection1 = ['eval_net_param', tf.GraphKeys.GLOBAL_VARIABLES]
            # input is 20 x 16
            w_conv1 = tf.get_variable('w1', [4, 4, 1, 32], dtype=tf.float32, initializer=w_initializer, collections=collection1)
            b_conv1 = tf.get_variable('b1', [32], dtype=tf.float32, initializer=b_initializer, collections=collection1)
            w_conv2 = tf.get_variable('w2', [3, 3, 32, 64], dtype=tf.float32, initializer=w_initializer, collections=collection1)
            b_conv2 = tf.get_variable('b2', [64], dtype=tf.float32, initializer=b_initializer, collections=collection1)
            w_fc3 = tf.get_variable('w3', [896, 64], dtype=tf.float32, initializer=w_initializer, collections=collection1)
            b_fc3 = tf.get_variable('b3', [64], dtype=tf.float32, initializer=b_initializer, collections=collection1)
            w_out = tf.get_variable('w_out', [64, self.action_num], dtype=tf.float32, initializer=w_initializer, collections=collection1)
            b_out = tf.get_variable('b_out', [self.action_num], dtype=tf.float32, initializer=b_initializer, collections=collection1)

            # 9 x 4
            conv1 = tf.nn.relu(tf.nn.conv2d(self.s, 
                                        w_conv1, 
                                        strides=[1, 2, 2, 1],
                                        padding='VALID') + b_conv1)
            # 7 x 2
            conv2 = tf.nn.relu(tf.nn.conv2d(conv1, 
                                        w_conv2, 
                                        strides=[1, 1, 1, 1],
                                        padding='VALID') + b_conv2)
            
            conv2_flat = tf.reshape(conv2, [-1, 896])
            fc3 = tf.nn.relu(tf.matmul(conv2_flat, w_fc3) + b_fc3)

            self.q_eval = tf.matmul(fc3, w_out) + b_out

        # target net
        with tf.variable_scope('target_net'):
            collection2 = ['target_net_param', tf.GraphKeys.GLOBAL_VARIABLES]
            # input is 20 x 16
            w_conv1 = tf.get_variable('w1', [4, 4, 1, 32], dtype=tf.float32, initializer=w_initializer, collections=collection2)
            b_conv1 = tf.get_variable('b1', [32], dtype=tf.float32, initializer=b_initializer, collections=collection2)
            w_conv2 = tf.get_variable('w2', [3, 3, 32, 64], dtype=tf.float32, initializer=w_initializer, collections=collection2)
            b_conv2 = tf.get_variable('b2', [64], dtype=tf.float32, initializer=b_initializer, collections=collection2)
            w_fc3 = tf.get_variable('w3', [896, 64], dtype=tf.float32, initializer=w_initializer, collections=collection2)
            b_fc3 = tf.get_variable('b3', [64], dtype=tf.float32, initializer=b_initializer, collections=collection2)
            w_out = tf.get_variable('w_out', [64, self.action_num], dtype=tf.float32, initializer=w_initializer, collections=collection2)
            b_out = tf.get_variable('b_out', [self.action_num], dtype=tf.float32, initializer=b_initializer, collections=collection2)

            # 9 x 7
            conv1 = tf.nn.relu(tf.nn.conv2d(self.s_, 
                                        w_conv1, 
                                        strides=[1, 2, 2, 1],
                                        padding='VALID') + b_conv1)
            # 7 x 5
            conv2 = tf.nn.relu(tf.nn.conv2d(conv1, 
                                        w_conv2, 
                                        strides=[1, 1, 1, 1],
                                        padding='VALID') + b_conv2)
            
            conv2_flat = tf.reshape(conv2, [-1, 896])
            fc3 = tf.nn.relu(tf.matmul(conv2_flat, w_fc3) + b_fc3)

            self.q_next = tf.matmul(fc3, w_out) + b_out
        
        with tf.variable_scope('q_target'):
            q_target = self.r + self.gamma * tf.reduce_max(self.q_next, axis=1)
            self.q_target = tf.stop_gradient(q_target)
        with tf.variable_scope('q_eval'):
            a_indices = tf.stack([tf.range(tf.shape(self.a)[0], dtype=tf.int32), self.a], axis=1)
            self.q_eval_wrt_a = tf.gather_nd(params=self.q_eval, indices=a_indices)

        # get q for action
        self.cost = tf.reduce_mean(tf.squared_difference(self.q_target, self.q_eval_wrt_a, name='TD_error'))
        self.optimizer = tf.train.AdamOptimizer(1e-3).minimize(self.cost)

    def chooseAction(self, observation):
        observation = observation.reshape(1, self.height, self.width, 1)
        action = None
        if np.random.uniform() < self.epsilion:
            q_values = self.sess.run(self.q_eval, feed_dict={self.s: observation})
            if np.argmax(q_values) == 3:
                # no speedup, change to noAction
                action = ActionMap.noAction
            else:
                action = ActionMap(np.argmax(q_values))
        else:
            tmp = np.random.randint(0, self.action_num)
            if tmp == 3:
                action = ActionMap.noAction
            else:
                action = ActionMap(tmp)
        return action

    def store(self, state, action, reward, state_):
        #transition = np.hstack((state, [action, reward], state_))
        index = self.memory_counter % self.memory_size
        self.memory[index] = (state, action, reward, state_)
        self.memory_counter += 1

    def learn(self):
        # replace target parameters
        #print self.learn_step_counter
        if self.learn_step_counter % self.replace_target_iter == 0:
            print 'update'
            self.sess.run(self.target_replace_op)

        if self.memory_counter > self.memory_size:
            print self.memory_counter
            sample_index = np.random.choice(self.memory_size, size=self.batch_size)
        else:
            sample_index = np.random.choice(self.memory_counter, size=self.batch_size)
        batch_s = []
        batch_a = []
        batch_r = []
        batch_s_ = []
        for i in sample_index:
            batch_s.append(self.memory[i][0])
            batch_a.append(self.memory[i][1].value)
            batch_r.append(self.memory[i][2])
            batch_s_.append(self.memory[i][3])
        _, cost = self.sess.run([self.optimizer, self.cost],
                                     feed_dict={self.s: batch_s,
                                                self.a: batch_a,
                                                self.r: batch_r,
                                                self.s_: batch_s_
                                                })
        
        self.learn_step_counter += 1
        if self.learn_step_counter % self.save_period == 1:
            self.saver.save(self.sess, 'models')
    



