"""
Example: Generating Visualizations
This script demonstrates all visualization capabilities
"""

import json
import numpy as np
from pathlib import Path

# Must be run from project root
from visualization import (
    SimulationVisualizer,
    TrainingVisualizer,
    NetworkVisualizer,
    generate_all_visualizations
)


def create_sample_results():
    """Create sample simulation results for demonstration"""
    # Ensure all metrics are non-zero to avoid division errors
    results = {
        'rr': {
            'throughput': 82.3,
            'retransmit_rate': 5.2,
            'avg_rtt': 52.1,
            'total_packets': 10000,
            'delivered_packets': 8230,
            'retransmitted_packets': 520
        },
        'wrr': {
            'throughput': 85.1,
            'retransmit_rate': 4.8,
            'avg_rtt': 48.3,
            'total_packets': 10000,
            'delivered_packets': 8510,
            'retransmitted_packets': 480
        },
        'hac_bpnn': {
            'throughput': 87.2,
            'retransmit_rate': 3.1,
            'avg_rtt': 45.7,
            'total_packets': 10000,
            'delivered_packets': 8720,
            'retransmitted_packets': 310
        },
        'madqn': {
            'throughput': 91.5,
            'retransmit_rate': 3.0,
            'avg_rtt': 31.5,
            'total_packets': 10000,
            'delivered_packets': 9150,
            'retransmitted_packets': 300
        }
    }
    
    # Ensure all values are valid (no zeros)
    for alg in results:
        results[alg]['throughput'] = max(results[alg]['throughput'], 0.1)
        results[alg]['retransmit_rate'] = max(results[alg]['retransmit_rate'], 0.1)
        results[alg]['avg_rtt'] = max(results[alg]['avg_rtt'], 0.1)
    
    return results


def create_sample_training_history():
    """Create sample training history for demonstration"""
    episodes = 50
    
    # Simulate convergence
    episode_rewards = []
    episode_metrics = []
    training_losses = []
    
    for ep in range(episodes):
        # Reward increases over time with some noise
        base_reward = 20 + ep * 0.8
        reward = base_reward + np.random.normal(0, 5)
        episode_rewards.append(float(reward))
        
        # Throughput increases
        throughput = 60 + ep * 0.6 + np.random.normal(0, 2)
        throughput = min(95, max(60, throughput))
        
        # Retransmit rate decreases
        retransmit_rate = 8 - ep * 0.1 + np.random.normal(0, 0.5)
        retransmit_rate = max(1, retransmit_rate)
        
        metrics = {
            'throughput': float(throughput),
            'retransmit_rate': float(retransmit_rate),
            'avg_rtt': float(50 - ep * 0.3),
            'total_packets': 1000 + ep * 100,
            'delivered_packets': int(1000 * throughput / 100),
            'retransmitted_packets': int(1000 * retransmit_rate / 100)
        }
        episode_metrics.append(metrics)
        
        # Training loss decreases
        loss = 1.0 / (1 + ep * 0.05) + np.random.normal(0, 0.02)
        training_losses.append(float(loss))
    
    return {
        'episode_rewards': episode_rewards,
        'episode_metrics': episode_metrics,
        'training_losses': training_losses
    }


def example_1_algorithm_comparison():
    """Example 1: Visualize algorithm comparison"""
    print("\n" + "="*60)
    print("Example 1: Algorithm Comparison Visualization")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    results = create_sample_results()
    
    viz = SimulationVisualizer()
    
    # Extract relevant data
    algo_results = {
        alg: {
            'throughput': results[alg]['throughput'],
            'retransmits': results[alg]['retransmit_rate'],
            'rtt': results[alg]['avg_rtt']
        }
        for alg in results.keys()
    }
    
    print("\nGenerating comparison charts...")
    viz.plot_algorithm_comparison(algo_results, 
                                 save_path='results/example_comparison.png')
    print("✓ Saved: results/example_comparison.png")


def example_2_radar_chart():
    """Example 2: Radar chart visualization"""
    print("\n" + "="*60)
    print("Example 2: Performance Radar Chart")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    results = create_sample_results()
    
    viz = SimulationVisualizer()
    
    algo_results = {
        alg: {
            'throughput': results[alg]['throughput'],
            'retransmits': results[alg]['retransmit_rate'],
            'rtt': results[alg]['avg_rtt']
        }
        for alg in results.keys()
    }
    
    print("\nGenerating radar chart...")
    viz.plot_performance_radar(algo_results,
                              save_path='results/example_radar.png')
    print("✓ Saved: results/example_radar.png")


def example_3_improvement():
    """Example 3: Improvement percentage visualization"""
    print("\n" + "="*60)
    print("Example 3: MADQN Improvement Visualization")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    results = create_sample_results()
    
    viz = SimulationVisualizer()
    
    algo_results = {
        alg: {
            'throughput': results[alg]['throughput'],
            'retransmits': results[alg]['retransmit_rate'],
            'rtt': results[alg]['avg_rtt']
        }
        for alg in results.keys()
    }
    
    print("\nGenerating improvement chart...")
    viz.plot_improvement_percentage(algo_results,
                                   save_path='results/example_improvement.png')
    print("✓ Saved: results/example_improvement.png")


def example_4_training_history():
    """Example 4: Training history visualization"""
    print("\n" + "="*60)
    print("Example 4: Training History Visualization")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    history = create_sample_training_history()
    
    viz = TrainingVisualizer()
    
    print("\nGenerating training history charts...")
    viz.plot_training_history(history,
                             save_path='results/example_training_history.png')
    print("✓ Saved: results/example_training_history.png")


def example_5_learning_curve():
    """Example 5: Learning curve visualization"""
    print("\n" + "="*60)
    print("Example 5: Learning Curve Visualization")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    history = create_sample_training_history()
    
    viz = TrainingVisualizer()
    
    print("\nGenerating learning curve...")
    viz.plot_learning_curve(history, window=5,
                           save_path='results/example_learning_curve.png')
    print("✓ Saved: results/example_learning_curve.png")


def example_6_topology():
    """Example 6: Network topology visualization"""
    print("\n" + "="*60)
    print("Example 6: Network Topology Visualization")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    print("\nGenerating network topology...")
    NetworkVisualizer.plot_network_topology(num_switches=4, num_paths=3,
                                           save_path='results/example_topology.png')
    print("✓ Saved: results/example_topology.png")


def example_7_all_visualizations():
    """Example 7: Generate all visualizations at once"""
    print("\n" + "="*60)
    print("Example 7: Generate All Visualizations")
    print("="*60)
    
    Path('results').mkdir(exist_ok=True)
    
    # Create sample data
    results = create_sample_results()
    history = create_sample_training_history()
    
    # Save to files
    with open('results/sample_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    with open('results/sample_history.json', 'w') as f:
        json.dump(history, f, indent=4)
    
    print("\nGenerating all visualizations...")
    generate_all_visualizations(
        results_json_path='results/sample_results.json',
        history_json_path='results/sample_history.json'
    )


def main():
    """Run all examples"""
    print("\n" + "█"*60)
    print("█ MADQN 5G SDN - Visualization Examples")
    print("█"*60)
    
    print("\nThis script demonstrates all visualization capabilities.")
    print("All charts will be saved to results/ directory.\n")
    
    try:
        # Run all examples
        example_1_algorithm_comparison()
        example_2_radar_chart()
        example_3_improvement()
        example_4_training_history()
        example_5_learning_curve()
        example_6_topology()
        example_7_all_visualizations()
        
        print("\n" + "█"*60)
        print("█ All Examples Completed Successfully!")
        print("█"*60)
        print("\nGenerated visualizations:")
        print("  • example_comparison.png - Algorithm comparison")
        print("  • example_radar.png - Radar chart")
        print("  • example_improvement.png - Improvement vs baseline")
        print("  • example_training_history.png - Training metrics")
        print("  • example_learning_curve.png - Smoothed learning")
        print("  • example_topology.png - Network topology")
        print("\n✓ Check results/ directory for all PNG files!")
        print("█"*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
