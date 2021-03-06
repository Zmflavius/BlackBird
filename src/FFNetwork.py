import numpy as np
import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class Network:
    def __init__(self, dims=(3,3), **kwargs):
        self.dims = dims
        self.parameters = kwargs['network']
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.4)
        self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
        

        self.default_alpha = self.parameters['policy']['dirichlet']['alpha']
        self.default_epsilon = self.parameters['policy']['dirichlet']['epsilon']

        self.CreateNetwork()

        self.init = tf.global_variables_initializer()
        self.sess.run(self.init)

    def CreateNetwork(self):
        with tf.variable_scope('inputs', reuse=tf.AUTO_REUSE) as scope:
            self.input = tf.placeholder(shape=[None, self.dims[0], self.dims[1], 3], name='board_input', dtype=tf.float32)
            self.correct_move_vec = tf.placeholder(shape=[None, self.dims[0] * self.dims[1]], name='correct_move_from_mcts', dtype=tf.float32)
            self.mcts_evaluation = tf.placeholder(shape=[None], name='mcts_evaluation', dtype=tf.float32)

        with tf.variable_scope('hidden', reuse=tf.AUTO_REUSE) as scope:
            self.hidden = [self.input]
            self.hidden.append(tf.reshape(self.hidden[-1], [-1, self.dims[0] * self.dims[1] * 3]))
            
            for block in range(self.parameters['blocks']):
                with tf.variable_scope('block_{}'.format(block), reuse=tf.AUTO_REUSE) as scope:
                    self.hidden.append(tf.layers.dense(self.hidden[-1], units=9, activation=tf.nn.relu))

        with tf.variable_scope('evaluation', reuse=tf.AUTO_REUSE) as scope:
            self.reduce_net = tf.reduce_sum(self.hidden[-1])
            self.evaluation = tf.tanh(self.reduce_net, name='evaluation')

        with tf.variable_scope('policy', reuse=tf.AUTO_REUSE) as scope:
            self.epsilon = tf.placeholder(shape=[1], dtype=tf.float32)
            self.alpha = tf.placeholder(shape=[1], dtype=tf.float32)

            self.policy_dense = tf.layers.dense(self.hidden[-1], units=9, activation=tf.nn.relu)
            self.policy = tf.nn.softmax(self.policy_dense)

        with tf.variable_scope('loss', reuse=tf.AUTO_REUSE) as scope:
            self.loss_evaluation = tf.square(self.evaluation - self.mcts_evaluation)
            self.loss_policy = tf.reduce_sum(tf.tensordot( tf.log(self.policy), tf.transpose(self.correct_move_vec), axes=1), axis=1)
            self.loss_param = tf.tile(tf.expand_dims(tf.reduce_sum([tf.nn.l2_loss(v) for v in tf.trainable_variables()
                              #if 'bias' not in v.name
                              ]) * self.parameters['loss']['L2_norm'], 0), [tf.shape(self.loss_policy)[0]])
            self.loss = self.loss_evaluation - self.loss_policy + self.loss_param
            tf.summary.scalar('total_loss', self.loss[0])

        with tf.variable_scope('training', reuse=tf.AUTO_REUSE) as scope:
            self.learning_rate = tf.placeholder(shape=[1], dtype=tf.float32, name='learning_rate')

            if self.parameters['training']['optimizer'] == 'adam':
                self.optimizer = tf.train.AdamOptimizer(self.learning_rate[0])
            elif self.parameters['training']['optimizer'] == 'momentum':
                self.optimizer = tf.train.MomentumOptimizer(self.learning_rate[0], momentum=self.parameters['training']['momentum'])
            else:  # Default to SGD
                self.optimizer = tf.train.GradientDescentOptimizer(self.learning_rate[0])

            self.training_op = self.optimizer.minimize(self.loss)

    def getEvaluation(self, state):
        """ Given a game state, return the network's evaluation.
        """
        evaluation = self.sess.run(self.evaluation, feed_dict={self.input:state})
        return evaluation

    def getPolicy(self, state):
        """ Given a game state, return the network's policy.
            Random Dirichlet noise is applied to the policy output to ensure exploration.
        """
        policy = self.sess.run(self.policy, 
            feed_dict={self.input:state, self.epsilon:[self.default_epsilon], self.alpha:[self.default_alpha]})
        return policy[0]

    def train(self, state, evaluation, policy, learning_rate=0.01):
        """ Train the network
        """
        feed_dict={
            self.input:state,
            self.mcts_evaluation:evaluation,
            self.correct_move_vec:policy,
            self.learning_rate:[learning_rate],
            self.epsilon:[self.default_epsilon],
            self.alpha:[self.default_alpha]
        }
        
        self.sess.run(self.training_op, feed_dict=feed_dict)