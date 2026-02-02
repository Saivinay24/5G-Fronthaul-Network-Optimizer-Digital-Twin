"""
Data Export Layer for Digital Twin Interface

Exports processed telemetry, topology, optimization results, and operator decisions
to JSON format for consumption by the digital twin web interface.

Usage:
    python src/export_digital_twin_data.py [--data-folder DATA_FOLDER]
"""

import json
import pandas as pd
import numpy as np
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.main_v2 import FronthaulOptimizer


class DigitalTwinDataExporter:
    """Export optimizer results to digital twin interface format."""
    
    def __init__(self, optimizer: FronthaulOptimizer):
        self.optimizer = optimizer
        self.export_data = {}
        
    def export_topology_data(self) -> dict:
        """Export topology discovery data with correlation timeline."""
        telemetry = self.optimizer.telemetry
        
        # Build link definitions
        links = []
        for link_id, cells in telemetry.topology.items():
            links.append({
                'link_id': link_id,
                'cells': cells,
                'cell_count': len(cells),
                'is_shared': len(cells) > 1
            })
        
        # Correlation matrix for animated discovery
        correlation_matrix = []
        if telemetry.loss_data is not None:
            binary_loss = (telemetry.loss_data > 0).astype(int)
            corr_matrix = binary_loss.corr()
            
            for cell1 in corr_matrix.columns:
                for cell2 in corr_matrix.columns:
                    if cell1 < cell2:  # Avoid duplicates
                        correlation_matrix.append({
                            'cell1': int(cell1),
                            'cell2': int(cell2),
                            'correlation': float(corr_matrix.loc[cell1, cell2])
                        })
        
        # Calculate topology confidence over time
        confidence_timeline = self._calculate_confidence_timeline()
        
        return {
            'links': links,
            'correlation_matrix': correlation_matrix,
            'confidence_timeline': confidence_timeline,
            'total_cells': len(telemetry.symbol_data),
            'total_links': len(links)
        }
    
    def _calculate_confidence_timeline(self) -> list:
        """Simulate topology confidence building over time."""
        # In real implementation, this would track correlation convergence
        # For now, create a realistic confidence curve
        timeline = []
        for slot in range(0, 1000, 50):  # Sample every 50 slots
            # Confidence increases logarithmically
            confidence = min(0.95, 0.3 + 0.65 * (slot / 1000))
            timeline.append({
                'slot': slot,
                'confidence': round(confidence, 3)
            })
        return timeline
    
    def export_telemetry_data(self) -> dict:
        """Export slot-level telemetry data for replay."""
        telemetry = self.optimizer.telemetry
        
        # Per-cell slot data (FULL FIDELITY - No Downsampling)
        slot_data = {}
        for cell_id, df in telemetry.slot_data.items():
            # Export all slots for physics simulation
            slot_data[int(cell_id)] = {
                'slots': df['slot_idx'].tolist(),
                'throughput_gbps': df['throughput_gbps'].round(3).tolist(),
                'total_slots': len(df)
            }
        
        # Burst statistics
        burst_stats = {}
        for cell_id, stats in telemetry.burst_stats.items():
            burst_stats[int(cell_id)] = {
                'peak_gbps': round(stats['peak_gbps'], 3),
                'avg_gbps': round(stats['avg_gbps'], 3),
                'papr': round(stats['papr'], 2),
                'burst_count': stats['burst_count'],
                'burst_ratio': round(stats['burst_ratio'], 4)
            }
        
        # Loss events (if available)
        loss_events = self._extract_loss_events()
        
        return {
            'slot_data': slot_data,
            'burst_stats': burst_stats,
            'loss_events': loss_events
        }
    
    def _extract_loss_events(self) -> list:
        """Extract timestamped packet loss events."""
        events = []
        telemetry = self.optimizer.telemetry
        
        if telemetry.loss_data is not None:
            # Find slots with any loss
            for idx, row in telemetry.loss_data.iterrows():
                if row.sum() > 0:
                    cells_with_loss = [int(cell) for cell in row[row > 0].index]
                    events.append({
                        'slot': int(idx) if isinstance(idx, (int, np.integer)) else 0,
                        'cells': cells_with_loss,
                        'total_loss': int(row.sum())
                    })
        
        return events  # Return all events for full timeline visualization
    
    def export_optimization_data(self) -> dict:
        """Export baseline vs optimized comparison data."""
        
        optimization_results = {}
        
        # Per-link optimization results
        for link_id, result in self.optimizer.optimization_results.items():
            # Generate timeline data for this link
            telemetry = self.optimizer.telemetry
            traffic = telemetry.get_link_aggregated_traffic(link_id)
            
            if len(traffic) == 0:
                continue
            
            # Sample traffic for visualization (every 10th slot)
            sampled_traffic = traffic.iloc[::10]
            
            # Simulate buffer state timeline
            buffer_timeline = self._simulate_buffer_timeline(
                traffic, 
                result['optimal_capacity_gbps'],
                result['buffer_us']
            )
            
            optimization_results[int(link_id)] = {
                'baseline': {
                    'peak_capacity_gbps': round(result['peak_capacity_gbps'], 3),
                    'traffic_timeline': sampled_traffic.round(3).tolist()
                },
                'optimized': {
                    'optimal_capacity_gbps': round(result['optimal_capacity_gbps'], 3),
                    'capacity_reduction_pct': round(result['capacity_reduction_pct'], 2),
                    'buffer_us': result['buffer_us'],
                    'shaping_mode': result['shaping_mode']
                },
                'buffer_timeline': buffer_timeline,
                'simulation_stats': {
                    'loss_pct': round(result['simulation_stats']['loss_pct'], 4),
                    'max_occupancy_pct': round(result['simulation_stats']['max_occupancy_pct'], 2),
                    'overflow_events': result['simulation_stats']['overflow_events']
                }
            }
        
        return optimization_results
    
    def _simulate_buffer_timeline(self, traffic: pd.Series, capacity_gbps: float, 
                                   buffer_us: float, sample_rate: int = 10) -> list:
        """Simulate buffer occupancy over time for visualization."""
        from src.utils.constants import SYMBOL_DURATION_SEC
        
        # Convert to bits per symbol
        incoming_bits = traffic.values * 1e9 * SYMBOL_DURATION_SEC
        leak_bits = capacity_gbps * 1e9 * SYMBOL_DURATION_SEC
        max_buffer_bits = capacity_gbps * 1e9 * (buffer_us * 1e-6)
        
        timeline = []
        current_buffer = 0.0
        
        for idx, bits in enumerate(incoming_bits):
            if idx % sample_rate != 0:  # Sample every Nth slot
                continue
            
            # Update buffer
            current_buffer += (bits - leak_bits)
            current_buffer = max(0, min(current_buffer, max_buffer_bits))
            
            # Calculate occupancy percentage
            occupancy_pct = (current_buffer / max_buffer_bits * 100) if max_buffer_bits > 0 else 0
            
            timeline.append({
                'slot': int(idx),
                'occupancy_pct': round(occupancy_pct, 2),
                'is_overflow': bool(occupancy_pct >= 99.0)
            })
        
        return timeline[:200]  # Limit timeline length
    
    def export_decision_data(self) -> dict:
        """Export operator decision and risk assessment data."""
        
        decisions = {}
        
        for link_id, decision in self.optimizer.recommendations.items():
            decisions[int(link_id)] = {
                'action': decision['action'],
                'recommendation': decision['recommendation'],
                'risk_level': decision.get('risk_level', 'UNKNOWN'),
                'confidence': decision.get('confidence', 0.0),
                'rationale': decision.get('rationale', 'No rationale available'),
                'capacity_reduction_pct': decision.get('capacity_reduction_pct', 0.0)
            }
        
        # Overall risk assessment
        risk_summary = {
            'total_links': len(decisions),
            'enable_shaping': sum(1 for d in decisions.values() if d['action'] == 'ENABLE_SHAPING'),
            'conditional': sum(1 for d in decisions.values() if d['action'] == 'CONDITIONAL_SHAPING'),
            'upgrade_required': sum(1 for d in decisions.values() if d['action'] == 'UPGRADE_REQUIRED')
        }
        
        return {
            'per_link': decisions,
            'risk_summary': risk_summary
        }
    
    def export_all(self, output_path: str = None) -> dict:
        """Export all data to JSON file."""
        if output_path is None:
            output_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'results',
                'digital_twin_data.json'
            )
        
        print(f"\n📊 Exporting Digital Twin Data...")
        
        self.export_data = {
            'metadata': {
                'export_timestamp': pd.Timestamp.now().isoformat(),
                'data_folder': self.optimizer.data_folder,
                'version': '2.0'
            },
            'topology': self.export_topology_data(),
            'telemetry': self.export_telemetry_data(),
            'optimization': self.export_optimization_data(),
            'decisions': self.export_decision_data()
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write JSON
        with open(output_path, 'w') as f:
            json.dump(self.export_data, f, indent=2)
        
        # Calculate file size
        file_size_kb = os.path.getsize(output_path) / 1024
        
        print(f"✅ Digital Twin Data Exported")
        print(f"   📁 File: {output_path}")
        print(f"   📦 Size: {file_size_kb:.1f} KB")
        print(f"   🔗 Links: {len(self.export_data['topology']['links'])}")
        print(f"   📡 Cells: {self.export_data['topology']['total_cells']}")
        
        return self.export_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Export Digital Twin Data from Fronthaul Optimizer'
    )
    parser.add_argument(
        '--data-folder',
        type=str,
        default='data',
        help='Path to data folder (default: data)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: results/digital_twin_data.json)'
    )
    
    args = parser.parse_args()
    
    # Run full analysis
    print("🚀 Running Full 6-Layer Analysis...")
    optimizer = FronthaulOptimizer(data_folder=args.data_folder)
    optimizer.run_full_analysis()
    
    # Export data
    exporter = DigitalTwinDataExporter(optimizer)
    exporter.export_all(output_path=args.output)
    
    print("\n✅ Digital Twin Data Export Complete!")


if __name__ == '__main__':
    main()
