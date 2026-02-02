"""
Layer 3: Control & Resilience Layer

Responsibilities:
- Identify failure modes where shaping may be suboptimal
- Detect risky scenarios in real-time
- Provide mitigation strategies for each failure mode

Failure Modes:
1. Synchronized cell bursts (multiple cells bursting simultaneously)
2. URLLC traffic (ultra-low latency requirements)
3. Buffer misconfiguration (too small or too large)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.constants import MIN_BUFFER_US, MAX_BUFFER_US


class ResilienceAnalyzer:
    """
    Failure mode detection and mitigation strategy engine.
    """
    
    def __init__(self):
        self.failure_modes = []
        
    def detect_synchronized_bursts(
        self,
        cell_traffic: Dict[int, pd.Series],
        sync_threshold: float = 0.7
    ) -> Dict:
        """
        Detect if multiple cells are bursting simultaneously.
        This can overwhelm shaping buffers.
        
        Args:
            cell_traffic: Dict of cell_id → traffic series
            sync_threshold: Correlation threshold for synchronization
            
        Returns:
            Detection result with risk level and mitigation
        """
        if len(cell_traffic) < 2:
            return {'detected': False, 'risk': 'NONE'}
            
        # Binarize bursts (traffic > 2x mean)
        burst_signals = {}
        for cell_id, traffic in cell_traffic.items():
            mean_rate = traffic.mean()
            burst_signals[cell_id] = (traffic > 2 * mean_rate).astype(int)
            
        # Calculate cross-correlation
        df = pd.DataFrame(burst_signals)
        corr_matrix = df.corr()
        
        # Find highly correlated pairs
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr = corr_matrix.iloc[i, j]
                if corr >= sync_threshold:
                    high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr))
                    
        if high_corr_pairs:
            return {
                'detected': True,
                'risk': 'HIGH',
                'synchronized_pairs': high_corr_pairs,
                'explanation': (
                    f"Detected {len(high_corr_pairs)} cell pairs with synchronized bursts. "
                    "When multiple cells burst simultaneously, aggregate traffic can exceed "
                    "buffer capacity even with shaping."
                ),
                'mitigation': [
                    "Increase buffer size to maximum (200 µs)",
                    "Consider load balancing across multiple physical links",
                    "If synchronization persists, upgrade link capacity"
                ]
            }
        else:
            return {
                'detected': False,
                'risk': 'LOW',
                'explanation': 'Cell bursts are not synchronized - shaping should be effective'
            }
            
    def detect_urllc_traffic(
        self,
        traffic_stats: Dict,
        latency_budget_us: float = 200
    ) -> Dict:
        """
        Detect if traffic has URLLC-like characteristics (ultra-low latency).
        Buffering adds latency, which may violate URLLC requirements.
        
        Args:
            traffic_stats: Traffic statistics dict
            latency_budget_us: Maximum tolerable latency (default 100 µs)
            
        Returns:
            Detection result with risk and mitigation
        """
        buffer_us = traffic_stats.get('buffer_us', 143)
        
        # URLLC typically requires < 1ms end-to-end latency
        # Fronthaul buffering should stay well below this
        if buffer_us > latency_budget_us:
            return {
                'detected': True,
                'risk': 'CRITICAL',
                'buffer_latency_us': buffer_us,
                'latency_budget_us': latency_budget_us,
                'explanation': (
                    f"Buffer delay ({buffer_us} µs) exceeds URLLC latency budget "
                    f"({latency_budget_us} µs). Shaping will violate QoS requirements."
                ),
                'mitigation': [
                    "BYPASS shaping for URLLC traffic (requires DPI or QoS tagging)",
                    "Upgrade link capacity to avoid buffering",
                    "Implement priority queuing with separate URLLC path"
                ]
            }
        else:
            return {
                'detected': False,
                'risk': 'LOW',
                'explanation': f'Buffer latency ({buffer_us} µs) within URLLC budget'
            }
            
    def detect_buffer_misconfiguration(
        self,
        buffer_us: float,
        max_occupancy_pct: float
    ) -> Dict:
        """
        Detect if buffer is misconfigured (too small or too large).
        
        Args:
            buffer_us: Configured buffer size
            max_occupancy_pct: Maximum observed buffer occupancy (%)
            
        Returns:
            Detection result with recommendations
        """
        issues = []
        
        # Buffer too small (frequently overflowing)
        if max_occupancy_pct > 95:
            issues.append({
                'type': 'BUFFER_TOO_SMALL',
                'risk': 'HIGH',
                'explanation': (
                    f"Buffer occupancy reaches {max_occupancy_pct:.1f}%, indicating "
                    "frequent overflows. Packet loss may exceed target."
                ),
                'mitigation': [
                    f"Increase buffer from {buffer_us} µs to {min(buffer_us * 1.5, MAX_BUFFER_US):.0f} µs",
                    "Re-run capacity optimization with larger buffer"
                ]
            })
            
        # Buffer too large (wasting resources)
        if max_occupancy_pct < 30 and buffer_us > MIN_BUFFER_US:
            issues.append({
                'type': 'BUFFER_OVERSIZED',
                'risk': 'LOW',
                'explanation': (
                    f"Buffer occupancy only {max_occupancy_pct:.1f}%, buffer is oversized. "
                    "This wastes memory and adds unnecessary latency."
                ),
                'mitigation': [
                    f"Reduce buffer from {buffer_us} µs to {max(buffer_us * 0.7, MIN_BUFFER_US):.0f} µs",
                    "Lower latency improves QoS for latency-sensitive traffic"
                ]
            })
            
        # Buffer out of spec range
        if buffer_us < MIN_BUFFER_US or buffer_us > MAX_BUFFER_US:
            issues.append({
                'type': 'BUFFER_OUT_OF_RANGE',
                'risk': 'MEDIUM',
                'explanation': (
                    f"Buffer size ({buffer_us} µs) outside recommended range "
                    f"[{MIN_BUFFER_US}-{MAX_BUFFER_US} µs]"
                ),
                'mitigation': [
                    f"Adjust buffer to recommended range [{MIN_BUFFER_US}-{MAX_BUFFER_US} µs]"
                ]
            })
            
        if issues:
            return {
                'detected': True,
                'issues': issues,
                'risk': max(issue['risk'] for issue in issues)
            }
        else:
            return {
                'detected': False,
                'risk': 'NONE',
                'explanation': 'Buffer configuration is optimal'
            }
            
    def analyze_all_failure_modes(
        self,
        cell_traffic: Dict[int, pd.Series],
        optimization_result: Dict
    ) -> Dict:
        """
        Run all failure mode detections.
        
        Args:
            cell_traffic: Dict of cell_id → traffic series
            optimization_result: Output from Layer 2 optimization
            
        Returns:
            Comprehensive failure mode analysis
        """
        results = {}
        
        # 1. Synchronized bursts
        results['synchronized_bursts'] = self.detect_synchronized_bursts(cell_traffic)
        
        # 2. URLLC traffic
        results['urllc_traffic'] = self.detect_urllc_traffic(
            optimization_result.get('simulation_stats', {})
        )
        
        # 3. Buffer misconfiguration
        sim_stats = optimization_result.get('simulation_stats', {})
        results['buffer_config'] = self.detect_buffer_misconfiguration(
            optimization_result.get('buffer_us', 143),
            sim_stats.get('max_occupancy_pct', 0)
        )
        
        # Aggregate risk level
        risk_levels = [r.get('risk', 'NONE') for r in results.values()]
        risk_priority = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'NONE': 0}
        max_risk = max(risk_levels, key=lambda r: risk_priority.get(r, 0))
        
        results['overall_risk'] = max_risk
        results['failure_modes_detected'] = sum(
            1 for r in results.values() if isinstance(r, dict) and r.get('detected', False)
        )
        
        return results
