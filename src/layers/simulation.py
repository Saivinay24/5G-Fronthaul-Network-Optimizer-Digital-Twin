"""
Layer 6: Simulation & Scaling Layer

Responsibilities:
- What-if simulator for parameter exploration
- Multi-site scaling analysis
- Complexity demonstration (O(N) scaling)

Components:
A. What-if simulator (vary buffer, rate, loss limit)
B. Scaling analysis (24 → 240 → 2400 cells)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.layers.intelligence import AdaptiveShaper
from src.utils.constants import PACKET_LOSS_LIMIT


class WhatIfSimulator:
    """
    Interactive simulator for exploring parameter space.
    """
    
    def __init__(self):
        self.shaper = AdaptiveShaper()
        
    def simulate_scenario(
        self,
        throughput_gbps: pd.Series,
        buffer_us: float,
        link_rate_gbps: float,
        loss_limit: float = PACKET_LOSS_LIMIT
    ) -> Dict:
        """
        Simulate a what-if scenario with custom parameters.
        
        Args:
            throughput_gbps: Traffic series
            buffer_us: Buffer size (microseconds)
            link_rate_gbps: Link capacity (Gbps)
            loss_limit: Maximum allowed packet loss
            
        Returns:
            Simulation results
        """
        # Run leaky bucket simulation
        loss_ratio, stats = self.shaper.simulate_leaky_bucket(
            throughput_gbps, link_rate_gbps, buffer_us
        )
        
        # Determine if configuration meets requirements
        meets_loss_target = loss_ratio <= loss_limit
        peak_capacity = throughput_gbps.max()
        capacity_reduction = (1 - link_rate_gbps / peak_capacity) * 100
        
        result = {
            'buffer_us': buffer_us,
            'link_rate_gbps': link_rate_gbps,
            'loss_limit': loss_limit,
            'actual_loss_ratio': loss_ratio,
            'actual_loss_pct': loss_ratio * 100,
            'meets_target': meets_loss_target,
            'peak_capacity_gbps': peak_capacity,
            'capacity_reduction_pct': capacity_reduction,
            'simulation_stats': stats
        }
        
        return result
        
    def parameter_sweep(
        self,
        throughput_gbps: pd.Series,
        buffer_range: Tuple[float, float, float] = (70, 200, 10),
        rate_range: Tuple[float, float, float] = (3, 10, 0.5)
    ) -> pd.DataFrame:
        """
        Sweep through parameter space to explore trade-offs.
        
        Args:
            throughput_gbps: Traffic series
            buffer_range: (min, max, step) for buffer size (µs)
            rate_range: (min, max, step) for link rate (Gbps)
            
        Returns:
            DataFrame with simulation results for all combinations
        """
        results = []
        
        buffer_values = np.arange(*buffer_range)
        rate_values = np.arange(*rate_range)
        
        for buffer_us in buffer_values:
            for rate_gbps in rate_values:
                result = self.simulate_scenario(
                    throughput_gbps, buffer_us, rate_gbps
                )
                results.append(result)
                
        df = pd.DataFrame(results)
        return df


class ScalingAnalyzer:
    """
    Analyze computational complexity and scaling behavior.
    """
    
    @staticmethod
    def analyze_complexity() -> Dict:
        """
        Analytical complexity analysis.
        
        Returns:
            Complexity breakdown by layer
        """
        return {
            'layer_1_telemetry': {
                'slot_aggregation': 'O(N)',
                'burst_detection': 'O(N * W)',  # W = window size (constant)
                'topology_discovery': 'O(C²)',  # C = number of cells
                'explanation': (
                    'Slot aggregation is linear in symbols. Burst detection uses '
                    'rolling windows (constant size). Topology discovery computes '
                    'correlation matrix (quadratic in cells, but cells << symbols).'
                )
            },
            'layer_2_intelligence': {
                'leaky_bucket_simulation': 'O(N)',
                'binary_search': 'O(log R)',  # R = rate search range
                'total': 'O(N log R)',
                'explanation': (
                    'Leaky bucket iterates through all symbols (linear). Binary search '
                    'runs log(R) iterations. Total: O(N log R) where N >> log R.'
                )
            },
            'layer_3_resilience': {
                'failure_detection': 'O(C²)',
                'explanation': (
                    'Failure mode detection computes cell-to-cell correlations. '
                    'Quadratic in cells, but cells are typically small (< 100).'
                )
            },
            'overall_complexity': {
                'time': 'O(N log R + C²)',
                'space': 'O(N + C²)',
                'dominant_term': 'O(N log R)',
                'explanation': (
                    'For typical deployments: N (symbols) >> C (cells). '
                    'Time complexity dominated by symbol processing. '
                    'Near-linear scaling in practice.'
                )
            }
        }
        
    @staticmethod
    def estimate_scaling(num_cells: int, symbols_per_cell: int = 100000) -> Dict:
        """
        Estimate resource requirements for different deployment sizes.
        
        Args:
            num_cells: Number of cells to analyze
            symbols_per_cell: Average symbols per cell
            
        Returns:
            Resource estimates
        """
        total_symbols = num_cells * symbols_per_cell
        
        # Memory estimates (rough)
        bytes_per_symbol = 16  # timestamp + value (float64)
        memory_mb = (total_symbols * bytes_per_symbol) / (1024 ** 2)
        
        # Time estimates (rough, based on empirical testing)
        # Assume ~1M symbols/second processing rate
        processing_rate = 1e6  # symbols/second
        estimated_time_sec = total_symbols / processing_rate
        
        return {
            'num_cells': num_cells,
            'total_symbols': total_symbols,
            'estimated_memory_mb': memory_mb,
            'estimated_time_sec': estimated_time_sec,
            'estimated_time_min': estimated_time_sec / 60,
            'parallelization_potential': 'HIGH (cells can be processed independently)'
        }
        
    @staticmethod
    def demonstrate_scaling() -> str:
        """
        Generate scaling demonstration report.
        
        Returns:
            Formatted scaling analysis
        """
        report = f"\n{'='*70}\n"
        report += "MULTI-SITE SCALING ANALYSIS\n"
        report += f"{'='*70}\n\n"
        
        # Complexity analysis
        complexity = ScalingAnalyzer.analyze_complexity()
        report += "📊 COMPUTATIONAL COMPLEXITY:\n"
        report += f"   ├─ Telemetry Layer:     {complexity['layer_1_telemetry']['topology_discovery']}\n"
        report += f"   ├─ Intelligence Layer:  {complexity['layer_2_intelligence']['total']}\n"
        report += f"   ├─ Resilience Layer:    {complexity['layer_3_resilience']['failure_detection']}\n"
        report += f"   └─ Overall:             {complexity['overall_complexity']['time']}\n\n"
        
        # Scaling scenarios
        report += "🚀 SCALING SCENARIOS:\n\n"
        
        scenarios = [
            ('Small Site', 24),
            ('Medium Site', 240),
            ('Large Site', 2400)
        ]
        
        for name, num_cells in scenarios:
            est = ScalingAnalyzer.estimate_scaling(num_cells)
            report += f"   {name} ({num_cells} cells):\n"
            report += f"      ├─ Total Symbols:   {est['total_symbols']:,}\n"
            report += f"      ├─ Memory Required: {est['estimated_memory_mb']:.1f} MB\n"
            report += f"      ├─ Processing Time: {est['estimated_time_min']:.2f} minutes\n"
            report += f"      └─ Parallelizable:  {est['parallelization_potential']}\n\n"
            
        report += "💡 SCALING STRATEGY:\n"
        report += "   ├─ Cells can be processed independently (embarrassingly parallel)\n"
        report += "   ├─ Linear memory scaling: O(N)\n"
        report += "   ├─ Near-linear time scaling: O(N log R)\n"
        report += "   └─ No quadratic explosion in symbol processing\n"
        
        report += f"\n{'='*70}\n"
        
        return report
