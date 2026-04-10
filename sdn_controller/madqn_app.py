"""
SDN Controller Application - MADQN Load Balancer
"""

import numpy as np
from collections import defaultdict


class MADQNControllerApp:
    """MADQN-based Load Balancing SDN Application"""
    
    def __init__(self, madqn_system, num_switches=4):
        """
        Initialize MADQN controller app
        
        Args:
            madqn_system: Multi-agent DQN system
            num_switches: Number of switches
        """
        self.madqn = madqn_system
        self.num_switches = num_switches
        self.network_states = None
    
    def get_routing_decision(self, switch_id, network_metrics):
        """
        Get routing decision from MADQN agent
        
        Args:
            switch_id: ID of the switch
            network_metrics: Current network metrics [queue_avg, queue_max, loss_rate, latency]
        
        Returns:
            out_port: Port to send traffic out
        """
        if switch_id >= self.num_switches:
            return 0
        
        # Get action from MADQN agent
        action = self.madqn.act(switch_id, np.array(network_metrics))
        
        return action
    
    def update_agents(self, switch_id, state, action, reward, next_state, done):
        """Update MADQN agents with experience"""
        self.madqn.remember(switch_id, state, action, reward, next_state, done)
    
    def train_batch(self, batch_size):
        """Train MADQN agents on a batch"""
        return self.madqn.replay(batch_size)


class NetworkStatsCollector:
    """Collect and maintain network statistics"""
    
    def __init__(self, num_switches=4, num_paths=3):
        self.num_switches = num_switches
        self.num_paths = num_paths
        self.queue_lengths = defaultdict(float)
        self.packet_counts = defaultdict(int)
        self.latencies = defaultdict(list)
    
    def update_queue_length(self, switch_id, path_id, length):
        """Update queue length for a path"""
        self.queue_lengths[(switch_id, path_id)] = length
    
    def record_packet(self, switch_id, path_id):
        """Record a packet transmission"""
        self.packet_counts[(switch_id, path_id)] += 1
    
    def record_latency(self, switch_id, path_id, latency):
        """Record latency for a transmission"""
        self.latencies[(switch_id, path_id)].append(latency)
        if len(self.latencies[(switch_id, path_id)]) > 1000:
            self.latencies[(switch_id, path_id)] = \
                self.latencies[(switch_id, path_id)][-1000:]
    
    def get_switch_metrics(self, switch_id):
        """Get aggregated metrics for a switch"""
        queues = []
        for p in range(self.num_paths):
            queues.append(self.queue_lengths.get((switch_id, p), 0))
        
        avg_queue = np.mean(queues) if queues else 0
        max_queue = np.max(queues) if queues else 0
        
        total_packets = sum(self.packet_counts[(switch_id, p)] 
                          for p in range(self.num_paths))
        loss_rate = 0  # Can be calculated from dropped packets
        
        all_latencies = []
        for p in range(self.num_paths):
            all_latencies.extend(self.latencies.get((switch_id, p), []))
        
        avg_latency = np.mean(all_latencies) if all_latencies else 0
        
        return np.array([avg_queue, max_queue, loss_rate, avg_latency])
    
    def reset(self):
        """Reset statistics"""
        self.queue_lengths.clear()
        self.packet_counts.clear()
        self.latencies.clear()
