"""
Visualization module for MADQN project
Generates comprehensive charts and graphs for training and simulation results
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import json
from pathlib import Path


class SimulationVisualizer:
    """Create visualizations for simulation results"""
    
    def __init__(self, style='seaborn-v0_8-darkgrid'):
        """Initialize visualizer with seaborn style"""
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        sns.set_palette("husl")
    
    def plot_algorithm_comparison(self, results_dict, save_path='results/comparison.png'):
        """
        Plot comparison of all algorithms
        
        Args:
            results_dict: Dict with {algorithm: {throughput, retransmits, rtt}}
            save_path: Where to save the figure
        """
        algorithms = list(results_dict.keys())
        throughput = [results_dict[alg]['throughput'] for alg in algorithms]
        retransmits = [results_dict[alg]['retransmits'] for alg in algorithms]
        rtt = [results_dict[alg]['rtt'] for alg in algorithms]
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('Load Balancing Algorithm Comparison', fontsize=16, fontweight='bold')
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        # Throughput
        bars1 = axes[0].bar(algorithms, throughput, color=colors, edgecolor='black', linewidth=1.5)
        axes[0].set_ylabel('Throughput (%)', fontsize=11, fontweight='bold')
        axes[0].set_title('Throughput Comparison', fontsize=12, fontweight='bold')
        axes[0].set_ylim([75, 100])
        axes[0].grid(axis='y', alpha=0.3)
        for bar, val in zip(bars1, throughput):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Retransmits
        bars2 = axes[1].bar(algorithms, retransmits, color=colors, edgecolor='black', linewidth=1.5)
        axes[1].set_ylabel('Retransmit Rate (%)', fontsize=11, fontweight='bold')
        axes[1].set_title('Packet Loss Comparison', fontsize=12, fontweight='bold')
        axes[1].set_ylim([0, 6])
        axes[1].grid(axis='y', alpha=0.3)
        for bar, val in zip(bars2, retransmits):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.2f}%', ha='center', va='bottom', fontweight='bold')
        
        # RTT
        bars3 = axes[2].bar(algorithms, rtt, color=colors, edgecolor='black', linewidth=1.5)
        axes[2].set_ylabel('Average RTT (ms)', fontsize=11, fontweight='bold')
        axes[2].set_title('Latency Comparison', fontsize=12, fontweight='bold')
        axes[2].set_ylim([25, 55])
        axes[2].grid(axis='y', alpha=0.3)
        for bar, val in zip(bars3, rtt):
            height = bar.get_height()
            axes[2].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.1f}ms', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()
    
    def plot_performance_radar(self, results_dict, save_path='results/radar_comparison.png'):
        """Create radar chart comparing algorithms"""
        algorithms = list(results_dict.keys())
        
        # Normalize metrics to 0-100 scale with safe division
        throughput = [results_dict[alg]['throughput'] for alg in algorithms]
        retransmits = [100 - results_dict[alg]['retransmits'] for alg in algorithms]  # Invert for radar
        
        # Safely normalize RTT (avoid division by zero)
        max_rtt = max((results_dict[alg]['rtt'] for alg in algorithms), default=60)
        if max_rtt > 0:
            rtt = [100 - (results_dict[alg]['rtt'] / max_rtt * 100) for alg in algorithms]
        else:
            rtt = [100] * len(algorithms)
        
        categories = ['Throughput', 'Packet Loss\nReduction', 'Latency\nReduction']
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for idx, alg in enumerate(algorithms):
            values = [throughput[idx], retransmits[idx], rtt[idx]]
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=alg, color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=11, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
        ax.grid(True, alpha=0.3)
        
        plt.title('Algorithm Performance Radar', fontsize=14, fontweight='bold', pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()
    
    def plot_improvement_percentage(self, results_dict, baseline='hac_bpnn', 
                                   save_path='results/improvement.png'):
        """Plot MADQN improvement over baseline"""
        baseline_results = results_dict[baseline]
        
        improvements = {}
        for alg, results in results_dict.items():
            if alg != baseline:
                # Handle division by zero with safe division
                def safe_improvement(baseline_val, current_val):
                    if baseline_val == 0 or baseline_val is None:
                        return 0
                    return ((baseline_val - current_val) / baseline_val * 100)
                
                throughput_imp = safe_improvement(baseline_results['throughput'], 
                                                 results['throughput'])
                retransmit_imp = safe_improvement(baseline_results['retransmits'], 
                                                 results['retransmits'])
                rtt_imp = safe_improvement(baseline_results['rtt'], 
                                          results['rtt'])
                improvements[alg] = {
                    'throughput': throughput_imp,
                    'retransmits': retransmit_imp,
                    'rtt': rtt_imp
                }
        
        algorithms = list(improvements.keys())
        x = np.arange(len(algorithms))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        throughput_imp = [improvements[alg]['throughput'] for alg in algorithms]
        retransmit_imp = [improvements[alg]['retransmits'] for alg in algorithms]
        rtt_imp = [improvements[alg]['rtt'] for alg in algorithms]
        
        bars1 = ax.bar(x - width, throughput_imp, width, label='Throughput', color='#96CEB4')
        bars2 = ax.bar(x, retransmit_imp, width, label='Packet Loss Reduction', color='#4ECDC4')
        bars3 = ax.bar(x + width, rtt_imp, width, label='Latency Reduction', color='#FF6B6B')
        
        ax.set_ylabel('Improvement (%)', fontsize=11, fontweight='bold')
        ax.set_title(f'Algorithm Improvement vs {baseline.upper()}', fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(algorithms)
        ax.legend(fontsize=10)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()


class TrainingVisualizer:
    """Visualize MADQN training progress"""
    
    def plot_training_history(self, history_dict, save_path='results/training_history.png'):
        """Plot training history from training_history.json"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('MADQN Training History', fontsize=16, fontweight='bold')
        
        # Episode rewards
        episode_rewards = history_dict.get('episode_rewards', [])
        if episode_rewards:
            episodes = range(len(episode_rewards))
            axes[0, 0].plot(episodes, episode_rewards, linewidth=2, color='#4ECDC4')
            axes[0, 0].fill_between(episodes, episode_rewards, alpha=0.3, color='#4ECDC4')
            axes[0, 0].set_xlabel('Episode', fontweight='bold')
            axes[0, 0].set_ylabel('Average Reward', fontweight='bold')
            axes[0, 0].set_title('Episode Rewards', fontweight='bold')
            axes[0, 0].grid(True, alpha=0.3)
        
        # Episode metrics
        episode_metrics = history_dict.get('episode_metrics', [])
        if episode_metrics:
            throughputs = [m.get('throughput', 0) for m in episode_metrics]
            episodes = range(len(throughputs))
            axes[0, 1].plot(episodes, throughputs, linewidth=2, color='#96CEB4')
            axes[0, 1].fill_between(episodes, throughputs, alpha=0.3, color='#96CEB4')
            axes[0, 1].set_xlabel('Episode', fontweight='bold')
            axes[0, 1].set_ylabel('Throughput (%)', fontweight='bold')
            axes[0, 1].set_title('Throughput Over Training', fontweight='bold')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Retransmit rate
        if episode_metrics:
            retransmits = [m.get('retransmit_rate', 0) for m in episode_metrics]
            episodes = range(len(retransmits))
            axes[1, 0].plot(episodes, retransmits, linewidth=2, color='#FF6B6B')
            axes[1, 0].fill_between(episodes, retransmits, alpha=0.3, color='#FF6B6B')
            axes[1, 0].set_xlabel('Episode', fontweight='bold')
            axes[1, 0].set_ylabel('Retransmit Rate (%)', fontweight='bold')
            axes[1, 0].set_title('Retransmit Rate Over Training', fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Training loss
        training_losses = history_dict.get('training_losses', [])
        if training_losses and any(training_losses):
            episodes = range(len(training_losses))
            # Filter out zeros for better visualization
            losses_filtered = [l if l > 0 else np.nan for l in training_losses]
            axes[1, 1].plot(episodes, losses_filtered, linewidth=2, color='#45B7D1', marker='o', markersize=3)
            axes[1, 1].set_xlabel('Episode', fontweight='bold')
            axes[1, 1].set_ylabel('Average Loss', fontweight='bold')
            axes[1, 1].set_title('Training Loss', fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()
    
    def plot_learning_curve(self, history_dict, window=5, save_path='results/learning_curve.png'):
        """Plot smoothed learning curve"""
        episode_rewards = history_dict.get('episode_rewards', [])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        episodes = range(len(episode_rewards))
        ax.plot(episodes, episode_rewards, alpha=0.3, linewidth=1, label='Raw', color='#4ECDC4')
        
        # Smoothed with moving average
        if len(episode_rewards) >= window:
            smoothed = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
            smoothed_episodes = range(window-1, len(episode_rewards))
            ax.plot(smoothed_episodes, smoothed, linewidth=2.5, label=f'Moving Average (window={window})', 
                   color='#FF6B6B')
        
        ax.set_xlabel('Episode', fontsize=11, fontweight='bold')
        ax.set_ylabel('Average Reward', fontsize=11, fontweight='bold')
        ax.set_title('MADQN Learning Curve', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()


class NetworkVisualizer:
    """Visualize network topology and metrics"""
    
    @staticmethod
    def plot_network_topology(num_switches=4, num_paths=3, 
                             save_path='results/topology.png'):
        """Draw network topology diagram"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw switches in a circle
        angles = np.linspace(0, 2*np.pi, num_switches, endpoint=False)
        radius = 3
        
        x_pos = radius * np.cos(angles)
        y_pos = radius * np.sin(angles)
        
        # Draw switches
        for i, (x, y) in enumerate(zip(x_pos, y_pos)):
            circle = plt.Circle((x, y), 0.3, color='#4ECDC4', ec='black', linewidth=2, zorder=3)
            ax.add_patch(circle)
            ax.text(x, y, f'S{i}', ha='center', va='center', fontweight='bold', fontsize=10, zorder=4)
        
        # Draw paths between switches
        for i in range(num_switches):
            for j in range(i+1, num_switches):
                x_line = [x_pos[i], x_pos[j]]
                y_line = [y_pos[i], y_pos[j]]
                ax.plot(x_line, y_line, 'k-', linewidth=1.5, alpha=0.5, zorder=1)
        
        # Add path labels
        for i, (x, y) in enumerate(zip(x_pos, y_pos)):
            # Draw multiple outgoing paths for each switch
            outer_angle_offset = 0.5
            for p in range(num_paths):
                path_angle = angles[i] + np.pi + (p - num_paths/2) * outer_angle_offset
                path_x = x + 0.7 * np.cos(path_angle)
                path_y = y + 0.7 * np.sin(path_angle)
                ax.plot([x, path_x], [y, path_y], 'b--', linewidth=1, alpha=0.4)
        
        ax.set_xlim([-4.5, 4.5])
        ax.set_ylim([-4.5, 4.5])
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Network Topology', fontsize=14, fontweight='bold', pad=20)
        
        # Add legend
        switch_patch = mpatches.Patch(color='#4ECDC4', label=f'Switches (n={num_switches})')
        path_patch = mpatches.Patch(color='blue', label=f'Paths per Switch (n={num_paths})', linestyle='--')
        ax.legend(handles=[switch_patch, path_patch], loc='upper right', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()
    
    @staticmethod
    def plot_queue_heatmap(metrics_over_time, switches=4, paths=3, 
                          save_path='results/queue_heatmap.png'):
        """Plot heatmap of queue lengths over time"""
        # Create matrix of queue data
        time_steps = len(metrics_over_time)
        queue_matrix = np.zeros((switches * paths, time_steps))
        
        for t, metrics in enumerate(metrics_over_time):
            for switch in range(switches):
                for path in range(paths):
                    # Simulate queue data
                    queue_matrix[switch * paths + path, t] = np.random.uniform(0, 100)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        im = ax.imshow(queue_matrix, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        
        ax.set_xlabel('Time Step', fontweight='bold', fontsize=11)
        ax.set_ylabel('Switch.Path', fontweight='bold', fontsize=11)
        ax.set_title('Queue Length Heatmap Over Time', fontweight='bold', fontsize=13)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Queue Length', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {save_path}")
        plt.close()


def generate_all_visualizations(results_json_path=None, history_json_path=None):
    """Generate all visualizations at once"""
    print("\n" + "="*60)
    print("Generating Visualizations")
    print("="*60 + "\n")
    
    # Create results directory
    Path('results').mkdir(exist_ok=True)
    
    sim_viz = SimulationVisualizer()
    train_viz = TrainingVisualizer()
    net_viz = NetworkVisualizer()
    
    # Load and visualize simulation results
    if results_json_path and Path(results_json_path).exists():
        print(f"Loading simulation results from {results_json_path}...")
        with open(results_json_path, 'r') as f:
            results_dict = json.load(f)
        
        # Extract algorithm results
        algo_results = {}
        for alg in ['rr', 'wrr', 'hac_bpnn', 'madqn']:
            if alg in results_dict:
                algo_results[alg] = {
                    'throughput': results_dict[alg].get('throughput', 0),
                    'retransmits': results_dict[alg].get('retransmits', 0),
                    'rtt': results_dict[alg].get('rtt', 0)
                }
        
        if algo_results:
            sim_viz.plot_algorithm_comparison(algo_results)
            sim_viz.plot_performance_radar(algo_results)
            sim_viz.plot_improvement_percentage(algo_results)
    
    # Load and visualize training history
    if history_json_path and Path(history_json_path).exists():
        print(f"\nLoading training history from {history_json_path}...")
        with open(history_json_path, 'r') as f:
            history_dict = json.load(f)
        
        if history_dict:
            train_viz.plot_training_history(history_dict)
            train_viz.plot_learning_curve(history_dict)
    
    # Generate network topology diagram
    net_viz.plot_network_topology(num_switches=4, num_paths=3)
    
    print("\n" + "="*60)
    print("✓ All visualizations generated!")
    print("✓ Check results/ directory for PNG files")
    print("="*60 + "\n")


if __name__ == "__main__":
    generate_all_visualizations(
        results_json_path='results/simulation_results.json',
        history_json_path='results/training_history.json'
    )
