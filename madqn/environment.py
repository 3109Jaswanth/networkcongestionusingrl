"""
Network simulation environment for MADQN training
"""

import numpy as np
from collections import defaultdict


class NetworkEnvironment:
    """Simulated network environment for multi-agent reinforcement learning"""
    
    def __init__(self, num_switches=4, num_paths_per_switch=3, 
                 link_capacity=250, queue_threshold=400, max_steps=1000):
        """
        Initialize network environment
        
        Args:
            num_switches: Number of switches in the network
            num_paths_per_switch: Number of outgoing paths per switch
            link_capacity: Maximum capacity of each link (packets/time step)
            queue_threshold: Queue buffer threshold per link before dropping
            max_steps: Maximum steps per episode
        """
        self.num_switches = num_switches
        self.num_paths_per_switch = num_paths_per_switch
        self.link_capacity = link_capacity
        self.queue_threshold = queue_threshold
        self.max_steps = max_steps
        
        # Network state
        self.queue_lengths = defaultdict(float)  # {(switch, path): queue_length}
        self.packet_loss = defaultdict(int)  # {(switch, path): lost_packets}
        self.latency = defaultdict(list)  # {(switch, path): latencies}
        
        # Statistics
        self.total_packets = 0
        self.delivered_packets = 0
        self.retransmitted_packets = 0
        self.current_step = 0
        self.last_step_metrics = {
            'offered': 0,
            'served': 0,
            'dropped': 0,
            'throughput': 0,
            'retransmit_rate': 0,
            'avg_rtt': 0
        }
        
    def reset(self):
        """Reset environment"""
        self.queue_lengths.clear()
        self.packet_loss.clear()
        self.latency.clear()
        self.total_packets = 0
        self.delivered_packets = 0
        self.retransmitted_packets = 0
        self.current_step = 0
        
        # Start with empty queues so throughput accounting is physically valid.
        for switch in range(self.num_switches):
            for path in range(self.num_paths_per_switch):
                self.queue_lengths[(switch, path)] = 0.0
        
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
        
        offered_by_switch = {switch: 0.0 for switch in range(self.num_switches)}
        queue_before = {
            (switch, path): float(self.queue_lengths[(switch, path)])
            for switch in range(self.num_switches)
            for path in range(self.num_paths_per_switch)
        }
        routed_offered = {
            (switch, path): 0.0
            for switch in range(self.num_switches)
            for path in range(self.num_paths_per_switch)
        }

        # Route all offered traffic at a switch to the chosen action/path.
        for switch, action in enumerate(actions):
            offered = 0
            for path in range(self.num_paths_per_switch):
                offered += float(incoming_traffic.get((switch, path), 0))

            offered_by_switch[switch] = offered
            routed_offered[(switch, action)] = offered
            self.queue_lengths[(switch, action)] += offered
            self.total_packets += offered
        
        # Process packets through links
        rewards = []
        step_served = 0.0
        step_served_from_offered = 0.0
        step_dropped = 0.0
        for switch in range(self.num_switches):
            reward, served, dropped, served_from_offered = self._process_switch_traffic(
                switch,
                offered_by_switch[switch],
                routed_offered,
                queue_before
            )
            rewards.append(reward)
            step_served += served
            step_served_from_offered += served_from_offered
            step_dropped += dropped

        step_offered = float(sum(offered_by_switch.values()))

        all_latencies = []
        for latencies in self.latency.values():
            all_latencies.extend(latencies)

        self.last_step_metrics = {
            'offered': step_offered,
            'served': step_served_from_offered,
            'served_total': step_served,
            'dropped': step_dropped,
            'throughput': (step_served_from_offered / step_offered * 100) if step_offered > 0 else 0,
            'retransmit_rate': (step_dropped / step_offered * 100) if step_offered > 0 else 0,
            'avg_rtt': float(np.mean(all_latencies)) if all_latencies else 0
        }
        
        next_states = self.get_state()
        done = self.current_step >= self.max_steps
        
        return next_states, np.array(rewards), done
    
    def _process_switch_traffic(self, switch, offered, routed_offered, queue_before):
        """Process traffic at a switch and calculate reward"""
        total_reward = 0.0
        congestion_level = 0.0
        switch_served = 0.0
        switch_served_from_offered = 0.0
        switch_dropped = 0.0
        
        for path in range(self.num_paths_per_switch):
            queue_len = self.queue_lengths[(switch, path)]
            
            # Serve up to link capacity from queued packets.
            served = min(queue_len, self.link_capacity)
            queue_after_service = queue_len - served
            self.delivered_packets += served
            switch_served += served

            offered_on_path = routed_offered[(switch, path)]
            before_on_path = queue_before[(switch, path)]
            backlog_served = min(before_on_path, self.link_capacity)
            remaining_capacity = max(0.0, self.link_capacity - backlog_served)
            served_from_offered = min(offered_on_path, remaining_capacity)
            switch_served_from_offered += served_from_offered
            
            # Drop packets if queue exceeds buffer threshold.
            dropped = max(0.0, queue_after_service - self.queue_threshold)
            if dropped > 0:
                self.packet_loss[(switch, path)] += dropped
                self.retransmitted_packets += dropped
                switch_dropped += dropped
            self.queue_lengths[(switch, path)] = min(queue_after_service, self.queue_threshold)
            
            # Calculate congestion
            utilization = self.queue_lengths[(switch, path)] / max(1.0, self.queue_threshold)
            congestion_level += utilization
            
            # Add latency
            latency = 5 + (self.queue_lengths[(switch, path)] / max(1.0, self.queue_threshold)) * 50
            self.latency[(switch, path)].append(latency)
            if len(self.latency[(switch, path)]) > 100:  # Keep only recent latencies
                self.latency[(switch, path)].pop(0)
        
        avg_congestion = congestion_level / self.num_paths_per_switch
        
        # Reward: maximize served traffic while minimizing drops and congestion.
        served_ratio = (switch_served / offered) if offered > 0 else 0
        drop_ratio = (switch_dropped / offered) if offered > 0 else 0
        throughput_reward = served_ratio * 100
        drop_penalty = drop_ratio * 200
        congestion_penalty = max(0, avg_congestion - 0.7) * 50
        
        total_reward = throughput_reward - drop_penalty - congestion_penalty
        
        return total_reward, switch_served, switch_dropped, switch_served_from_offered
    
    def get_metrics(self):
        """Get current network metrics"""
        if self.total_packets == 0:
            return {
                'throughput': 0,
                'retransmit_rate': 0,
                'avg_rtt': 0
            }
        
        # Cumulative metrics across episode.
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

    def get_step_metrics(self):
        """Get metrics for the most recent step."""
        return dict(self.last_step_metrics)
