#!/usr/bin/env python3
"""
Quick Operator Summary Generator

Generates operator-facing summary in <30 seconds.
Runs minimal analysis (topology + optimization only) for rapid decision support.

Usage:
    python src/quick_summary.py [--data-folder DATA_FOLDER]
"""

import pandas as pd
import sys
import os
import argparse
from typing import Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from layers.telemetry import TelemetryAnalyzer
from layers.intelligence import AdaptiveShaper
from layers.resilience import ResilienceAnalyzer
from layers.operator_decision import OperatorDecisionEngine
from layers.sustainability import SustainabilityAnalyzer
from operator_summary import OperatorSummaryGenerator
from main import NetworkLoader


def quick_analysis(data_folder: str = 'data') -> Dict:
    """
    Run quick analysis for operator summary.
    
    Args:
        data_folder: Path to data folder
        
    Returns:
        Dict with recommendations and sustainability analyses
    """
    print("\n" + "="*70)
    print("🚀 QUICK OPERATOR SUMMARY GENERATOR")
    print("="*70 + "\n")
    
    # Layer 1: Telemetry (minimal)
    print("📡 Loading telemetry data...")
    loader = NetworkLoader(data_folder)
    loss_data = loader.load_pkt_stats()
    
    telemetry = TelemetryAnalyzer(data_folder)
    topology = telemetry.discover_topology(loss_data)
    
    all_cells = list(range(1, 25))
    telemetry.load_symbol_data(all_cells)
    telemetry.aggregate_to_slots()
    
    print(f"   ✅ {len(topology)} links discovered\n")
    
    # Layer 2: Intelligence
    print("🧠 Running optimization analysis...")
    shaper = AdaptiveShaper()
    optimization_results = {}
    
    for link_id, cells in topology.items():
        if len(cells) == 0:
            continue
            
        traffic = telemetry.get_link_aggregated_traffic(link_id)
        if len(traffic) == 0:
            continue
            
        papr = traffic.max() / traffic.mean() if traffic.mean() > 0 else 0
        result = shaper.optimize_capacity(traffic, papr)
        optimization_results[link_id] = result
        
    print(f"   ✅ {len(optimization_results)} links optimized\n")
    
    # Layer 3: Resilience (quick check)
    print("🛡️  Checking failure modes...")
    resilience = ResilienceAnalyzer()
    resilience_analyses = {}
    
    for link_id, cells in topology.items():
        if link_id not in optimization_results:
            continue
            
        cell_traffic = {}
        for cell_id in cells:
            if cell_id in telemetry.slot_data:
                # Use slot_idx as index to avoid duplicate timestamp issues
                cell_traffic[cell_id] = telemetry.slot_data[cell_id].set_index('slot_idx')['throughput_gbps']
                
        analysis = resilience.analyze_all_failure_modes(
            cell_traffic,
            optimization_results[link_id]
        )
        resilience_analyses[link_id] = analysis
        
    print(f"   ✅ Resilience analysis complete\n")
    
    # Layer 4: Operator Decision
    print("💡 Generating recommendations...")
    decision_engine = OperatorDecisionEngine()
    recommendations = decision_engine.generate_all_recommendations(
        optimization_results,
        resilience_analyses
    )
    
    print(f"   ✅ {len(recommendations)} recommendations generated\n")
    
    # Layer 5: Sustainability (quick)
    print("🌍 Calculating impact...")
    sustainability = SustainabilityAnalyzer()
    sustainability_analyses = {}
    
    for link_id, opt_result in optimization_results.items():
        analysis = sustainability.analyze_link_sustainability(link_id, opt_result)
        sustainability_analyses[link_id] = analysis
        
    print(f"   ✅ Sustainability analysis complete\n")
    
    return {
        'recommendations': recommendations,
        'sustainability': sustainability_analyses
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Quick Operator Summary Generator'
    )
    parser.add_argument(
        '--data-folder',
        type=str,
        default='data',
        help='Path to data folder'
    )
    parser.add_argument(
        '--cli-only',
        action='store_true',
        help='Only print CLI summary (no files)'
    )
    
    args = parser.parse_args()
    
    # Run quick analysis
    results = quick_analysis(args.data_folder)
    
    # Generate summaries
    print("="*70)
    print("GENERATING OPERATOR SUMMARIES")
    print("="*70 + "\n")
    
    summary_gen = OperatorSummaryGenerator(
        results['recommendations'],
        results['sustainability']
    )
    
    if args.cli_only:
        # Print to console only
        print(summary_gen.generate_cli_summary())
    else:
        # Generate all formats
        os.makedirs('results', exist_ok=True)
        
        summary_gen.generate_markdown_summary('results/OPERATOR_SUMMARY.md')
        summary_gen.generate_html_summary('results/OPERATOR_SUMMARY.html')
        
        print("\n" + "="*70)
        print("✅ SUMMARY GENERATION COMPLETE")
        print("="*70)
        print("\nGenerated files:")
        print("  - results/OPERATOR_SUMMARY.md")
        print("  - results/OPERATOR_SUMMARY.html")
        print("\nOpen the HTML file in a browser for best viewing experience.\n")


if __name__ == '__main__':
    main()
