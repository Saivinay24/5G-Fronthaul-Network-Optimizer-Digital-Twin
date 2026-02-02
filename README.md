# 5G Fronthaul Network Optimizer

**Production-grade O-RAN fronthaul optimization engine with six-layer architecture**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

This system implements an intelligent, deterministic optimization solution for 5G Open RAN fronthaul networks. By analyzing symbol-level telemetry and applying adaptive traffic shaping, it reduces required link capacity by up to **88.5%** without hardware upgrades.

### Key Features

- **Dual-Mode Topology Discovery**: Both 3-link compliance (hierarchical clustering) AND 12-link high-resolution (Pearson correlation)
- **Six-Layer Architecture**: Modular design from telemetry to operator decisions
- **Adaptive Traffic Shaping**: PAPR-based intelligent smoothing (70-200 µs buffers)
- **Deterministic Intelligence**: NO machine learning - explainable, safety-critical algorithms
- **Failure Mode Detection**: Identifies and mitigates 3 critical failure scenarios
- **Operator-Centric**: Human-readable recommendations with clear action plans
- **Sustainability Metrics**: Quantifies cost, energy, and carbon impact
- **What-If Simulator**: Interactive CLI tool for parameter exploration
- **Scalable**: O(N log R) complexity, proven from 24 → 2400 cells
- **Digital Twin Physics**: Particle-based causal simulation (explains *why* it works)
- **AI-Powered Explanations**: Natural language insights for operator decisions


## Quick Start - Run the Dashboards

**Get started in 3 steps** - See the final product immediately:

### Step 1: Setup Environment
```bash
# Clone repository
git clone https://github.com/Saivinay24/5G-Fronthaul-Network-Optimizer-Digital-Twin.git
cd 5G-Fronthaul-Network-Optimizer-Digital-Twin

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pandas numpy matplotlib seaborn jupyter
```

### Step 2: Generate Results & Digital Twin Data
```bash
# Run full analysis (generates operator summary and visualizations)
python src/main_v2.py --data-folder data

# Generate digital twin simulation data
python src/export_digital_twin_data.py
```

### Step 3: Launch Dashboards
```bash
# Start the web server
python src/server.py

# Open in your browser:
# - Operator Summary: http://localhost:8000/results/OPERATOR_SUMMARY.html
# - Analytics Dashboard: http://localhost:8000/dashboard.html
# - Digital Twin: http://localhost:8000/digital_twin.html
# - Test Simulator: http://localhost:8000/test_simulator.html
```

**That's it!** You now have access to all four interactive dashboards showing:
- 88.5% capacity reduction results
- Physics-based network simulation
- Interactive failure mode testing
- Complete operator recommendations

---

## Demo & Visualization

### Interactive Demo
Explore the complete solution through our interactive Jupyter notebook:

```bash
jupyter notebook demo_presentation.ipynb
```

### Generate All Visualizations
Create publication-quality visualizations for all 5 demo sections:

```bash
python src/generate_demo.py --data-folder data --output results/demo
```

**Output includes:**
- Section 1: Micro-burst problem visualization
- Section 2: Topology discovery (correlation analysis)
- Section 3: Before/After capacity comparison (88% reduction)
- Section 4: Operator decision dashboard
- Section 5: Robustness and what-if analysis
- Complete demo flow guide and presentation script

### 5-Section Demo Flow (2-3 minutes)

1. **The Problem** — Micro-bursts cause congestion (not sustained traffic)
2. **Topology Discovery** — Correlation reveals network structure
3. **Capacity Optimization** — 88% reduction with software shaping
4. **Operator Decision** — Clear actionable recommendations
5. **Robustness** — Safe, tunable, production-ready

See [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for complete presentation guide.

## Challenge Solutions

This project addresses two core challenges in 5G Open RAN fronthaul optimization:

### Challenge 1: Network Topology Identification
**Blind topology discovery using statistical correlation**

- **Dual-Mode Discovery**: Both 3-link compliance (hierarchical clustering) AND 12-link high-resolution (Pearson correlation)
- **Sliding Window Burst Detection**: Sub-slot micro-burst identification (~143 µs windows)
- **SRLG Analysis**: Shared Risk Link Groups identified through correlated packet loss
- **3-Stage Visualization**: Observation → Correlation → Inference

See [challenge-1-solution.md](challenge-1-solution.md) for detailed technical implementation.

### Challenge 2: Link Capacity Estimation & Optimization
**Time-domain optimization replacing space-domain upgrades**

- **Adaptive Traffic Shaping**: PAPR-based intelligent buffering (70-200 µs)
- **Leaky Bucket Simulation**: Bit-exact physics modeling at symbol level
- **Binary Search Optimization**: Finding optimal capacity with 0.1 Gbps precision
- **88.5% Capacity Reduction**: From 32.31 Gbps → 3.71 Gbps (Link 2)

See [challenge-2-solution.md](challenge-2-solution.md) for detailed technical implementation.

**Key Innovation**: Shifting from **Space Domain** (expensive hardware upgrades) to **Time Domain** (intelligent buffering) achieves 85-90% capacity reduction without service degradation.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 6: Simulation & Scaling                          │
│  What-if simulator, Multi-site scaling (O(N log R))     │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Impact & Sustainability                       │
│  Cost savings, Energy impact, Carbon footprint          │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Operator Decision                             │
│  Human-readable recommendations, Action plans           │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Control & Resilience                          │
│  Failure mode detection, Mitigation strategies          │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Deterministic Intelligence                    │
│  Adaptive shaping, Leaky bucket, Binary search          │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Telemetry & Analysis                          │
│  Slot aggregation, Burst detection, Topology mapping    │
└─────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Usage

### Full Six-Layer Analysis
```bash
python src/main_v2.py --data-folder data
```

**Output includes**:
- Network topology discovery
- Adaptive shaping recommendations
- Failure mode analysis
- Operator decisions (upgrade/no-upgrade)
- Sustainability impact (cost/energy/CO₂)
- Scaling analysis

### What-If Simulation
```bash
python src/cli_simulator.py --link 2 --buffer 143 --rate 5 --loss-limit 0.01
```

**Parameters**:
- `--link`: Link ID to simulate
- `--buffer`: Buffer size in microseconds (70-200)
- `--rate`: Link capacity in Gbps
- `--loss-limit`: Maximum packet loss (0.005-0.02)

## AI Explanation Mode

The system includes a dual-mode explanation engine:
- **Template Mode**: Deterministic, pre-written explanations (Default)
- **AI Mode**: Generative AI insights using Gemini API

See [README_AI_MODE.md](README_AI_MODE.md) for setup and usage.

## Results

### Capacity Optimization
- **Link 2**: 32.31 Gbps → 3.71 Gbps (**88.5% reduction**)
- **Link 5**: 32.14 Gbps → 3.14 Gbps (**90.2% reduction**)
- **Network-wide**: Avoided $30K+ in hardware upgrades

### Sustainability Impact
- **Energy Savings**: ~90 kWh/year per link
- **Carbon Reduction**: ~390 kg CO₂e/year network-wide
- **CAPEX Avoidance**: 40G → 25G optic upgrades eliminated

## Four Dashboards for Different Audiences

The system provides four distinct interfaces, each optimized for different user personas:

### 1. Operator Summary Dashboard
**Target Audience**: Network operators and decision-makers  
**Access**: `results/OPERATOR_SUMMARY.html`

**Features**:
- Executive summary with clear upgrade/no-upgrade decisions
- Per-link capacity recommendations
- Cost savings and sustainability metrics
- Risk assessment and mitigation strategies
- Human-readable, no technical jargon

**Generate**:
```bash
python src/quick_summary.py --data-folder data
```

### 2. Analytics Dashboard
**Target Audience**: Network engineers and analysts  
**Access**: `dashboard.html` (run with `python src/server.py`)

**Features**:
- Interactive visualizations (Matplotlib-based)
- Traffic pattern analysis with PAPR metrics
- Topology correlation heatmaps
- Before/after capacity comparisons
- Detailed technical metrics and statistics
- AI-powered insights and explanations

**Launch**:
```bash
python src/server.py
# Open http://localhost:8000/dashboard.html
```

### 3. Digital Twin Interface
**Target Audience**: Researchers and technical stakeholders  
**Access**: `digital_twin.html`, `digital_twin_demo.html`, or `topology_3d.html`

**Features**:
- **Physics-Based Particle Simulation**: Traffic visualized as moving particles
- **3-Stage Topology Discovery**: Observation → Correlation → Inference visualization
- **Real-Time Traffic Flow**: Symbol-level (35.7 µs) animation
- **Synchronized Comparison**: Baseline vs. optimized networks side-by-side
- **Buffer Tank Visualization**: Physical representation of traffic shaping
- **Frame-by-Frame Replay**: Scrub through burst events with timeline control
- **Causal Explanation**: Visual proof of why buffering prevents packet loss
- **3D Network Topology**: Interactive city-like layout (topology_3d.html)

**Launch**:
```bash
# Generate digital twin data first
python src/export_digital_twin_data.py

# Then serve the interface
python src/server.py
# Open http://localhost:8000/digital_twin.html
# Or http://localhost:8000/digital_twin_demo.html
# Or http://localhost:8000/topology_3d.html
```

**See [DIGITAL_TWIN_README.md](DIGITAL_TWIN_README.md) for detailed documentation.**

### 4. Test Simulator (What-If Analysis)
**Target Audience**: Network engineers and QA teams  
**Access**: `test_simulator.html`

**Features**:
- **Interactive Failure Mode Testing**: Run simulations for URLLC, synchronized bursts, and buffer misconfiguration
- **Real-Time Risk Assessment**: Instant detection results with confidence scores
- **Impact Analysis**: Packet loss, latency, and buffer utilization metrics
- **Mitigation Recommendations**: Actionable guidance for each failure scenario
- **Traffic Pattern Visualization**: Canvas-based charts showing burst patterns

**Launch**:
```bash
python src/server.py
# Open http://localhost:8000/test_simulator.html
```

**Test Cases Available**:
- URLLC Traffic Detection (latency budget violations)
- Synchronized Burst Detection (correlated cell bursts)
- Buffer Misconfiguration Detection (oversized/undersized buffers)


## Digital Twin Interface

The project includes **three physics-based digital twin interfaces** that visualize network behavior in real-time:

### 1. Main Digital Twin (`digital_twin.html`)
Production-grade physics simulation with complete feature set:
- **3-Stage Topology Discovery**: Visual progression from raw telemetry → correlation analysis → final topology
- **Particle-Based Physics Engine**: Traffic represented as moving particles showing buffering vs. dropping
- **Dual Network Simulation**: Side-by-side baseline (packet loss) vs. optimized (buffering) comparison
- **Time Control**: Play/pause/rewind with adjustable speed (0.5x - 10x)
- **Buffer Tank Visualization**: Physical tank showing fill/drain dynamics
- **Loss Event Timeline**: Jump to specific congestion events

### 2. Demo Interface (`digital_twin_demo.html`)
Streamlined version optimized for presentations and quick demonstrations.

### 3. 3D Topology Viewer (`topology_3d.html`)
Interactive 3D network topology with city-like layout visualization.

### Live Development Server
For enhanced development experience, a Vite-based dev server is available:
```bash
cd digital-twin-ui
npm run dev
```

**See [DIGITAL_TWIN_README.md](DIGITAL_TWIN_README.md) for complete documentation, data generation, and troubleshooting.**


## Why Deterministic (Not ML)?

This system uses **deterministic algorithms** instead of machine learning for six critical reasons:

1. **Safety-Critical**: Fronthaul requires verifiable, predictable decisions
2. **Explainability**: Operators must understand WHY decisions are made
3. **Guarantees**: Mathematical proof of packet loss ≤ 1%
4. **Regulatory**: Auditable for telecom compliance
5. **Simplicity**: No GPU, model versioning, or retraining
6. **Real-Time**: Predictable O(N) latency

See [intelligence.py](src/layers/intelligence.py) for detailed rationale.

## Documentation

### Core Documentation
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design and layer descriptions
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Operator deployment guide
- **[DEMO_GUIDE.md](docs/DEMO_GUIDE.md)**: Complete presentation guide (2-3 min demo)
- **[ROBUSTNESS.md](docs/ROBUSTNESS.md)**: Failure scenarios and safety guarantees
- **[PROJECT_DETAILS.md](PROJECT_DETAILS.md)**: Technical deep-dive and innovation summary

### Challenge Solutions
- **[challenge-1-solution.md](challenge-1-solution.md)**: Network topology identification (blind discovery)
- **[challenge-2-solution.md](challenge-2-solution.md)**: Link capacity estimation & optimization

### Interface Documentation
- **[DIGITAL_TWIN_README.md](DIGITAL_TWIN_README.md)**: Digital twin interface guide
- **[README_AI_MODE.md](README_AI_MODE.md)**: AI explanation mode setup and usage

## Operator Tools

### Quick Summary Report
Generate operator-facing summary in <30 seconds:
```bash
python src/quick_summary.py --data-folder data
```

Output: `results/OPERATOR_SUMMARY.md` and `results/OPERATOR_SUMMARY.html`

### Full Analysis with Summary
Run complete six-layer analysis (includes operator summary):
```bash
python src/main_v2.py --data-folder data
```

Generates:
- Layer-by-layer analysis output
- Operator summary reports (Markdown + HTML)
- Sustainability impact metrics

## File Structure

```
├── src/
│   ├── layers/              # Six-layer implementation
│   │   ├── telemetry.py
│   │   ├── intelligence.py
│   │   ├── resilience.py
│   │   ├── operator_decision.py
│   │   ├── sustainability.py
│   │   └── simulation.py
│   ├── main_v2.py           # Production orchestrator
│   ├── main.py              # Legacy analyzer (for compatibility)
│   ├── cli_simulator.py     # What-if simulator CLI
│   ├── operator_summary.py  # Operator summary generator (MD/HTML)
│   ├── quick_summary.py     # Fast summary generation
│   ├── demo_visualizer.py   # Demo visualization engine
│   ├── generate_demo.py     # One-command demo generation
│   ├── generate_explanations.py  # Explanation generator
│   ├── visualize_comparison.py   # Before/after comparison plots
│   ├── ai_explainer.py      # Dual-mode explanation engine
│   ├── export_digital_twin_data.py  # Digital twin data exporter
│   ├── topology_3link.py    # 3-link compliance mode
│   └── utils/
│       └── constants.py     # Physical layer constants
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── DEMO_GUIDE.md        # Presentation guide
│   └── ROBUSTNESS.md        # Failure modes and safety
├── challenge-1-solution.md  # Topology discovery solution
├── challenge-2-solution.md  # Capacity optimization solution
├── DIGITAL_TWIN_README.md   # Digital twin documentation
├── README_AI_MODE.md        # AI explanation mode guide
├── PROJECT_DETAILS.md       # Technical deep-dive
├── demo_presentation.ipynb  # Interactive demo notebook
├── dashboard.html           # AI-powered analytics dashboard
├── digital_twin.html        # Main digital twin interface
├── digital_twin_demo.html   # Demo digital twin interface
├── topology_3d.html         # 3D topology viewer
├── test_simulator.html      # Interactive what-if simulator
├── digital-twin-ui/         # Vite dev server (optional)
└── results/
    ├── figures/             # Analysis visualizations
    ├── demo/                # Demo presentation materials
    ├── explanations/        # Generated operator narratives
    ├── digital_twin_data.json  # Digital twin simulation data
    └── OPERATOR_SUMMARY.html/md  # Operator reports
```

## Key Technologies

- **Python 3.8+**: Core language
- **NumPy/Pandas**: Vectorized telemetry processing
- **Matplotlib/Seaborn**: Visualization
- **Gnuplot**: High-precision time-series plotting

## Deployment

### Requirements
- Python 3.8+
- 4+ GB RAM (for 24-cell analysis)
- Symbol-level throughput logs
- Packet loss statistics

### Deployment Scenarios

**Scenario A: Enable Shaping** (Recommended)
- Configure shaping at DU/switch layer
- Set buffer from recommendation (e.g., 143 µs)
- Monitor packet loss < 1%

**Scenario B: Conditional Shaping** (High Risk)
- Deploy in monitoring mode first
- Address failure modes
- Gradual rollout with close monitoring

**Scenario C: Upgrade Required** (Critical Risk)
- Do NOT deploy shaping
- Plan link capacity upgrade
- Consider traffic segregation

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete guide.

## Scaling

### Complexity
- **Time**: O(N log R) - near-linear
- **Space**: O(N + C²) - dominated by symbol storage
- **Parallelization**: Embarrassingly parallel (cells independent)

### Multi-Site Performance
| Site Size | Cells | Symbols | Memory | Time |
|-----------|-------|---------|--------|------|
| Small     | 24    | 2.4M    | 40 MB  | 2.4 min |
| Medium    | 240   | 24M     | 400 MB | 24 min |
| Large     | 2400  | 240M    | 4 GB   | 240 min |

## Contributing

This is a production-grade system designed for telecom operators. Contributions should maintain:
- Deterministic algorithms (no ML)
- Operator-centric design
- Safety-critical standards
- Comprehensive documentation


## Contact

- **Repository**: [https://github.com/Saivinay24/5G-Fronthaul-Optimizer](https://github.com/Saivinay24/5G-Fronthaul-Optimizer)
- **Issues**: GitHub Issues
- **Documentation**: `docs/` directory

## Acknowledgments

Built for the 5G Open RAN fronthaul optimization challenge. Implements deterministic intelligence for safety-critical telecom infrastructure.

---

**Production-Grade O-RAN Fronthaul Optimizer v2.0** - Deterministic. Explainable. Deployable.
