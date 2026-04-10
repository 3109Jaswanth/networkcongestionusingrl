"""
Multi-Agent DQN implementation for SDN load balancing
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from .utils import ReplayBuffer


class DQNAgent:
    """Deep Q-Network Agent for a single switch/node"""
    
    def __init__(self, state_size=4, action_size=3, agent_id=0, learning_rate=0.001):
        """
        Initialize DQN Agent
        
        Args:
            state_size: Size of state space
            action_size: Number of possible actions (number of outgoing paths)
            agent_id: Unique identifier for this agent
            learning_rate: Learning rate for neural network
        """
        self.state_size = state_size
        self.action_size = action_size
        self.agent_id = agent_id
        self.learning_rate = learning_rate
        
        # Hyperparameters
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        
        # Replay buffer
        self.memory = ReplayBuffer(capacity=10000)
        
        # Neural networks
        self.q_network = self._build_model()
        self.target_network = self._build_model()
        self.update_target_network()
        
    def _build_model(self):
        """Build Q-value neural network"""
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(self.state_size,)),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
                     loss='mse')
        return model
    
    def update_target_network(self):
        """Update target network weights"""
        self.target_network.set_weights(self.q_network.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.add(state, action, reward, next_state, done)
    
    def act(self, state):
        """Select action using epsilon-greedy policy"""
        if np.random.random() < self.epsilon:
            return np.random.randint(0, self.action_size)
        else:
            q_values = self.q_network.predict(np.array([state]), verbose=0)
            return np.argmax(q_values[0])
    
    def replay(self, batch_size):
        """Train on batch from replay buffer"""
        if self.memory.size() < batch_size:
            return 0
        
        states, actions, rewards, next_states, dones = self.memory.sample(batch_size)
        
        # Predict Q-values for starting state
        target_q_values = self.q_network.predict(states, verbose=0)
        
        # Predict Q-values for next state using target network
        next_q_values = self.target_network.predict(next_states, verbose=0)
        
        for i in range(batch_size):
            if dones[i]:
                target_q_values[i, actions[i]] = rewards[i]
            else:
                target_q_values[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
        
        # Train the Q-network
        loss = self.q_network.train_on_batch(states, target_q_values)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss
    
    def save(self, filepath):
        """Save agent model"""
        self.q_network.save(filepath)
    
    def load(self, filepath):
        """Load agent model"""
        self.q_network = keras.models.load_model(filepath)
        self.update_target_network()


class MultiAgentDQN:
    """Multi-Agent DQN system for SDN network"""
    
    def __init__(self, num_agents, state_size=4, action_size=3):
        """
        Initialize Multi-Agent DQN system
        
        Args:
            num_agents: Number of agents in the network
            state_size: Size of state space for each agent
            action_size: Number of actions for each agent
        """
        self.num_agents = num_agents
        self.agents = [DQNAgent(state_size, action_size, i) for i in range(num_agents)]
    
    def act(self, agent_id, state):
        """Get action from specific agent"""
        return self.agents[agent_id].act(state)
    
    def remember(self, agent_id, state, action, reward, next_state, done):
        """Store experience for specific agent"""
        self.agents[agent_id].remember(state, action, reward, next_state, done)
    
    def replay(self, batch_size):
        """Train all agents"""
        total_loss = 0
        for agent in self.agents:
            loss = agent.replay(batch_size)
            total_loss += loss
        return total_loss / len(self.agents)
    
    def update_target_networks(self):
        """Update target networks for all agents"""
        for agent in self.agents:
            agent.update_target_network()
    
    def save_all_agents(self, directory):
        """Save all agent models"""
        for i, agent in enumerate(self.agents):
            agent.save(f"{directory}/agent_{i}.h5")
    
    def load_all_agents(self, directory):
        """Load all agent models"""
        for i, agent in enumerate(self.agents):
            agent.load(f"{directory}/agent_{i}.h5")
