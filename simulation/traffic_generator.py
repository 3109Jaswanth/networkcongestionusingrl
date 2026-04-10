"""
Traffic generation for network simulations
"""

import numpy as np
from collections import defaultdict


class TrafficGenerator:
    """Generate realistic network traffic patterns"""
    
    def __init__(self, num_switches=4, num_paths_per_switch=3):
        """
        Initialize traffic generator
        
        Args:
            num_switches: Number of switches
            num_paths_per_switch: Number of paths per switch
        """
        self.num_switches = num_switches
        self.num_paths = num_paths_per_switch
        self.traffic_state = {}
    
    def generate_normal_traffic(self, base_rate=100):
        """Generate normal/uniform traffic distribution"""
        traffic = {}
        
        for switch in range(self.num_switches):
            for path in range(self.num_paths):
                # 70% chance of traffic on this path
                if np.random.random() < 0.7:
                    # Traffic normally distributed around base_rate
                    packets = np.random.normal(base_rate, base_rate * 0.3)
                    packets = max(0, int(packets))
                    if packets > 0:
                        traffic[(switch, path)] = packets
        
        return traffic
    
    def generate_bursty_traffic(self, base_rate=100, burst_probability=0.2):
        """Generate bursty traffic with occasional spikes"""
        traffic = {}
        
        for switch in range(self.num_switches):
            for path in range(self.num_paths):
                # 50% chance of baseline traffic
                if np.random.random() < 0.5:
                    packets = int(np.random.exponential(base_rate * 0.5))
                    if packets > 0:
                        traffic[(switch, path)] = packets
                
                # Random bursts
                if np.random.random() < burst_probability:
                    burst = int(np.random.exponential(base_rate * 2))
                    if burst > 0:
                        if (switch, path) in traffic:
                            traffic[(switch, path)] += burst
                        else:
                            traffic[(switch, path)] = burst
        
        return traffic
    
    def generate_voip_traffic(self):
        """Generate VoIP-like traffic (small packets, constant rate)"""
        traffic = {}
        
        for switch in range(self.num_switches):
            for path in range(self.num_paths):
                # VoIP: small packets (20-30 bytes) at regular intervals
                if np.random.random() < 0.3:  # 30% VoIP calls active
                    packets = np.random.randint(5, 20)
                    if packets > 0:
                        traffic[(switch, path)] = packets
        
        return traffic
    
    def generate_video_traffic(self):
        """Generate video streaming traffic (bursty, large packets)"""
        traffic = {}
        
        for switch in range(self.num_switches):
            for path in range(self.num_paths):
                # Video: periodic large bursts
                if np.random.random() < 0.2:  # 20% video streams active
                    packets = np.random.randint(100, 500)
                    if packets > 0:
                        traffic[(switch, path)] = packets
        
        return traffic
    
    def generate_mixed_traffic(self):
        """Generate mixed traffic (combination of VoIP, video, and data)"""
        traffic = self.generate_voip_traffic()
        
        # Add video traffic
        video = self.generate_video_traffic()
        for key, value in video.items():
            traffic[key] = traffic.get(key, 0) + value
        
        # Add background data traffic
        data = self.generate_normal_traffic(50)
        for key, value in data.items():
            traffic[key] = traffic.get(key, 0) + value
        
        return traffic
    
    def generate_ddos_attack_traffic(self, target_switch=0, target_paths=[0, 1]):
        """Generate DDoS attack traffic"""
        traffic = self.generate_normal_traffic(base_rate=50)
        
        # Inject large Volume of traffic to target
        for path in target_paths:
            if path < self.num_paths:
                attack_volume = np.random.randint(1000, 5000)
                traffic[(target_switch, path)] = attack_volume
        
        return traffic


class TrafficProfile:
    """Define traffic profiles for different scenarios"""
    
    def __init__(self):
        self.profiles = {
            'normal': lambda gen: gen.generate_normal_traffic(),
            'bursty': lambda gen: gen.generate_bursty_traffic(),
            'voip': lambda gen: gen.generate_voip_traffic(),
            'video': lambda gen: gen.generate_video_traffic(),
            'mixed': lambda gen: gen.generate_mixed_traffic(),
            'ddos': lambda gen: gen.generate_ddos_attack_traffic()
        }
    
    def generate_traffic(self, profile_name, num_switches=4, num_paths=3):
        """Generate traffic based on profile"""
        if profile_name not in self.profiles:
            profile_name = 'normal'
        
        gen = TrafficGenerator(num_switches, num_paths)
        return self.profiles[profile_name](gen)


def print_traffic_stats(traffic):
    """Print statistics about generated traffic"""
    if not traffic:
        print("No traffic generated")
        return
    
    total_packets = sum(traffic.values())
    avg_packets = total_packets / len(traffic) if traffic else 0
    max_packets = max(traffic.values())
    min_packets = min(traffic.values())
    
    print(f"Traffic Statistics:")
    print(f"  Total Packets: {total_packets}")
    print(f"  Average per Path: {avg_packets:.1f}")
    print(f"  Min per Path: {min_packets}")
    print(f"  Max per Path: {max_packets}")
