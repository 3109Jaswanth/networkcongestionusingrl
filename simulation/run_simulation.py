"""
Main simulation runner for comparing load balancing algorithms
"""

import numpy as np
import json
import random
from datetime import datetime

from madqn.agent import MultiAgentDQN
from madqn.environment import NetworkEnvironment
from sdn_controller.load_balancer import LoadBalancerController
from simulation.topology import NetworkTopology, TopologyBuilder
from simulation.traffic_generator import TrafficGenerator, TrafficProfile


class SimulationRunner:
    """Run simulations comparing different load balancing algorithms"""
    
    def __init__(self, num_switches=4, num_paths=3, simulation_steps=1000, seed=None,
                 link_capacity=250, queue_threshold=400):
        """
        Initialize simulation runner
        
        Args:
            num_switches: Number of switches
            num_paths: Number of paths per switch
            simulation_steps: Number of simulation steps to run
            seed: Optional random seed for reproducibility
            link_capacity: Packets served per link per step
            queue_threshold: Max queue length before dropping packets
        """
        self.num_switches = num_switches
        self.num_paths = num_paths
        self.simulation_steps = simulation_steps
        self.seed = seed
        self.link_capacity = link_capacity
        self.queue_threshold = queue_threshold

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        self.topology = NetworkTopology(num_switches, num_paths, link_capacity=link_capacity)
        self.traffic_generator = TrafficGenerator(num_switches, num_paths)
        self.traffic_profile = TrafficProfile()
        
        self.results = {
            'madqn': {'throughput': [], 'rtt': [], 'retransmits': [], 'metrics': [], 'time_series': [], 'queue_history': [], 'actions': []},
            'rr': {'throughput': [], 'rtt': [], 'retransmits': [], 'metrics': [], 'time_series': [], 'queue_history': [], 'actions': []},
            'wrr': {'throughput': [], 'rtt': [], 'retransmits': [], 'metrics': [], 'time_series': [], 'queue_history': [], 'actions': []},
            'hac_bpnn': {'throughput': [], 'rtt': [], 'retransmits': [], 'metrics': [], 'time_series': [], 'queue_history': [], 'actions': []}
        }

    def _record_step(self, algorithm, step, env, actions):
        step_metrics = env.get_step_metrics()
        self.results[algorithm]['time_series'].append({
            'step': step,
            'throughput': step_metrics['throughput'],
            'retransmit_rate': step_metrics['retransmit_rate'],
            'avg_rtt': step_metrics['avg_rtt'],
            'queue_lengths': {f"{s}_{p}": float(env.queue_lengths[(s, p)])
                              for s in range(self.num_switches)
                              for p in range(self.num_paths)},
            'actions': actions.copy()
        })
        self.results[algorithm]['queue_history'].append({
            f"{s}_{p}": float(env.queue_lengths[(s, p)])
            for s in range(self.num_switches)
            for p in range(self.num_paths)
        })
        self.results[algorithm]['actions'].append(actions.copy())

        return step_metrics
    
    def run_madqn_simulation(self, trained_madqn=None, traffic_pattern='normal'):
        """Run simulation with MADQN"""
        print("\n=== Running MADQN Simulation ===")
        
        if trained_madqn is None:
            madqn = MultiAgentDQN(self.num_switches, state_size=4, action_size=self.num_paths)
        else:
            madqn = trained_madqn

        # Evaluate policy greedily (no exploration randomness).
        original_epsilons = [agent.epsilon for agent in madqn.agents]
        for agent in madqn.agents:
            agent.epsilon = 0.0
        
        env = NetworkEnvironment(
            self.num_switches,
            self.num_paths,
            link_capacity=self.link_capacity,
            queue_threshold=self.queue_threshold,
            max_steps=self.simulation_steps
        )
        states = env.reset()
        
        for step in range(self.simulation_steps):
            # Get actions from all agents
            actions = []
            for agent_id in range(self.num_switches):
                action = madqn.act(agent_id, states[agent_id])
                actions.append(action)
            actions = [int(a) for a in actions]
            
            # Generate traffic
            traffic = self.traffic_profile.generate_traffic(traffic_pattern, 
                                                           self.num_switches, 
                                                           self.num_paths)
            
            # Step environment
            next_states, rewards, done = env.step(actions, traffic)
            
            # Collect step metrics
            states = next_states
            step_metrics = self._record_step('madqn', step, env, actions)
            
            if step % 100 == 0:
                self.results['madqn']['metrics'].append(dict(step_metrics))
                print(f"  Step {step}: Throughput={step_metrics['throughput']:.2f}%, "
                      f"RTT={step_metrics['avg_rtt']:.2f}ms")

            if done:
                break
        
        # Final metrics
        final_metrics = env.get_metrics()
        self.results['madqn']['throughput'] = final_metrics['throughput']
        self.results['madqn']['retransmits'] = final_metrics['retransmit_rate']
        self.results['madqn']['rtt'] = final_metrics['avg_rtt']

        # Restore training-time epsilons.
        for agent, epsilon in zip(madqn.agents, original_epsilons):
            agent.epsilon = epsilon
        
        return final_metrics
    
    def run_baseline_simulation(self, algorithm, traffic_pattern='normal'):
        """Run simulation with baseline algorithm"""
        print(f"\n=== Running {algorithm.upper()} Simulation ===")
        
        controller = LoadBalancerController(algorithm, self.num_switches, self.num_paths)
        env = NetworkEnvironment(
            self.num_switches,
            self.num_paths,
            link_capacity=self.link_capacity,
            queue_threshold=self.queue_threshold,
            max_steps=self.simulation_steps
        )
        states = env.reset()
        
        for step in range(self.simulation_steps):
            # Generate traffic
            traffic = self.traffic_profile.generate_traffic(traffic_pattern,
                                                           self.num_switches,
                                                           self.num_paths)
            
            # Get routing decisions
            actions = []
            for switch in range(self.num_switches):
                action = controller.get_routing_decision(switch, states[switch])
                actions.append(action)
            actions = [int(a) for a in actions]

            next_states, _, done = env.step(actions, traffic)
            states = next_states

            step_metrics = self._record_step(algorithm, step, env, actions)
            
            if step % 100 == 0:
                self.results[algorithm]['metrics'].append(dict(step_metrics))
                print(f"  Step {step}: Throughput={step_metrics['throughput']:.2f}%")

            if done:
                break
        metrics = env.get_metrics()
        
        self.results[algorithm]['throughput'] = metrics['throughput']
        self.results[algorithm]['retransmits'] = metrics['retransmit_rate']
        self.results[algorithm]['rtt'] = metrics['avg_rtt']
        
        return metrics
    
    def run_all_simulations(self, traffic_pattern='normal'):
        """Run all simulation scenarios"""
        print(f"\n{'='*60}")
        print(f"Starting Simulations - Traffic Pattern: {traffic_pattern}")
        print(f"{'='*60}")
        
        # Run baseline algorithms
        rr_metrics = self.run_baseline_simulation('rr', traffic_pattern)
        wrr_metrics = self.run_baseline_simulation('wrr', traffic_pattern)
        hac_metrics = self.run_baseline_simulation('hac_bpnn', traffic_pattern)
        
        # Run MADQN
        madqn_metrics = self.run_madqn_simulation(traffic_pattern=traffic_pattern)
        
        return {
            'rr': rr_metrics,
            'wrr': wrr_metrics,
            'hac_bpnn': hac_metrics,
            'madqn': madqn_metrics
        }
    
    def compare_results(self):
        """Compare simulation results"""
        print(f"\n{'='*60}")
        print("Simulation Results Comparison")
        print(f"{'='*60}")
        
        print(f"\n{'Algorithm':<15} {'Throughput':<15} {'Retransmits':<15} {'RTT':<15}")
        print("-" * 60)
        
        for algorithm in ['rr', 'wrr', 'hac_bpnn', 'madqn']:
            throughput = self.results[algorithm]['throughput']
            retransmits = self.results[algorithm]['retransmits']
            rtt = self.results[algorithm]['rtt']
            
            print(f"{algorithm:<15} {throughput:>6.2f}%{'':<7} {retransmits:>6.2f}%{'':<7} {rtt:>6.2f}ms")
        
        # Calculate MADQN improvement over HAC+BPNN
        hac_throughput = self.results['hac_bpnn']['throughput']
        madqn_throughput = self.results['madqn']['throughput']
        
        if hac_throughput > 0:
            improvement = ((madqn_throughput - hac_throughput) / hac_throughput) * 100
            print(f"\nMADQN improvement over HAC+BPNN: {improvement:.2f}%")
    
    def save_results(self, filepath):
        """Save results to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\nResults saved to {filepath}")


def main():
    """Main simulation runner"""
    # Initialize simulation
    runner = SimulationRunner(num_switches=4, num_paths=3, simulation_steps=500)
    
    # Run simulations with different traffic patterns
    for traffic_pattern in ['normal', 'bursty']:
        results = runner.run_all_simulations(traffic_pattern=traffic_pattern)
    
    # Compare and display results
    runner.compare_results()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runner.save_results(f'results/simulation_results_{timestamp}.json')


if __name__ == "__main__":
    main()
