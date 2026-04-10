"""
Main entry point for MADQN 5G SDN Load Balancing Project
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from madqn.train import MADQNTrainer
from simulation.run_simulation import SimulationRunner
from visualization import generate_all_visualizations


def main():
    parser = argparse.ArgumentParser(
        description='MADQN 5G SDN Load Balancing - Training and Simulation'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train MADQN agents')
    train_parser.add_argument('--episodes', type=int, default=100,
                            help='Number of training episodes (default: 100)')
    train_parser.add_argument('--batch_size', type=int, default=32,
                            help='Training batch size (default: 32)')
    train_parser.add_argument('--agents', type=int, default=4,
                            help='Number of agents (default: 4)')
    
    # Simulate command
    sim_parser = subparsers.add_parser('simulate', help='Run simulations')
    sim_parser.add_argument('--traffic', type=str, default='normal',
                          choices=['normal', 'bursty', 'voip', 'video', 'mixed', 'ddos'],
                          help='Traffic pattern (default: normal)')
    sim_parser.add_argument('--steps', type=int, default=500,
                          help='Simulation steps (default: 500)')
    sim_parser.add_argument('--switches', type=int, default=4,
                          help='Number of switches (default: 4)')
    
    # Combined command
    combined_parser = subparsers.add_parser('all', help='Train and then simulate')
    combined_parser.add_argument('--episodes', type=int, default=50,
                               help='Training episodes (default: 50)')
    
    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='Generate visualizations')
    viz_parser.add_argument('--results', type=str, default='results/simulation_results.json',
                          help='Simulation results JSON file')
    viz_parser.add_argument('--history', type=str, default='results/training_history.json',
                          help='Training history JSON file')
    
    args = parser.parse_args()
    
    if args.command == 'train':
        print("\n" + "="*60)
        print("MADQN Training")
        print("="*60)
        
        trainer = MADQNTrainer(
            num_agents=args.agents,
            episodes=args.episodes,
            batch_size=args.batch_size
        )
        trainer.train()
        
        # Save models
        trainer.save_models('./models/madqn')
        trainer.save_training_history('./results/training_history.json')
        
        print("\nTraining completed!")
        print(f"Models saved to: ./models/madqn/")
        print(f"History saved to: ./results/training_history.json")
    
    elif args.command == 'simulate':
        print("\n" + "="*60)
        print(f"Running Simulation - Traffic: {args.traffic}")
        print("="*60)
        
        runner = SimulationRunner(
            num_switches=args.switches,
            simulation_steps=args.steps
        )
        
        results = runner.run_all_simulations(traffic_pattern=args.traffic)
        runner.compare_results()
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        runner.save_results(f'./results/simulation_results_{timestamp}.json')
    
    elif args.command == 'all':
        print("\n" + "="*60)
        print("Complete MADQN Workflow: Training + Simulation")
        print("="*60)
        
        # Train
        print("\n>>> Starting Training Phase...")
        trainer = MADQNTrainer(episodes=args.episodes)
        trainer.train()
        trainer.save_models('./models/madqn')
        trainer.save_training_history('./results/training_history.json')
        
        # Simulate
        print("\n>>> Starting Simulation Phase...")
        runner = SimulationRunner()
        results = runner.run_all_simulations(traffic_pattern='mixed')
        runner.compare_results()
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        runner.save_results(f'./results/simulation_results_{timestamp}.json')
        
        print("\n" + "="*60)
        print("Complete workflow finished!")
        print("="*60)
    
    elif args.command == 'visualize':
        print("\n" + "="*60)
        print("Generating Visualizations")
        print("="*60)
        
        from pathlib import Path
        
        results_path = args.results if Path(args.results).exists() else None
        history_path = args.history if Path(args.history).exists() else None
        
        if not results_path and not history_path:
            print("⚠ No results or history files found!")
            print("Please run 'python main.py train' or 'python main.py simulate' first")
        else:
            generate_all_visualizations(results_path, history_path)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
