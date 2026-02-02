# Deployment Guide - Production O-RAN Fronthaul Optimizer

## Pre-Deployment Checklist

### System Requirements
- Python 3.8+
- NumPy, Pandas, Matplotlib, Seaborn
- 4+ GB RAM (for 24-cell analysis)
- CPU: Any modern x86 processor

### Data Requirements
- Symbol-level throughput logs (`cell_X_throughput.dat`)
- Packet loss statistics (`cell_X_pkt_stats.dat`)
- Minimum 100K symbols per cell for statistical significance

## Deployment Steps

### 1. Installation
```bash
# Clone repository
git clone https://github.com/Saivinay24/5G-Fronthaul-Optimizer.git
cd 5G-Fronthaul-Optimizer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pandas numpy matplotlib seaborn
```

### 2. Data Preparation
```bash
# Place telemetry files in data/ directory
mkdir -p data
# Copy cell_X_throughput.dat and cell_X_pkt_stats.dat files
```

### 3. Initial Analysis
```bash
# Run full six-layer analysis
python src/main_v2.py --data-folder data
```

**Expected Output**:
- Topology discovery results
- Adaptive shaping recommendations
- Failure mode analysis
- Operator decisions
- Sustainability impact
- Scaling analysis

### 3b. Visualize Results
```bash
# Open Digital Twin interface
open digital_twin.html
```
- Verify topology matches physical network
- Observe baseline vs optimized physics


### 4. Interpret Results

#### Operator Recommendations
Look for recommendations in the format:
```
LINK X ANALYSIS & RECOMMENDATION
├─ Current Peak Load: XX.XX Gbps
├─ Optimal Capacity: XX.XX Gbps
└─ RECOMMENDATION: ✅ DO NOT upgrade / ⚠️ UPGRADE REQUIRED
```

#### Risk Levels
- **NONE/LOW**: Safe to deploy shaping
- **MEDIUM**: Deploy with monitoring
- **HIGH**: Address failure modes first
- **CRITICAL**: Do not deploy shaping, upgrade required

### 5. What-If Exploration
```bash
# Test different configurations
python src/cli_simulator.py --link 2 --buffer 143 --rate 5 --loss-limit 0.01
```

Vary parameters to find optimal configuration:
- `--buffer`: 70-200 µs
- `--rate`: Link capacity in Gbps
- `--loss-limit`: 0.005-0.02 (0.5%-2%)

## Deployment Scenarios

### Scenario A: Enable Shaping (Recommended)
**When**: Recommendation is "✅ DO NOT upgrade"

**Steps**:
1. Configure shaping at DU/switch software layer
2. Set buffer depth from recommendation (e.g., 143 µs)
3. Set shaping mode (MINIMAL/MODERATE/AGGRESSIVE)
4. Enable monitoring for packet loss
5. Validate QoS metrics

**Monitoring**:
- Packet loss should remain < 1%
- Buffer occupancy should be < 95%
- Latency should be within budget

### Scenario B: Conditional Shaping (High Risk)
**When**: Risk level is HIGH

**Steps**:
1. Deploy in monitoring mode first (no active shaping)
2. Address failure modes from resilience analysis
3. Gradually enable shaping with conservative buffer
4. Monitor closely for 24-48 hours
5. Prepare upgrade plan as fallback

### Scenario C: Upgrade Required (Critical Risk)
**When**: Risk level is CRITICAL or URLLC detected

**Steps**:
1. Do NOT deploy shaping
2. Plan link capacity upgrade
3. Consider traffic segregation (URLLC vs eMBB)
4. Re-run analysis after upgrade

## Configuration Parameters

### Buffer Sizing
- **Minimum**: 70 µs (low latency, high risk)
- **Standard**: 143 µs (balanced)
- **Maximum**: 200 µs (high burstiness)

**Rule of Thumb**: Use recommended buffer from analysis.

### Shaping Modes
- **MINIMAL**: PAPR < 10x, light traffic
- **MODERATE**: PAPR 10-100x, typical 5G
- **AGGRESSIVE**: PAPR > 100x, bursty traffic

**Rule of Thumb**: System auto-selects based on PAPR.

### Loss Limits
- **Standard**: 1% (default)
- **Strict**: 0.5% (premium services)
- **Relaxed**: 2% (best-effort only)

**Rule of Thumb**: Use 1% unless specific SLA requires otherwise.

## Troubleshooting

### Issue: High Packet Loss After Deployment
**Symptoms**: Loss > 1% consistently

**Solutions**:
1. Increase buffer size by 50%
2. Check for synchronized bursts (failure mode)
3. Verify shaping configuration matches recommendation
4. Consider link upgrade if loss persists

### Issue: Buffer Overflow Events
**Symptoms**: Frequent buffer overflows

**Solutions**:
1. Increase buffer from 143 µs → 200 µs
2. Check if cells are bursting simultaneously
3. Verify traffic hasn't increased since analysis
4. Re-run optimization with updated data

### Issue: URLLC Latency Violations
**Symptoms**: Latency-sensitive traffic degraded

**Solutions**:
1. Bypass shaping for URLLC traffic (DPI/QoS tagging)
2. Reduce buffer size to minimum (70 µs)
3. Implement priority queuing
4. Consider dedicated URLLC path

## Validation & Testing

### Pre-Production Testing
1. **Shadow Mode**: Run shaping in monitoring mode (no active shaping)
2. **A/B Testing**: Deploy on subset of links first
3. **Gradual Rollout**: 10% → 50% → 100% of traffic

### Key Metrics to Monitor
- **Packet Loss**: Target < 1%
- **Buffer Occupancy**: Target < 95%
- **Latency**: Within budget (< 1ms fronthaul)
- **Throughput**: No degradation

### Success Criteria
- ✅ Packet loss ≤ 1%
- ✅ No URLLC latency violations
- ✅ Buffer occupancy stable
- ✅ Cost savings realized

## Rollback Plan

If shaping causes issues:

1. **Immediate**: Disable shaping, revert to baseline
2. **Short-term**: Increase buffer size, reduce shaping aggressiveness
3. **Long-term**: Re-analyze with updated data, consider upgrade

## Support & Maintenance

### Regular Monitoring
- **Daily**: Packet loss, buffer occupancy
- **Weekly**: Traffic patterns, burst statistics
- **Monthly**: Re-run optimization with fresh data

### When to Re-Optimize
- Traffic patterns change significantly
- New cells added to network
- Packet loss exceeds target
- Hardware upgrades planned

## Contact & Resources

- **Documentation**: `docs/ARCHITECTURE.md`
- **What-If Simulator**: `src/cli_simulator.py --help`
- **Issue Tracking**: GitHub Issues
