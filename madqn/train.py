"""
Training script for MADQN
"""

import numpy as np
import os
from .agent import MultiAgentDQN
from .environment import NetworkEnvironment
from .utils import save_metrics


def generate_traffic(num_switches, num_paths, traffic_pattern='normal'):
    """Generate incoming traffic for the network"""
    traffic = {}
    
    if traffic_pattern == 'normal':
        # Normal traffic distribution
        for switch in range(num_switches):
            for path in range(num_paths):
                if np.random.random() < 0.7:  # 70% chance of traffic
                    traffic[(switch, path)] = np.random.randint(50, 200)
    
    elif traffic_pattern == 'bursty':
        # Bursty traffic with high variance
        for switch in range(num_switches):
            chosen_path = np.random.randint(0, num_paths)
            traffic[(switch, chosen_path)] = np.random.randint(100, 500)
    
    return traffic


class MADQNTrainer:
    """Trainer for Multi-Agent DQN"""
    
    def __init__(self, num_agents=4, num_paths=3, episodes=100, batch_size=32,
                 max_steps_per_episode=1000, train_frequency=1):
        """
        Initialize trainer
        
        Args:
            num_agents: Number of agents
            num_paths: Number of paths per agent
            episodes: Number of training episodes
            batch_size: Batch size for training
            max_steps_per_episode: Max environment steps per episode
            train_frequency: Train every N environment steps
        """
        self.num_agents = num_agents
        self.num_paths = num_paths
        self.episodes = episodes
        self.batch_size = batch_size
        self.max_steps_per_episode = max_steps_per_episode
        self.train_frequency = max(1, train_frequency)
        
        # Initialize multi-agent system
        self.madqn = MultiAgentDQN(num_agents, state_size=4, action_size=num_paths)
        
        # Initialize environment
        self.env = NetworkEnvironment(num_switches=num_agents, num_paths_per_switch=num_paths)
        
        # Training history
        self.episode_rewards = []
        self.episode_metrics = []
        self.training_losses = []
    
    def train_episode(self, episode, update_interval=5):
        """Train for one episode"""
        states = self.env.reset()
        episode_reward = 0
        episode_loss = 0
        
        for step in range(self.max_steps_per_episode):
            # Get actions from all agents
            actions = []
            for agent_id in range(self.num_agents):
                action = self.madqn.act(agent_id, states[agent_id])
                actions.append(action)
            
            # Generate traffic
            traffic = generate_traffic(self.num_agents, self.num_paths)
            
            # Execute step
            next_states, rewards, done = self.env.step(actions, traffic)
            
            # Store experiences and train
            for agent_id in range(self.num_agents):
                self.madqn.remember(agent_id, states[agent_id], actions[agent_id],
                                   rewards[agent_id], next_states[agent_id], done)
            
            # Train all agents at a configurable frequency to reduce runtime.
            if (step + 1) % self.train_frequency == 0:
                loss = self.madqn.replay(self.batch_size)
                episode_loss += loss if isinstance(loss, (int, float)) else 0
            
            # Update state and accumulate reward
            states = next_states
            episode_reward += np.mean(rewards)
            
            if done:
                break
        
        # Update target networks
        if (episode + 1) % update_interval == 0:
            self.madqn.update_target_networks()
        
        # Record metrics
        metrics = self.env.get_metrics()
        self.episode_rewards.append(episode_reward)
        self.episode_metrics.append(metrics)
        self.training_losses.append(episode_loss)
        
        return episode_reward, metrics
    
    def train(self, verbose=True):
        """Train for all episodes"""
        for episode in range(self.episodes):
            reward, metrics = self.train_episode(episode)
            
            if verbose and (episode + 1) % 10 == 0:
                print(f"Episode {episode + 1}/{self.episodes}")
                print(f"  Reward: {reward:.2f}")
                print(f"  Throughput: {metrics['throughput']:.2f}%")
                print(f"  Retransmit Rate: {metrics['retransmit_rate']:.2f}%")
                print(f"  Avg RTT: {metrics['avg_rtt']:.2f}ms")
                print()
    
    def save_models(self, directory):
        """Save trained models"""
        os.makedirs(directory, exist_ok=True)
        self.madqn.save_all_agents(directory)
    
    def save_training_history(self, filepath):
        """Save training history"""
        history = {
            'episode_rewards': self.episode_rewards,
            'episode_metrics': self.episode_metrics,
            'training_losses': self.training_losses
        }
        save_metrics(history, filepath)


def main():
    """Main training function"""
    print("Initializing MADQN Trainer...")
    trainer = MADQNTrainer(num_agents=4, num_paths=3, episodes=100, batch_size=32)
    
    print("Starting training...")
    trainer.train()
    
    # Save models and history
    print("\nSaving models and training history...")
    trainer.save_models('./models/madqn')
    trainer.save_training_history('./results/training_history.json')
    
    print("Training completed!")


if __name__ == "__main__":
    main()
