"""
What-If Simulator CLI Tool

Interactive tool for exploring parameter space and trade-offs.

Usage:
    python src/cli_simulator.py --link 2 --buffer 100 --rate 5 --loss-limit 0.01
"""

import argparse
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from layers.telemetry import TelemetryAnalyzer
from layers.simulation import WhatIfSimulator
from main import NetworkLoader


def main():
    parser = argparse.ArgumentParser(
        description='What-If Simulator for Fronthaul Optimization'
    )
    parser.add_argument('--link', type=int, required=True, help='Link ID to simulate')
    parser.add_argument('--buffer', type=float, required=True, help='Buffer size (microseconds)')
    parser.add_argument('--rate', type=float, required=True, help='Link rate (Gbps)')
    parser.add_argument('--loss-limit', type=float, default=0.01, help='Max packet loss (default 1%%)')
    parser.add_argument('--data-folder', type=str, default='data', help='Data folder path')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("WHAT-IF SIMULATOR")
    print("="*70 + "\n")
    
    # Load data
    print(f"📡 Loading data for Link {args.link}...")
    
    loader = NetworkLoader(args.data_folder)
    loss_data = loader.load_pkt_stats()
    
    telemetry = TelemetryAnalyzer(args.data_folder)
    topology = telemetry.discover_topology(loss_data)
    
    if args.link not in topology:
        print(f"❌ Link {args.link} not found in topology")
        return
        
    cells = topology[args.link]
    print(f"   Cells: {cells}\n")
    
    # Load traffic
    telemetry.load_symbol_data(cells)
    telemetry.aggregate_to_slots()
    traffic = telemetry.get_link_aggregated_traffic(args.link)
    
    if len(traffic) == 0:
        print(f"❌ No traffic data for Link {args.link}")
        return
        
    # Run simulation
    print("🔄 Running simulation...")
    simulator = WhatIfSimulator()
    result = simulator.simulate_scenario(
        traffic,
        args.buffer,
        args.rate,
        args.loss_limit
    )
    
    # Print results
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70 + "\n")
    
    print("📊 INPUT PARAMETERS:")
    print(f"   ├─ Buffer Size:       {result['buffer_us']} µs")
    print(f"   ├─ Link Rate:         {result['link_rate_gbps']} Gbps")
    print(f"   └─ Loss Limit:        {result['loss_limit']*100}%\n")
    
    print("📈 TRAFFIC CHARACTERISTICS:")
    print(f"   ├─ Peak Capacity:     {result['peak_capacity_gbps']:.2f} Gbps")
    print(f"   └─ Capacity Reduction: {result['capacity_reduction_pct']:.1f}%\n")
    
    print("🎯 SIMULATION RESULTS:")
    print(f"   ├─ Actual Loss:       {result['actual_loss_pct']:.3f}%")
    print(f"   ├─ Meets Target:      {'✅ YES' if result['meets_target'] else '❌ NO'}")
    
    stats = result['simulation_stats']
    print(f"   ├─ Max Buffer Occupancy: {stats['max_occupancy_pct']:.1f}%")
    print(f"   └─ Overflow Events:   {stats['overflow_events']}\n")
    
    # Recommendation
    if result['meets_target']:
        print("💡 RECOMMENDATION:")
        print(f"   ✅ Configuration is viable. Packet loss ({result['actual_loss_pct']:.3f}%) ")
        print(f"      is within target ({result['loss_limit']*100}%).\n")
    else:
        print("⚠️  RECOMMENDATION:")
        print(f"   ❌ Configuration FAILS. Packet loss ({result['actual_loss_pct']:.3f}%) ")
        print(f"      exceeds target ({result['loss_limit']*100}%).")
        print(f"   Suggested actions:")
        print(f"      1. Increase link rate above {args.rate} Gbps")
        print(f"      2. Increase buffer size above {args.buffer} µs")
        print(f"      3. Relax loss limit above {args.loss_limit*100}%\n")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
