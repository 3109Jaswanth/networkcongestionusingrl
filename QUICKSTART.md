# Quick Start Guide - MADQN 5G SDN Load Balancing

## Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd /home/gvp/Documents/RL_Project
pip install -r requirements.txt
```

### Step 2: Train MADQN Agents (5-10 minutes)
```bash
python main.py train --episodes 50
```

**What happens:**
- Initializes 4 DQN agents (one per switch)
- Trains on simulated 5G network traffic
- Saves trained models to `models/madqn/`
- Shows training progress every 10 episodes

**Example Output:**
```
Episode 10/50
  Reward: 45.23
  Throughput: 87.45%
  Retransmit Rate: 2.34%
  Avg RTT: 45.67ms

Episode 20/50
  ...
```

### Step 3: Run Simulations (Comparative Analysis)
```bash
python main.py simulate --traffic normal --steps 500
```

**What happens:**
- Compares RR, WRR, HAC+BPNN, and MADQN algorithms
- Runs each algorithm through 500 simulation steps
- Shows results comparison table
- Saves detailed results to `results/`

**Example Output:**
```
==============================================================
Simulation Results Comparison
==============================================================

Algorithm       Throughput      Retransmits     RTT
------
rr              82.34%          5.20%           52.10ms
wrr             85.12%          4.80%           48.30ms
hac_bpnn        87.20%          3.10%           45.70ms
madqn           91.45%          3.00%           31.50ms

MADQN improvement over HAC+BPNN: 4.84%
```

### Step 4: Run Complete Workflow
```bash
python main.py all --episodes 50
```

Trains MADQN then runs comparisons automatically.

---

## Common Tasks

### Train with Custom Settings
```bash
python main.py train \
  --episodes 100 \
  --batch_size 64 \
  --agents 8
```

### Test Different Traffic Patterns
```bash
python main.py simulate --traffic bursty
python main.py simulate --traffic video
python main.py simulate --traffic ddos
python main.py simulate --traffic mixed
```

### Check Saved Models
```bash
ls -la models/madqn/
```

### View Training History
```bash
cat results/training_history.json | python -m json.tool
```

---

## Project Navigation

```
RL_Project/
├── main.py                    ← Start here!
├── README.md                  ← Full documentation
├── requirements.txt           ← Install dependencies
│
├── madqn/
│   ├── train.py              ← Training script
│   ├── agent.py              ← DQN implementation
│   ├── environment.py        ← Network simulator
│   └── utils.py              ← Helper functions
│
├── sdn_controller/
│   ├── load_balancer.py      ← Algorithm implementations
│   ├── rr_app.py             ← Round Robin
│   ├── wrr_app.py            ← Weighted Round Robin
│   └── madqn_app.py          ← MADQN SDN app
│
├── simulation/
│   ├── run_simulation.py     ← Main simulator
│   ├── topology.py           ← Network topology
│   └── traffic_generator.py  ← Traffic patterns
│
└── results/                   ← Output files
```

---

## Understanding the Code

### 1. **What are the 4 algorithms?**
- **RR (Round Robin)**: Simple sequential distribution
- **WRR (Weighted Round Robin)**: Sequential with weights
- **HAC+BPNN**: Clustering + neural network (baseline)
- **MADQN**: Multi-agent deep Q-learning (proposed)

### 2. **How does MADQN work?**
```
Network State → DQN Agent → Routing Decision → Reward
     ↓              ↓              ↓              ↓
[queue,latency] [Neural Net] [which path?] [traffic metrics]

Agent learns to make better decisions through trial and error
```

### 3. **What metrics are tracked?**
- **Throughput**: % of packets successfully delivered
- **Retransmits**: % of packets lost (need retransmission)
- **RTT**: Average round-trip time in milliseconds

---

## Troubleshooting

### Error: "No module named 'tensorflow'"
```bash
pip install --upgrade tensorflow
```

### Error: "CUDA out of memory"
Reduce batch size:
```bash
python main.py train --batch_size 16
```

### Error: "Port already in use" (when using SDN)
Change port:
```bash
python -c "import sys; sys.argv=['', '--wsapi-port', '8081']; ..."
```

### Slow Training?
Use fewer episodes or smaller network:
```bash
python main.py train --episodes 20  # Reduced from 50
```

---

## Next Steps

1. **Understand the Results**: Why does MADQN perform better?
   - Read the comparison table output
   - Check the improvement percentage

2. **Experiment with Settings**:
   - Try different numbers of agents
   - Test with different traffic patterns
   - Adjust learning rate and batch size

3. **Extend the Project**:
   - Add more network topology types
   - Implement custom traffic patterns
   - Deploy with real SDN controller (Ryu)

4. **Research & Analysis**:
   - Generate plots of training convergence
   - Analyze agent decision making
   - Study impact of network size

---

## Key Concepts to Know

### Multi-Agent Learning
Instead of one agent controlling everything, each switch has its own agent that learns independently. They coordinate through network effects.

### Deep Q-Network (DQN)
Machine learning algorithm that learns to make routing decisions by:
1. Observing network state
2. Taking an action (routing decision)
3. Receiving reward (based on network performance)
4. Adjusting strategy to maximize rewards

### Reinforcement Learning Loop
```
State → Action → Reward → Learn → Better Action
  ↑                                    ↓
  └────────────────────────────────────┘
```

---

## Performance Expectations

| Metric | Time | Accuracy |
|--------|------|----------|
| Train 50 episodes (4 agents) | 2-5 min | ~85% throughput |
| Train 100 episodes | 5-10 min | ~92% throughput |
| Simulation (500 steps) | 1-2 min | Comparative results |
| Full workflow | 10-15 min | Complete analysis |

---

## File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | Command-line interface for all operations |
| `train.py` | MADQN training logic |
| `agent.py` | DQN and multi-agent implementation |
| `environment.py` | Network simulation |
| `load_balancer.py` | RR, WRR, HAC+BPNN algorithms |
| `run_simulation.py` | Comparative evaluation |

---

## Tips for Success

✅ **Do:**
- Start with fewer episodes to test setup
- Save results regularly
- Document your experiments
- Experiment with different traffic patterns

❌ **Don't:**
- Run very long training without checkpoints
- Use GPU memory excessively
- Skip understanding the metrics
- Override default hyperparameters without reason

---

## Getting Help

1. **Check README.md** - Full documentation and API details
2. **Review code comments** - Each module is well-commented  
3. **Look at examples** - Check train.py for usage patterns
4. **Run with --help** - Each command shows available options:
   ```bash
   python main.py train --help
   python main.py simulate --help
   ```

---

## What to Try Next

### Beginner:
```bash
# Train for 20 episodes
python main.py train --episodes 20

# Run quick simulation
python main.py simulate --steps 200
```

### Intermediate:
```bash
# Train with more agents
python main.py train --episodes 100 --agents 8

# Test different traffic
python main.py simulate --traffic bursty
python main.py simulate --traffic video
```

### Advanced:
```bash
# Full workflow with custom settings
python main.py all --episodes 100

# Modify madqn/agent.py to change:
# - learning_rate
# - gamma (discount factor)  
# - network architecture
```

---

Happy Learning! 🚀

For detailed information, see README.md
For API details, check docstrings in Python files
For experiments, modify main.py or individual modules
