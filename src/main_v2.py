"""
Production-Grade O-RAN Fronthaul Optimizer v2.0
Main Orchestrator - Integrates all six layers

Usage:
    python src/main_v2.py [--data-folder DATA_FOLDER]
"""

import pandas as pd
import numpy as np
import os
import sys
import argparse
from typing import Dict, List

# Import all layers
from layers.telemetry import TelemetryAnalyzer
from layers.intelligence import AdaptiveShaper, DeterministicRationale
from layers.resilience import ResilienceAnalyzer
from layers.operator_decision import OperatorDecisionEngine
from layers.sustainability import SustainabilityAnalyzer
from layers.simulation import ScalingAnalyzer
from operator_summary import OperatorSummaryGenerator

# Legacy loader for packet stats
sys.path.insert(0, os.path.dirname(__file__))
from main import NetworkLoader


class FronthaulOptimizer:
    """
    Production-grade orchestrator for six-layer optimization system.
    """
    
    def __init__(self, data_folder: str = 'data'):
        self.data_folder = data_folder
        
        # Initialize all layers
        self.telemetry = TelemetryAnalyzer(data_folder)
        self.shaper = AdaptiveShaper()
        self.resilience = ResilienceAnalyzer()
        self.decision_engine = OperatorDecisionEngine()
        self.sustainability = SustainabilityAnalyzer()
        
        # Results storage
        self.optimization_results = {}
        self.resilience_analyses = {}
        self.recommendations = {}
        self.sustainability_analyses = {}
        
    def run_full_analysis(self) -> None:
        """
        Execute complete six-layer analysis pipeline.
        """
        print("\n" + "="*70)
        print("🚀 PRODUCTION-GRADE O-RAN FRONTHAUL OPTIMIZER v2.0")
        print("="*70 + "\n")
        
        # Print deterministic rationale
        print("📋 DESIGN PHILOSOPHY:")
        DeterministicRationale.print_rationale()
        
        # Layer 1: Telemetry & Analysis
        print("\n" + "="*70)
        print("LAYER 1: TELEMETRY & ANALYSIS")
        print("="*70 + "\n")
        
        self._run_telemetry_layer()
        
        # Layer 2: Deterministic Intelligence
        print("\n" + "="*70)
        print("LAYER 2: DETERMINISTIC INTELLIGENCE")
        print("="*70 + "\n")
        
        self._run_intelligence_layer()
        
        # Layer 3: Control & Resilience
        print("\n" + "="*70)
        print("LAYER 3: CONTROL & RESILIENCE")
        print("="*70 + "\n")
        
        self._run_resilience_layer()
        
        # Layer 4: Operator Decision
        print("\n" + "="*70)
        print("LAYER 4: OPERATOR DECISION")
        print("="*70 + "\n")
        
        self._run_decision_layer()
        
        # Layer 5: Impact & Sustainability
        print("\n" + "="*70)
        print("LAYER 5: IMPACT & SUSTAINABILITY")
        print("="*70 + "\n")
        
        self._run_sustainability_layer()
        
        # Layer 6: Simulation & Scaling
        print("\n" + "="*70)
        print("LAYER 6: SIMULATION & SCALING")
        print("="*70 + "\n")
        
        self._run_scaling_layer()
        
        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70 + "\n")
        
    def _run_telemetry_layer(self) -> None:
        """Execute Layer 1: Telemetry & Analysis."""
        # Load packet loss data for topology discovery
        loader = NetworkLoader(self.data_folder)
        loss_data = loader.load_pkt_stats()
        
        # Discover topology
        topology = self.telemetry.discover_topology(loss_data)
        
        # Load symbol-level data for all cells
        all_cells = list(range(1, 25))  # Cells 1-24
        self.telemetry.load_symbol_data(all_cells)
        
        # Aggregate to slots
        self.telemetry.aggregate_to_slots()
        
        # Analyze bursts
        self.telemetry.analyze_all_bursts()
        
        # Print summary
        summary = self.telemetry.get_telemetry_summary()
        print(f"✅ Topology discovered: {len(topology)} links")
        print(f"✅ Burst analysis complete for {len(summary['burst_statistics'])} cells")
        
    def _run_intelligence_layer(self) -> None:
        """Execute Layer 2: Deterministic Intelligence."""
        print("🧠 Running adaptive traffic shaping optimization...\n")
        
        for link_id, cells in self.telemetry.topology.items():
            if len(cells) == 0:
                continue
                
            # Get aggregated traffic
            traffic = self.telemetry.get_link_aggregated_traffic(link_id)
            
            if len(traffic) == 0:
                continue
                
            # Calculate PAPR
            papr = traffic.max() / traffic.mean() if traffic.mean() > 0 else 0
            
            # Optimize capacity with adaptive shaping
            result = self.shaper.optimize_capacity(traffic, papr)
            self.optimization_results[link_id] = result
            
            print(f"Link {link_id}:")
            print(f"   ├─ PAPR: {papr:.1f}x")
            print(f"   ├─ Shaping Mode: {result['shaping_mode']}")
            print(f"   ├─ Peak Capacity: {result['peak_capacity_gbps']:.2f} Gbps")
            print(f"   ├─ Optimal Capacity: {result['optimal_capacity_gbps']:.2f} Gbps")
            print(f"   └─ Reduction: {result['capacity_reduction_pct']:.1f}%\n")
            
    def _run_resilience_layer(self) -> None:
        """Execute Layer 3: Control & Resilience."""
        print("🛡️  Analyzing failure modes...\n")
        
        for link_id, cells in self.telemetry.topology.items():
            if link_id not in self.optimization_results:
                continue
                
            # Get cell-level traffic for synchronization analysis
            cell_traffic = {}
            for cell_id in cells:
                if cell_id in self.telemetry.slot_data:
                    # Use slot_idx as index to avoid duplicate timestamp issues
                    cell_traffic[cell_id] = self.telemetry.slot_data[cell_id].set_index('slot_idx')['throughput_gbps']
                    
            # Run failure mode analysis
            analysis = self.resilience.analyze_all_failure_modes(
                cell_traffic,
                self.optimization_results[link_id]
            )
            
            self.resilience_analyses[link_id] = analysis
            
            print(f"Link {link_id}:")
            print(f"   ├─ Overall Risk: {analysis['overall_risk']}")
            print(f"   └─ Failure Modes Detected: {analysis['failure_modes_detected']}\n")
            
    def _run_decision_layer(self) -> None:
        """Execute Layer 4: Operator Decision."""
        print("💡 Generating operator recommendations...\n")
        
        self.recommendations = self.decision_engine.generate_all_recommendations(
            self.optimization_results,
            self.resilience_analyses
        )
        
        # Print formatted reports
        for link_id, recommendation in self.recommendations.items():
            report = self.decision_engine.format_operator_report(recommendation)
            print(report)
            
        # Generate operator summary reports
        print("\n📋 Generating operator summary reports...")
        summary_gen = OperatorSummaryGenerator(
            self.recommendations,
            self.sustainability_analyses if hasattr(self, 'sustainability_analyses') and self.sustainability_analyses else None
        )
        
        # Create results directory if needed
        os.makedirs('results', exist_ok=True)
        
        # Generate both formats
        summary_gen.generate_markdown_summary('results/OPERATOR_SUMMARY.md')
        summary_gen.generate_html_summary('results/OPERATOR_SUMMARY.html')
        print("   ✅ Operator summaries generated in results/\n")
            
    def _run_sustainability_layer(self) -> None:
        """Execute Layer 5: Impact & Sustainability."""
        print("🌍 Calculating sustainability impact...\n")
        
        for link_id, opt_result in self.optimization_results.items():
            analysis = self.sustainability.analyze_link_sustainability(link_id, opt_result)
            self.sustainability_analyses[link_id] = analysis
            
            report = self.sustainability.format_sustainability_report(analysis)
            print(report)
            
        # Network-wide aggregate
        if self.sustainability_analyses:
            aggregate = self.sustainability.aggregate_network_impact(self.sustainability_analyses)
            
            print("\n" + "="*70)
            print("NETWORK-WIDE SUSTAINABILITY IMPACT")
            print("="*70 + "\n")
            print(f"   ├─ Total Links Analyzed:    {aggregate['num_links']}")
            print(f"   ├─ Total Hardware Savings:  ${aggregate['total_hardware_savings_usd']:,}")
            print(f"   ├─ Total Energy Savings:    {aggregate['total_annual_energy_kwh']:.1f} kWh/year")
            print(f"   └─ Total CO₂ Reduction:     {aggregate['total_annual_co2_tons']:.2f} tons/year\n")
            
    def _run_scaling_layer(self) -> None:
        """Execute Layer 6: Simulation & Scaling."""
        print("📈 Demonstrating scaling capabilities...\n")
        
        scaling_report = ScalingAnalyzer.demonstrate_scaling()
        print(scaling_report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Production-Grade O-RAN Fronthaul Optimizer v2.0'
    )
    parser.add_argument(
        '--data-folder',
        type=str,
        default='data',
        help='Path to data folder containing telemetry files'
    )
    
    args = parser.parse_args()
    
    # Run full analysis
    optimizer = FronthaulOptimizer(args.data_folder)
    optimizer.run_full_analysis()


if __name__ == '__main__':
    main()
