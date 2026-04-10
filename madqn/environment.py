"""
Network simulation environment for MADQN training
"""

import numpy as np
from collections import defaultdict


class NetworkEnvironment:
    """Simulated network environment for multi-agent reinforcement learning"""
    
    def __init__(self, num_switches=4, num_paths_per_switch=3, 
                 link_capacity=1000, queue_threshold=800):
        """
        Initialize network environment
        
        Args:
            num_switches: Number of switches in the network
            num_paths_per_switch: Number of outgoing paths per switch
            link_capacity: Maximum capacity of each link (packets/time step)
            queue_threshold: Threshold for link congestion
        """
        self.num_switches = num_switches
        self.num_paths_per_switch = num_paths_per_switch
        self.link_capacity = link_capacity
        self.queue_threshold = queue_threshold
        
        # Network state
        self.queue_lengths = defaultdict(float)  # {(switch, path): queue_length}
        self.packet_loss = defaultdict(int)  # {(switch, path): lost_packets}
        self.latency = defaultdict(list)  # {(switch, path): latencies}
        
        # Statistics
        self.total_packets = 0
        self.delivered_packets = 0
        self.retransmitted_packets = 0
        self.current_step = 0
        
    def reset(self):
        """Reset environment"""
        self.queue_lengths.clear()
        self.packet_loss.clear()
        self.latency.clear()
        self.total_packets = 0
        self.delivered_packets = 0
        self.retransmitted_packets = 0
        self.current_step = 0
        
        # Initialize queue lengths
        for switch in range(self.num_switches):
            for path in range(self.num_paths_per_switch):
                self.queue_lengths[(switch, path)] = np.random.uniform(0, 100)
        
        return self.get_state()
    
    def get_state(self):
        """Get current network state for each switch"""
        states = []
        for switch in range(self.num_switches):
            # State: [avg_queue_length, max_queue_length, packet_loss_rate, avg_latency]
            queues = [self.queue_lengths[(switch, p)] for p in range(self.num_paths_per_switch)]
            avg_queue = np.mean(queues)
            max_queue = np.max(queues)
            
            losses = [self.packet_loss[(switch, p)] for p in range(self.num_paths_per_switch)]
            loss_rate = np.mean(losses) if self.total_packets > 0 else 0
            
            latencies = []
            for p in range(self.num_paths_per_switch):
                if self.latency[(switch, p)]:
                    latencies.append(np.mean(self.latency[(switch, p)]))
                else:
                    latencies.append(0)
            avg_latency = np.mean(latencies)
            
            state = np.array([avg_queue, max_queue, loss_rate, avg_latency], dtype=np.float32)
            state = (state - np.min(state)) / (np.max(state) - np.min(state) + 1e-8)
            states.append(state)
        
        return np.array(states)
    
    def step(self, actions, incoming_traffic):
        """
        Execute one simulation step
        
        Args:
            actions: List of routing decisions from each agent
            incoming_traffic: Dict {(switch, path): packet_count}
        
        Returns:
            next_states, rewards, done
        """
        self.current_step += 1
        
        # Update queue lengths based on routing decisions
        for switch, action in enumerate(actions):
            # Route traffic to selected path
            if (switch, action) in incoming_traffic:
                packets = incoming_traffic[(switch, action)]
                self.queue_lengths[(switch, action)] += packets
                self.total_packets += packets
        
        # Process packets through links
        rewards = []
        for switch in range(self.num_switches):
            reward = self._process_switch_traffic(switch)
            rewards.append(reward)
        
        next_states = self.get_state()
        done = self.current_step >= 1000
        
        return next_states, np.array(rewards), done
    
    def _process_switch_traffic(self, switch):
        """Process traffic at a switch and calculate reward"""
        total_reward = 0
        congestion_level = 0
        
        for path in range(self.num_paths_per_switch):
            queue_len = self.queue_lengths[(switch, path)]
            
            # Calculate throughput (packets delivered)
            throughput = min(queue_len, self.link_capacity * 0.9)
            self.queue_lengths[(switch, path)] = queue_len - throughput
            self.delivered_packets += throughput
            
            # Calculate packet loss (overflow)
            if queue_len > self.link_capacity:
                loss = queue_len - self.link_capacity
                self.packet_loss[(switch, path)] += loss
                self.retransmitted_packets += loss
                self.queue_lengths[(switch, path)] = self.link_capacity
            
            # Calculate congestion
            utilization = queue_len / self.link_capacity
            congestion_level += utilization
            
            # Add latency
            latency = 5 + (queue_len / self.link_capacity) * 100  # Proportional to queue
            self.latency[(switch, path)].append(latency)
            if len(self.latency[(switch, path)]) > 100:  # Keep only recent latencies
                self.latency[(switch, path)].pop(0)
        
        avg_congestion = congestion_level / self.num_paths_per_switch
        
        # Reward: balance between high throughput and low congestion
        throughput_reward = self.delivered_packets
        congestion_penalty = max(0, avg_congestion - 0.5) * 100
        
        total_reward = throughput_reward - congestion_penalty
        
        return total_reward
    
    def get_metrics(self):
        """Get current network metrics"""
        if self.total_packets == 0:
            return {
                'throughput': 0,
                'retransmit_rate': 0,
                'avg_rtt': 0
            }
        
        # Calculate metrics
        throughput = (self.delivered_packets / self.total_packets) * 100
        retransmit_rate = (self.retransmitted_packets / self.total_packets) * 100
        
        all_latencies = []
        for latencies in self.latency.values():
            all_latencies.extend(latencies)
        
        avg_rtt = np.mean(all_latencies) if all_latencies else 0
        
        return {
            'throughput': throughput,
            'retransmit_rate': retransmit_rate,
            'avg_rtt': avg_rtt,
            'total_packets': self.total_packets,
            'delivered_packets': int(self.delivered_packets),
            'retransmitted_packets': int(self.retransmitted_packets)
        }
