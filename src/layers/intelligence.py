"""
Layer 2: Deterministic Intelligence Layer

Responsibilities:
- Adaptive traffic shaping based on burstiness (PAPR)
- Dynamic buffer optimization (70-200 µs range)
- Leaky bucket simulation with time-domain precision
- Binary search for optimal capacity
- Maintain packet loss ≤ 1% constraint

CRITICAL: NO MACHINE LEARNING.
This layer uses deterministic algorithms with explainable logic.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.constants import (
    SYMBOL_DURATION_SEC, BUFFER_SIZE_US, MIN_BUFFER_US, MAX_BUFFER_US,
    PACKET_LOSS_LIMIT, PAPR_LOW, PAPR_MEDIUM, PAPR_HIGH
)


class AdaptiveShaper:
    """
    Adaptive traffic shaping engine that adjusts aggressiveness based on
    observed burstiness (PAPR).
    
    Shaping Modes:
    - Low PAPR (<10x): Minimal smoothing, low buffer
    - Medium PAPR (10-100x): Moderate smoothing, standard buffer
    - High PAPR (>100x): Aggressive smoothing, maximum buffer
    """
    
    def __init__(self):
        self.shaping_config = {}
        
    def determine_shaping_mode(self, papr: float) -> Dict:
        """
        Determine shaping aggressiveness based on PAPR.
        
        Args:
            papr: Peak-to-Average Power Ratio
            
        Returns:
            Configuration dict with mode, buffer size, and smoothing factor
        """
        if papr < PAPR_LOW:
            return {
                'mode': 'MINIMAL',
                'buffer_us': MIN_BUFFER_US,
                'smoothing_factor': 1.1,
                'description': 'Low burstiness - minimal shaping required'
            }
        elif papr < PAPR_MEDIUM:
            return {
                'mode': 'MODERATE',
                'buffer_us': BUFFER_SIZE_US,
                'smoothing_factor': 1.5,
                'description': 'Medium burstiness - standard shaping'
            }
        else:
            return {
                'mode': 'AGGRESSIVE',
                'buffer_us': MAX_BUFFER_US,
                'smoothing_factor': 2.0,
                'description': 'High burstiness - aggressive shaping'
            }
            
    def simulate_leaky_bucket(
        self,
        throughput_gbps: pd.Series,
        capacity_gbps: float,
        buffer_us: float = BUFFER_SIZE_US
    ) -> Tuple[float, Dict]:
        """
        Simulate leaky bucket traffic shaper with precise time-domain modeling.
        
        Args:
            throughput_gbps: Input traffic series (Gbps)
            capacity_gbps: Link capacity (Gbps)
            buffer_us: Buffer depth in microseconds
            
        Returns:
            (loss_ratio, statistics_dict)
        """
        # Convert to bits per symbol
        incoming_bits = throughput_gbps.values * 1e9 * SYMBOL_DURATION_SEC
        leak_bits = capacity_gbps * 1e9 * SYMBOL_DURATION_SEC
        
        # Buffer capacity in bits (dynamic based on link rate)
        max_buffer_bits = capacity_gbps * 1e9 * (buffer_us * 1e-6)
        
        # Simulation state
        current_buffer = 0.0
        total_loss_bits = 0.0
        total_input_bits = np.sum(incoming_bits)
        
        max_buffer_occupancy = 0.0
        buffer_overflow_count = 0
        
        if total_input_bits == 0:
            return 0.0, {'max_occupancy_pct': 0, 'overflow_events': 0}
            
        # Time-domain simulation
        for bits in incoming_bits:
            # Net flow: incoming - outgoing
            current_buffer += (bits - leak_bits)
            
            # Clamp to [0, max_buffer]
            if current_buffer < 0:
                current_buffer = 0
            elif current_buffer > max_buffer_bits:
                loss = current_buffer - max_buffer_bits
                total_loss_bits += loss
                current_buffer = max_buffer_bits
                buffer_overflow_count += 1
                
            # Track max occupancy
            max_buffer_occupancy = max(max_buffer_occupancy, current_buffer)
            
        loss_ratio = total_loss_bits / total_input_bits
        
        stats = {
            'loss_ratio': loss_ratio,
            'loss_pct': loss_ratio * 100,
            'max_occupancy_bits': max_buffer_occupancy,
            'max_occupancy_pct': (max_buffer_occupancy / max_buffer_bits * 100) if max_buffer_bits > 0 else 0,
            'overflow_events': buffer_overflow_count,
            'buffer_us': buffer_us,
            'capacity_gbps': capacity_gbps
        }
        
        return loss_ratio, stats
        
    def optimize_capacity(
        self,
        throughput_gbps: pd.Series,
        papr: float,
        loss_limit: float = PACKET_LOSS_LIMIT
    ) -> Dict:
        """
        Find optimal link capacity using adaptive shaping.
        
        Args:
            throughput_gbps: Traffic series
            papr: Peak-to-Average Power Ratio
            loss_limit: Maximum allowed packet loss (default 1%)
            
        Returns:
            Optimization results with capacity, buffer, and savings
        """
        # Determine shaping mode
        shaping_config = self.determine_shaping_mode(papr)
        buffer_us = shaping_config['buffer_us']
        
        # Baseline: no shaping (peak capacity required)
        peak_capacity = throughput_gbps.max()
        
        # Binary search for minimum capacity with shaping
        low = throughput_gbps.mean()
        high = peak_capacity
        optimal_capacity = high
        best_stats = None
        
        # Precision: 0.1 Gbps
        for _ in range(20):
            mid = (low + high) / 2
            loss_ratio, stats = self.simulate_leaky_bucket(
                throughput_gbps, mid, buffer_us
            )
            
            if loss_ratio <= loss_limit:
                optimal_capacity = mid
                best_stats = stats
                high = mid
            else:
                low = mid
                
        # Calculate savings
        capacity_reduction_pct = (1 - optimal_capacity / peak_capacity) * 100
        
        result = {
            'peak_capacity_gbps': peak_capacity,
            'optimal_capacity_gbps': optimal_capacity,
            'capacity_reduction_pct': capacity_reduction_pct,
            'shaping_mode': shaping_config['mode'],
            'buffer_us': buffer_us,
            'papr': papr,
            'simulation_stats': best_stats,
            'shaping_config': shaping_config
        }
        
        return result


class DeterministicRationale:
    """
    Documentation and justification for why deterministic logic is chosen
    over machine learning for this safety-critical application.
    """
    
    @staticmethod
    def get_rationale() -> Dict[str, str]:
        """
        Return structured rationale for deterministic approach.
        
        Returns:
            Dictionary with key decision factors
        """
        return {
            'safety_critical': (
                "Fronthaul networks carry time-sensitive 5G traffic with strict "
                "latency requirements (< 1ms). Any shaping decision must be "
                "deterministic and verifiable. ML models introduce unpredictability "
                "that is unacceptable in safety-critical transport."
            ),
            'explainability': (
                "Network operators must understand WHY a shaping decision was made. "
                "Deterministic algorithms (leaky bucket, binary search) provide "
                "complete transparency. ML 'black boxes' cannot explain individual "
                "decisions to regulators or during incident analysis."
            ),
            'deterministic_guarantees': (
                "We can mathematically prove that our shaping algorithm maintains "
                "packet loss ≤ 1% under specified conditions. ML models provide "
                "probabilistic outputs without hard guarantees, which is insufficient "
                "for SLA compliance."
            ),
            'deployment_simplicity': (
                "Deterministic logic runs on any standard CPU without GPU acceleration, "
                "model versioning, or retraining pipelines. This reduces operational "
                "complexity and eliminates model drift risks."
            ),
            'regulatory_compliance': (
                "Telecom regulators require auditable decision-making for QoS. "
                "Deterministic algorithms can be formally verified and certified. "
                "ML models face regulatory barriers in safety-critical infrastructure."
            ),
            'real_time_performance': (
                "Leaky bucket simulation runs in O(N) time with predictable latency. "
                "ML inference introduces variable latency and potential tail latencies "
                "that could violate real-time constraints."
            )
        }
        
    @staticmethod
    def print_rationale() -> None:
        """Print human-readable rationale."""
        rationale = DeterministicRationale.get_rationale()
        
        print("\n" + "="*70)
        print("WHY DETERMINISTIC LOGIC INSTEAD OF MACHINE LEARNING?")
        print("="*70)
        
        for i, (key, explanation) in enumerate(rationale.items(), 1):
            title = key.replace('_', ' ').title()
            print(f"\n{i}. {title}")
            print(f"   {explanation}")
            
        print("\n" + "="*70)
        print("CONCLUSION: Deterministic algorithms provide the safety, explainability,")
        print("and regulatory compliance required for production fronthaul networks.")
        print("="*70 + "\n")
