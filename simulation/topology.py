"""
Network topology for simulations
"""

import numpy as np
from collections import defaultdict


class NetworkTopology:
    """Represents a network topology with switches, links, and paths"""
    
    def __init__(self, num_switches=4, num_paths_per_switch=3, link_capacity=1000):
        """
        Initialize network topology
        
        Args:
            num_switches: Number of switches in the network
            num_paths_per_switch: Number of outgoing paths per switch
            link_capacity: Capacity of each link (packets/time step)
        """
        self.num_switches = num_switches
        self.num_paths = num_paths_per_switch
        self.link_capacity = link_capacity
        
        # Link properties
        self.link_delays = defaultdict(float)  # {(switch, path): delay_ms}
        self.link_loss_rates = defaultdict(float)  # {(switch, path): loss_rate}
        self.link_utilization = defaultdict(float)  # {(switch, path): utilization}
        
        # Initialize link properties
        self._initialize_links()
    
    def _initialize_links(self):
        """Initialize network links with random properties"""
        for switch in range(self.num_switches):
            for path in range(self.num_paths):
                # Random delay between 1-100ms
                self.link_delays[(switch, path)] = np.random.uniform(1, 100)
                
                # Small loss rate (0-5%)
                self.link_loss_rates[(switch, path)] = np.random.uniform(0, 0.05)
    
    def get_link_delay(self, switch, path):
        """Get delay for a specific link"""
        return self.link_delays.get((switch, path), 10)
    
    def get_link_loss_rate(self, switch, path):
        """Get loss rate for a specific link"""
        return self.link_loss_rates.get((switch, path), 0.01)
    
    def update_link_utilization(self, switch, path, packets):
        """Update link utilization based on transmitted packets"""
        utilization = (packets / self.link_capacity) * 100
        self.link_utilization[(switch, path)] = utilization
    
    def get_link_utilization(self, switch, path):
        """Get current link utilization percentage"""
        return self.link_utilization.get((switch, path), 0)
    
    def get_congested_links(self, threshold=80):
        """Get links with utilization above threshold"""
        congested = []
        for (switch, path), util in self.link_utilization.items():
            if util > threshold:
                congested.append((switch, path, util))
        return congested


class TopologyBuilder:
    """Helper class to build different network topologies"""
    
    @staticmethod
    def create_3_tier_topology(num_switches_per_tier=2):
        """Create a 3-tier topology (Access, Aggregation, Core)"""
        total_switches = num_switches_per_tier * 3
        topology = NetworkTopology(num_switches=total_switches, num_paths_per_switch=3)
        
        # Access tier: 0 to num_switches_per_tier-1
        # Aggregation tier: num_switches_per_tier to 2*num_switches_per_tier-1
        # Core tier: 2*num_switches_per_tier to total_switches-1
        
        return topology
    
    @staticmethod
    def create_mesh_topology(num_switches=4):
        """Create a full mesh topology"""
        return NetworkTopology(num_switches=num_switches, num_paths_per_switch=num_switches-1)
    
    @staticmethod
    def create_fat_tree_topology(k=4):
        """Create a fat-tree topology"""
        # k: ports per switch
        # Total switches = 5k²/4
        num_switches = int(5 * (k ** 2) / 4)
        return NetworkTopology(num_switches=num_switches, num_paths_per_switch=k)


def visualize_topology(topology):
    """Print topology information"""
    print(f"Network Topology Information")
    print(f"  Total Switches: {topology.num_switches}")
    print(f"  Paths per Switch: {topology.num_paths}")
    print(f"  Link Capacity: {topology.link_capacity} packets/step")
    print()
    
    print("Link Properties:")
    for switch in range(min(3, topology.num_switches)):
        for path in range(topology.num_paths):
            delay = topology.get_link_delay(switch, path)
            loss = topology.get_link_loss_rate(switch, path)
            print(f"  Link ({switch},{path}): Delay={delay:.1f}ms, Loss={loss:.2%}")
