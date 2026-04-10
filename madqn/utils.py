"""
Utility functions for MADQN framework
"""

import numpy as np
from collections import deque
import json


class ReplayBuffer:
    """Experience replay buffer for DQN training"""
    
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state, action, reward, next_state, done):
        """Add experience to buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """Sample random batch from buffer"""
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states, actions, rewards, next_states, dones = zip(*[self.buffer[i] for i in indices])
        return np.array(states), np.array(actions), np.array(rewards), \
               np.array(next_states), np.array(dones)
    
    def size(self):
        """Return buffer size"""
        return len(self.buffer)


def normalize_state(state, min_val=0, max_val=100):
    """Normalize network state to [0, 1]"""
    return (state - min_val) / (max_val - min_val + 1e-8)


def calculate_link_utilization(queue_length, link_capacity):
    """Calculate link utilization percentage"""
    return min(100, (queue_length / link_capacity) * 100)


def save_metrics(metrics, filepath):
    """Save metrics to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=4)


def load_metrics(filepath):
    """Load metrics from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)
