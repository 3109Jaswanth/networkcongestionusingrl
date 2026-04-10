"""
SDN controller applications for load balancing
"""

import numpy as np
from collections import defaultdict


class RoundRobinLB:
    """Round Robin Load Balancer"""
    
    def __init__(self, num_switches=4, num_paths=3):
        self.num_switches = num_switches
        self.num_paths = num_paths
        self.round_robin_index = defaultdict(int)
    
    def get_action(self, switch_id, state):
        """Get routing action using round-robin"""
        action = self.round_robin_index[switch_id] % self.num_paths
        self.round_robin_index[switch_id] += 1
        return action
    
    def reset(self):
        """Reset round-robin indices"""
        self.round_robin_index.clear()


class WeightedRoundRobinLB:
    """Weighted Round Robin Load Balancer"""
    
    def __init__(self, num_switches=4, num_paths=3, weights=None):
        self.num_switches = num_switches
        self.num_paths = num_paths
        
        # Default weights: prefer paths with lower latency
        if weights is None:
            self.weights = [1.0] * num_paths
        else:
            self.weights = weights
        
        self.wrr_index = defaultdict(int)
    
    def get_action(self, switch_id, state):
        """Get routing action using weighted round-robin"""
        # State contains: [avg_queue, max_queue, loss_rate, avg_latency]
        # Use latency to adjust weights
        latency = state[3] if len(state) > 3 else 0
        
        # Adjust weights inversely to latency
        adjusted_weights = []
        for i in range(self.num_paths):
            base_weight = self.weights[i]
            adjusted_weights.append(base_weight / (1 + latency * 0.1))
        
        # Normalize weights
        total_weight = sum(adjusted_weights)
        normalized_weights = [w / total_weight for w in adjusted_weights]
        
        # Select path based on accumulated weights
        index = self.wrr_index[switch_id] % sum(int(w * 10) for w in normalized_weights)
        self.wrr_index[switch_id] += 1
        
        cumulative = 0
        for path_id, weight in enumerate(normalized_weights):
            cumulative += int(weight * 10)
            if index < cumulative:
                return path_id
        
        return self.num_paths - 1
    
    def reset(self):
        """Reset WRR indices"""
        self.wrr_index.clear()


class HACBPNNLoadBalancer:
    """Hierarchical Agglomerative Clustering + Back Propagation Neural Networks"""
    
    def __init__(self, num_switches=4, num_paths=3):
        self.num_switches = num_switches
        self.num_paths = num_paths
        
        # Simple neural network weights (simulated)
        self.weights_layer1 = np.random.randn(4, 8) * 0.01
        self.weights_layer2 = np.random.randn(8, num_paths) * 0.01
        self.bias1 = np.zeros(8)
        self.bias2 = np.zeros(num_paths)
    
    def _relu(self, x):
        """ReLU activation"""
        return np.maximum(0, x)
    
    def _softmax(self, x):
        """Softmax activation"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=-1, keepdims=True)
    
    def get_action(self, switch_id, state):
        """Get routing decision using neural network"""
        # Forward pass
        hidden = self._relu(np.dot(state, self.weights_layer1) + self.bias1)
        output = self._softmax(np.dot(hidden, self.weights_layer2) + self.bias2)
        
        # Select action with highest output
        return np.argmax(output)
    
    def train_step(self, state, target_action, learning_rate=0.001):
        """Simple training step (for demonstration)"""
        # This is simplified - real BPNN would do full backpropagation
        hidden = self._relu(np.dot(state, self.weights_layer1) + self.bias1)
        output = self._softmax(np.dot(hidden, self.weights_layer2) + self.bias2)
        
        # Simple weight update
        self.weights_layer2 += learning_rate * np.random.randn(*self.weights_layer2.shape)


class LoadBalancerController:
    """Main SDN Controller for load balancing"""
    
    def __init__(self, algorithm='madqn', num_switches=4, num_paths=3):
        """
        Initialize load balancer controller
        
        Args:
            algorithm: 'madqn', 'rr', 'wrr', or 'hac_bpnn'
            num_switches: Number of switches
            num_paths: Number of paths per switch
        """
        self.algorithm = algorithm
        self.num_switches = num_switches
        self.num_paths = num_paths
        
        if algorithm == 'rr':
            self.lb = RoundRobinLB(num_switches, num_paths)
        elif algorithm == 'wrr':
            self.lb = WeightedRoundRobinLB(num_switches, num_paths)
        elif algorithm == 'hac_bpnn':
            self.lb = HACBPNNLoadBalancer(num_switches, num_paths)
        else:
            self.lb = None  # Will use MADQN (external)
    
    def get_routing_decision(self, switch_id, network_state):
        """Get routing decision for a flow"""
        if self.lb is None:
            raise ValueError("Algorithm not initialized")
        
        return self.lb.get_action(switch_id, network_state)
    
    def reset(self):
        """Reset controller state"""
        if self.lb is not None:
            self.lb.reset()


def create_sdn_app(algorithm, num_switches=4, num_paths=3):
    """Factory function to create SDN app"""
    return LoadBalancerController(algorithm, num_switches, num_paths)
