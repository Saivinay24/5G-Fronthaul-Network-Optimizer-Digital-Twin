# O-RAN Fronthaul Digital Twin Interface

A research-grade digital twin viewer for deterministic network simulation of O-RAN fronthaul optimization.

## Quick Start

### 1. Generate Data

```bash
cd /Users/saivinay/Desktop/5G-Fronthaul-Optimizer
python src/export_digital_twin_data.py
```

This runs the full 6-layer analysis and exports `results/digital_twin_data.json` (≈12.5 MB).

### 2. Open Interface

```bash
open digital_twin.html
```

Or navigate to: `file:///Users/saivinay/Desktop/5G-Fronthaul-Optimizer/digital_twin.html`

## Interface Components

### 🔍 3-Stage Topology Discovery
- **Stage A (Observation):** Timeline view of packet loss events per cell.
- **Stage B (Correlation):** Force-directed clustering of synchronized cells.
- **Stage C (Inference):** Final topology drawing with confidence score.
- *Goal:* visually explain *how* the topology is learned from telemetry.

### ⚛️ Digital Twin Physics Engine (New)
- **Particle System:** Traffic represented as moving particles.
- **Baseline Physics:** Particles drop (turn red) when exceeding capacity.
- **Optimized Physics:** Particles enter a visual "Buffer Tank" and drain at controlled rates.
- *Goal:* visually explain *why* optimization works (buffering vs dropping).

### 🔬 Link Physics & Metrics
- **Capacity Meter:** Real-time utilization
- **Buffer Tank:** Physical tank with fill/drain animation
- **Packet Loss Counter:** Total events and loss rate
- **Rate Trace:** Last 100 slots with PAPR metrics

### ⏱️ Time Control
- Slot-based timeline (1 slot ≈ 500 µs)
- Play/pause/rewind/fast-forward
- Playback speed: 0.5x - 10x
- Jump to loss events
- Scrubbable timeline with progress indicator

### 💡 Operator Decision
- Risk level assessment (NONE → CRITICAL)
- Actionable recommendations
- Deployment summary (Enable/Conditional/Upgrade)
- Confidence scores and rationale

## Design Philosophy

**This is NOT a dashboard.** It's a live digital twin viewer for a deterministic network simulator.

### NOC-Style Aesthetics
- Dark theme (#0a0e1a base)
- High-contrast alerts (red/orange/green)
- Technical typography (Inter + JetBrains Mono)
- Grid background for lab/NOC feel
- No decorative elements—everything is functional

### Key Principles
✅ Network physics are visible  
✅ Topology emerges from data  
✅ Time-domain causality is proven  
✅ Everything is explainable and inspectable  
✅ Operator-grade decisions  

## Files

- **digital_twin.html** - Main interface structure
- **digital_twin.css** - NOC-style dark theme
- **digital_twin.js** - Interactive visualization engine
- **src/export_digital_twin_data.py** - Data export layer

## Data Structure

The interface loads `results/digital_twin_data.json` with:

```json
{
  "metadata": { ... },
  "topology": {
    "links": [...],
    "correlation_matrix": [...],
    "confidence_timeline": [...]
  },
  "telemetry": {
    "slot_data": {...},
    "burst_stats": {...},
    "loss_events": [...]
  },
  "optimization": {
    "1": {
      "baseline": {...},
      "optimized": {...},
      "buffer_timeline": [...]
    }
  },
  "decisions": {
    "per_link": {...},
    "risk_summary": {...}
  }
}
```

## Technical Details

### Performance
- Data sampling: Every 10th slot for traffic timelines
- Canvas rendering: Efficient 2D context operations
- Timeline limiting: First 200 buffer states
- Loss events: Capped at 100 events

### Algorithms
- **Topology Discovery:** Correlation-based clustering (threshold: 0.70)
- **Buffer Simulation:** Leaky bucket with time-domain precision
- **Time Control:** Slot-based indexing with synchronized rendering

## Browser Compatibility

Tested on:
- Chrome/Edge (recommended)
- Firefox
- Safari

Requires:
- Canvas 2D support
- ES6+ JavaScript
- Fetch API

## Troubleshooting

### Data Not Loading
```bash
# Regenerate data
python src/export_digital_twin_data.py

# Check file exists
ls -lh results/digital_twin_data.json
```

### Console Errors
- Open browser console (F12 or Cmd+Option+I)
- Check for CORS errors (use local file:// or serve via HTTP)
- Verify JSON is valid: `python -m json.tool results/digital_twin_data.json > /dev/null`

## Key Insights

> **"This system learns the network, simulates its physics, and proves optimization through replay — not assumptions."**

The interface demonstrates:
1. **Blind Topology Discovery:** Network wiring inferred from packet loss correlation
2. **Time-Domain Optimization:** Buffer absorbs bursts without increasing capacity
3. **Deterministic Intelligence:** Explainable algorithms, not ML black boxes
4. **Operator-Grade Decisions:** Clear recommendations with confidence scores

## Target Audience

This interface is designed for:
- ✅ Telecom standards engineers
- ✅ Systems researchers
- ✅ Network architects
- ✅ Network operators

It demonstrates that fronthaul optimization can be achieved through **time-domain shaping** (143 µs buffer) instead of **space-domain upgrades** (expensive fiber), reducing required capacity by **85-90%**.

---

**Built with:** Vanilla JavaScript, Canvas 2D, Python (data export)  
**No frameworks:** Pure HTML/CSS/JS for maximum transparency and control
