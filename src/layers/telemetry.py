"""
Layer 1: Telemetry & Analysis Layer

Responsibilities:
- Parse symbol-level throughput data
- Aggregate symbols → slots (14 symbols = 1 slot)
- Detect micro-bursts at sub-slot timescales
- Infer fronthaul topology via congestion correlation
- Output structured telemetry with burst statistics

NO MACHINE LEARNING. Deterministic statistical methods only.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.constants import (
    SYMBOL_DURATION_SEC, SYMBOLS_PER_SLOT, SLOT_DURATION_SEC,
    CORRELATION_THRESHOLD
)


class TelemetryAnalyzer:
    """
    Enhanced telemetry analysis with slot-level aggregation and burst detection.
    """
    
    def __init__(self, data_folder: str):
        self.data_folder = data_folder
        self.symbol_data: Dict[int, pd.DataFrame] = {}
        self.slot_data: Dict[int, pd.DataFrame] = {}
        self.loss_data: pd.DataFrame = None
        self.topology: Dict[int, List[int]] = {}
        self.burst_stats: Dict[int, Dict] = {}
        
    def load_symbol_data(self, cells: List[int]) -> None:
        """Load raw symbol-level throughput data."""
        print(f"📡 Loading symbol-level data for {len(cells)} cells...")
        
        for cell_id in cells:
            filename = f"throughput-cell-{cell_id}.dat"
            filepath = os.path.join(self.data_folder, filename)
            
            if not os.path.exists(filepath):
                continue
                
            try:
                df = pd.read_csv(filepath, sep=r'\s+', header=None, 
                               names=['timestamp', 'bits'], engine='python')
                df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
                df['bits'] = pd.to_numeric(df['bits'], errors='coerce')
                df = df.dropna()
                
                if len(df) > 0:
                    self.symbol_data[cell_id] = df
                    
            except Exception as e:
                print(f"⚠️  Failed to load cell {cell_id}: {e}")
                
        print(f"✅ Loaded {len(self.symbol_data)} cells")
        
    def aggregate_to_slots(self) -> None:
        """
        Aggregate symbol-level data to slot-level (14 symbols = 1 slot).
        This reduces noise and aligns with 5G NR frame structure.
        """
        print(f"🔄 Aggregating symbols → slots (14 symbols/slot)...")
        
        for cell_id, df in self.symbol_data.items():
            # Group by slot index
            df['slot_idx'] = df.index // SYMBOLS_PER_SLOT
            
            slot_aggregated = df.groupby('slot_idx').agg({
                'timestamp': 'first',  # Slot start time
                'bits': 'sum'  # Total bits in slot
            }).reset_index()
            
            # Convert to Gbps (slot-level rate)
            slot_aggregated['throughput_gbps'] = (
                slot_aggregated['bits'] / SLOT_DURATION_SEC / 1e9
            )
            
            self.slot_data[cell_id] = slot_aggregated
            
        print(f"✅ Slot aggregation complete")
        
    def detect_sub_slot_bursts(self, cell_id: int, window_symbols: int = 4) -> Dict:
        """
        Detect micro-bursts at sub-slot timescales using rolling windows.
        
        Args:
            cell_id: Cell to analyze
            window_symbols: Rolling window size (default 4 symbols ~143 µs)
            
        Returns:
            Dictionary with burst statistics
        """
        if cell_id not in self.symbol_data:
            return {}
            
        df = self.symbol_data[cell_id].copy()
        
        # Calculate instantaneous rate (Gbps)
        df['rate_gbps'] = df['bits'] / SYMBOL_DURATION_SEC / 1e9
        
        # Rolling window statistics
        df['rolling_max'] = df['rate_gbps'].rolling(window=window_symbols, min_periods=1).max()
        df['rolling_mean'] = df['rate_gbps'].rolling(window=window_symbols, min_periods=1).mean()
        
        # Burst metrics
        peak_rate = df['rate_gbps'].max()
        avg_rate = df['rate_gbps'].mean()
        papr = peak_rate / avg_rate if avg_rate > 0 else 0
        
        # Burst events (rate > 2x rolling mean)
        burst_threshold = 2.0
        df['is_burst'] = df['rate_gbps'] > (df['rolling_mean'] * burst_threshold)
        burst_count = df['is_burst'].sum()
        burst_ratio = burst_count / len(df) if len(df) > 0 else 0
        
        stats = {
            'peak_gbps': peak_rate,
            'avg_gbps': avg_rate,
            'papr': papr,
            'burst_count': int(burst_count),
            'burst_ratio': burst_ratio,
            'window_symbols': window_symbols
        }
        
        return stats
        
    def analyze_all_bursts(self) -> None:
        """Analyze burst characteristics for all cells."""
        print(f"💥 Analyzing sub-slot burst patterns...")
        
        for cell_id in self.symbol_data.keys():
            self.burst_stats[cell_id] = self.detect_sub_slot_bursts(cell_id)
            
        print(f"✅ Burst analysis complete for {len(self.burst_stats)} cells")
        
    def discover_topology(self, loss_data) -> Dict[int, List[int]]:
        """
        Discover network topology using congestion correlation.
        Cells with correlated packet loss share the same physical link.
        
        Args:
            loss_data: DataFrame or Dict with packet loss per cell
            
        Returns:
            Dictionary mapping link_id → [cell_ids]
        """
        print(f"🔗 Discovering network topology via loss correlation...")
        
        # Convert dict to DataFrame if needed
        if isinstance(loss_data, dict):
            loss_df = pd.DataFrame(loss_data)
        else:
            loss_df = loss_data
            
        self.loss_data = loss_df
        
        # Binarize loss events
        binary_loss = (loss_df > 0).astype(int)
        
        if binary_loss.sum().sum() == 0:
            print("✅ No packet loss detected - all cells independent")
            return {i: [cell] for i, cell in enumerate(loss_df.columns)}
            
        # Correlation matrix
        corr_matrix = binary_loss.corr()
        
        # Cluster cells by correlation
        processed = set()
        clusters = {}
        link_id = 1
        
        for cell in corr_matrix.columns:
            if cell in processed:
                continue
                
            # Find correlated cells
            correlated = corr_matrix[cell][corr_matrix[cell] >= CORRELATION_THRESHOLD].index.tolist()
            
            if len(correlated) > 1:
                clusters[link_id] = sorted(correlated)
                processed.update(correlated)
                link_id += 1
            else:
                # Independent cell
                clusters[link_id] = [cell]
                processed.add(cell)
                link_id += 1
                
        self.topology = clusters
        
        # Print topology
        for link_id, cells in clusters.items():
            if len(cells) > 1:
                print(f"🔗 LINK {link_id}: Cells {cells}")
            else:
                print(f"⚡ LINK {link_id}: Cell {cells[0]} (independent)")
                
        return clusters
        
    def get_link_aggregated_traffic(self, link_id: int) -> pd.Series:
        """
        Get aggregated slot-level traffic for a link.
        
        Args:
            link_id: Link identifier
            
        Returns:
            Series with total throughput (Gbps) per slot
        """
        if link_id not in self.topology:
            return pd.Series()
            
        cells = self.topology[link_id]
        
        # Aggregate slot data across cells
        slot_series = []
        for cell_id in cells:
            if cell_id in self.slot_data:
                # Use slot_idx as index for alignment to avoid duplicate timestamp issues
                slot_series.append(self.slot_data[cell_id].set_index('slot_idx')['throughput_gbps'])
                
        if not slot_series:
            return pd.Series()
            
        # Align slots and sum
        combined = pd.concat(slot_series, axis=1).fillna(0)
        total_throughput = combined.sum(axis=1)
        
        return total_throughput
        
    def get_telemetry_summary(self) -> Dict:
        """
        Generate comprehensive telemetry summary.
        
        Returns:
            Dictionary with topology, burst stats, and traffic summaries
        """
        summary = {
            'topology': self.topology,
            'burst_statistics': self.burst_stats,
            'link_traffic': {}
        }
        
        for link_id in self.topology.keys():
            traffic = self.get_link_aggregated_traffic(link_id)
            
            if len(traffic) > 0:
                summary['link_traffic'][link_id] = {
                    'peak_gbps': traffic.max(),
                    'avg_gbps': traffic.mean(),
                    'papr': traffic.max() / traffic.mean() if traffic.mean() > 0 else 0,
                    'samples': len(traffic)
                }
                
        return summary
