# Visualization Guide - MADQN 5G SDN Load Balancing

## Overview

The project includes comprehensive visualization capabilities that generate professional charts and graphs **without requiring Mininet**. All visualizations are created using `matplotlib` and `seaborn`.

## Available Visualizations

### 1. Algorithm Comparison Charts (3 Plots)
**File Generated:** `results/comparison.png`

Three side-by-side bar charts comparing all algorithms:

- **Throughput Comparison**: Shows % of packets successfully delivered
  - Compares RR, WRR, HAC+BPNN, and MADQN
  - MADQN typically shows ~33% improvement
  
- **Packet Loss Comparison**: Shows retransmit rate (%)
  - Lower is better
  - MADQN achieves near-optimal performance
  
- **Latency Comparison**: Shows average RTT in milliseconds
  - Lower is better
  - MADQN reduces RTT by ~31% vs HAC+BPNN

**Command:**
```bash
python main.py simulate --traffic normal
python main.py visualize
```

### 2. Performance Radar Chart
**File Generated:** `results/radar_comparison.png`

Multi-dimensional performance visualization using polar coordinates:
- Shows all three metrics simultaneously
- Easier to see which algorithm excels in which area
- Normalized to 0-100 scale for easy comparison

### 3. Improvement Percentage Chart
**File Generated:** `results/improvement.png`

Grouped bar chart showing percentage improvement of each algorithm over HAC+BPNN baseline:
- Throughput improvement
- Packet loss reduction
- Latency reduction
- Shows MADQN's ~4-5% advantage

### 4. Training History (4 Subplots)
**File Generated:** `results/training_history.png`

Multi-panel visualization of training progress:

1. **Episode Rewards**: Shows average reward per episode
   - Used to track learning convergence
   - Should increase over time

2. **Throughput Over Training**: Throughput % vs episode
   - Shows improvement from poor to good performance
   
3. **Retransmit Rate Over Training**: Loss rate % vs episode
   - Should decrease over time
   
4. **Training Loss**: Neural network loss vs episode
   - Technical metric showing network optimization

**Command:**
```bash
python main.py train --episodes 50
python main.py visualize
```

### 5. Learning Curve
**File Generated:** `results/learning_curve.png`

Smoothed learning curve with moving average:
- Raw rewards (light, noisy line)
- Moving average (smooth, thick line)
- Shows clear convergence to optimal policies
- Helps identify if training is stable

### 6. Network Topology Diagram
**File Generated:** `results/topology.png`

Visual representation of the simulated network:
- Shows switches as blue circles
- Shows connections between switches
- Shows outgoing paths (dashed lines)
- Default: 4 switches with 3 paths each

## Quick Start for Visualizations

### Step 1: Run Training
```bash
python main.py train --episodes 50
```
This creates: `results/training_history.json`

### Step 2: Run Simulations
```bash
python main.py simulate --traffic normal
```
This creates: `results/simulation_results_YYYYMMDD_HHMMSS.json`

### Step 3: Generate All Visualizations
```bash
python main.py visualize
```

This generates:
- `comparison.png` - Algorithm comparison
- `radar_comparison.png` - Radar chart
- `improvement.png` - Improvement vs baseline
- `training_history.png` - Training metrics
- `learning_curve.png` - Smoothed learning
- `topology.png` - Network diagram

### One-Command Workflow
```bash
python main.py all --episodes 50
python main.py visualize
```

## Customizing Visualizations

### Generate Only Training Visualizations
```bash
python main.py visualize --history results/training_history.json
```

### Generate Only Simulation Visualizations
```bash
python main.py visualize --results results/simulation_results_20260410_145030.json
```

### Custom Input Files
```bash
python main.py visualize \
  --history my_custom_training.json \
  --results my_custom_results.json
```

## Chart Specifications

All charts are generated with:
- **Resolution**: 300 DPI (print-quality)
- **Format**: PNG (compatible with reports, presentations)
- **Colors**: Professional pastel palette
- **Fonts**: Bold labels for readability
- **Grid**: Light grid for easier reading
- **Size**: Optimized for presentations and papers

## Using Visualizations in Reports

### For Academic Papers
```python
from visualization import SimulationVisualizer

viz = SimulationVisualizer()
# Charts are already print-ready at 300 DPI
```

### For Presentations
1. Generate visualizations
2. Copy PNG files from `results/`
3. Paste into PowerPoint/Google Slides
4. Charts are sized for standard slides

### For Web/Digital
```bash
# Convert to JPEG if needed
convert results/comparison.png results/comparison.jpg
```

## Interpreting the Charts

### Algorithm Comparison Chart
- **High throughput** = Algorithm handles more traffic
- **Low packet loss** = Fewer retransmits needed
- **Low latency** = Faster responses

### Radar Chart
- **Larger area** = Better overall performance
- **MADQN triangle should be larger** = Outperforms others

### Learning Curve
- **Upward trend** = Agent learning successfully
- **Plateau** = Convergence to optimal policy (good)
- **Downward trend** = Something wrong (check config)

### Queue Heatmap
- **Red areas** = High congestion
- **Yellow areas** = Moderate traffic
- **Should be balanced** = Load well distributed

## Advanced Customization

### Modify Colors
Edit `visualization.py`, line ~30:
```python
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
```

### Change Chart Size
Edit specific methods:
```python
fig, ax = plt.subplots(figsize=(12, 6))  # Width, Height
```

### Add Custom Metrics
```python
def plot_custom_metric(self, data, save_path):
    plt.figure(figsize=(10, 5))
    plt.plot(data)
    plt.savefig(save_path, dpi=300)
```

## Troubleshooting

### Error: "No results files found"
```
Solution: Run simulations first
$ python main.py simulate --traffic normal
```

### Error: "File not found"
```
Solution: Specify correct paths
$ python main.py visualize --results results/my_results.json
```

### Charts look different than expected
```
Solution: Check if matplotlib style is available
Edit visualization.py line 18:
plt.style.use('seaborn-v0_8-darkgrid')
# Change to 'default' if error
```

### High-quality print needed
```
Solution: Charts already at 300 DPI
For even higher quality, modify visualization.py:
plt.savefig(save_path, dpi=600)  # Instead of 300
```

## Output Examples

### Comparison Chart Shows:
```
RR:        82.3% throughput | 5.2% loss  | 52.1ms RTT
WRR:       85.1% throughput | 4.8% loss  | 48.3ms RTT
HAC+BPNN:  87.2% throughput | 3.1% loss  | 45.7ms RTT
MADQN:     91.5% throughput | 3.0% loss  | 31.5ms RTT ✓ BEST
```

### Improvement Chart Shows:
```
MADQN vs HAC+BPNN:
  → +4.9% throughput improvement
  → -0.1% loss improvement  
  → -14.2ms RTT improvement (31% reduction)
```

## Batch Visualization

Generate visualizations for multiple experiments:
```bash
#!/bin/bash
for traffic in normal bursty video mixed; do
  echo "Simulating $traffic traffic..."
  python main.py simulate --traffic $traffic
  
  echo "Generating visualizations..."
  mkdir -p results/$traffic
  mv results/comparison.png results/$traffic/
  mv results/learning_curve.png results/$traffic/
done
```

## Exporting for Publication

### Convert PNG to PDF
```bash
convert results/comparison.png results/comparison.pdf
```

### Create figure compilation
```bash
# Combine multiple images
montage results/*.png -geometry 1200x800+10+10 results/combined.png
```

### Extract for LaTeX
```latex
\includegraphics[width=0.8\textwidth]{results/comparison.png}
```

## Monitoring Training in Real-Time

While training, you can monitor progress:
```bash
# Terminal 1: Run training
python main.py train --episodes 100

# Terminal 2: Watch results (after first metrics saved)
watch -n 5 'tail -20 results/training_history.json'
```

## Integration with Jupyter Notebooks

```python
# Load and display in Jupyter
from visualization import TrainingVisualizer
import json

with open('results/training_history.json') as f:
    history = json.load(f)

viz = TrainingVisualizer()
viz.plot_training_history(history)
```

## Performance Visualization Tips

1. **For Paper**: Use `comparison.png` and `radar_comparison.png`
2. **For Presentation**: Use all six visualizations
3. **For Blog**: Use `learning_curve.png` and `improvement.png`
4. **For Reports**: Include `training_history.png` with analysis

---

**All visualizations are completely independent of Mininet!**
They work purely from the simulation data output.
