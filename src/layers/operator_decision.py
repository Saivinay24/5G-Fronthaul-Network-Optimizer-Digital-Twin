"""
Layer 4: Operator Decision Layer

Responsibilities:
- Transform technical analytics into actionable operator decisions
- Generate human-readable recommendations
- Provide clear upgrade/no-upgrade guidance
- Format output for network operations teams

CRITICAL: Every output must answer "What should the operator do?"
"""

import pandas as pd
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.constants import LINK_RATES


class OperatorDecisionEngine:
    """
    Translates technical analysis into operator-facing recommendations.
    """
    
    def __init__(self):
        self.recommendations = {}
        
    def determine_current_link_rate(self, peak_gbps: float) -> str:
        """
        Infer current link rate based on peak traffic.
        
        Args:
            peak_gbps: Peak observed traffic
            
        Returns:
            Link rate string (e.g., '25G')
        """
        # Assume link is sized for peak + some headroom
        required = peak_gbps * 1.1  # 10% headroom
        
        for rate_name in ['10G', '25G', '40G', '100G']:
            if LINK_RATES[rate_name] >= required:
                return rate_name
                
        return '100G'
        
    def recommend_action(
        self,
        link_id: int,
        optimization_result: Dict,
        resilience_analysis: Dict
    ) -> Dict:
        """
        Generate operator recommendation based on analysis.
        
        Args:
            link_id: Link identifier
            optimization_result: Output from Layer 2
            resilience_analysis: Output from Layer 3
            
        Returns:
            Structured recommendation with action, rationale, and metrics
        """
        peak_capacity = optimization_result['peak_capacity_gbps']
        optimal_capacity = optimization_result['optimal_capacity_gbps']
        reduction_pct = optimization_result['capacity_reduction_pct']
        buffer_us = optimization_result['buffer_us']
        shaping_mode = optimization_result['shaping_mode']
        
        current_rate = self.determine_current_link_rate(peak_capacity)
        overall_risk = resilience_analysis.get('overall_risk', 'NONE')
        
        # Decision logic
        recommendation = {
            'link_id': link_id,
            'current_peak_gbps': peak_capacity,
            'optimal_capacity_gbps': optimal_capacity,
            'capacity_reduction_pct': reduction_pct,
            'buffer_required_us': buffer_us,
            'current_link_rate': current_rate,
            'shaping_mode': shaping_mode,
            'risk_level': overall_risk
        }
        
        # Determine action based on risk and capacity
        if overall_risk == 'CRITICAL':
            # URLLC or critical failure mode
            recommendation['action'] = 'UPGRADE_REQUIRED'
            recommendation['recommendation'] = (
                f"⚠️  UPGRADE REQUIRED due to {overall_risk} risk. "
                "Shaping cannot be safely deployed."
            )
            recommendation['next_steps'] = [
                "Review failure mode analysis",
                "Plan link capacity upgrade",
                "Consider traffic segregation (URLLC vs eMBB)"
            ]
            
        elif overall_risk == 'HIGH':
            # High risk but potentially manageable
            recommendation['action'] = 'CONDITIONAL_SHAPING'
            recommendation['recommendation'] = (
                f"⚠️  CONDITIONAL: Enable shaping with {buffer_us} µs buffer, "
                "but monitor closely due to HIGH risk factors."
            )
            recommendation['next_steps'] = [
                "Deploy shaping in monitoring mode first",
                "Address failure modes from resilience analysis",
                "Prepare upgrade plan as fallback"
            ]
            
        elif reduction_pct > 50:
            # Shaping provides significant benefit
            recommendation['action'] = 'ENABLE_SHAPING'
            recommendation['recommendation'] = (
                f"✅ DO NOT upgrade fiber. Enable shaping with {buffer_us} µs buffer.\n"
                f"   Savings: {reduction_pct:.1f}% capacity reduction "
                f"({peak_capacity:.2f} → {optimal_capacity:.2f} Gbps)"
            )
            recommendation['next_steps'] = [
                f"Configure {shaping_mode} shaping mode",
                f"Set buffer depth to {buffer_us} µs",
                "Monitor packet loss (target < 1%)",
                "Validate QoS metrics post-deployment"
            ]
            
        else:
            # Marginal benefit from shaping
            recommendation['action'] = 'UPGRADE_RECOMMENDED'
            recommendation['recommendation'] = (
                f"⚡ Shaping provides minimal benefit ({reduction_pct:.1f}% reduction). "
                "Consider upgrading link capacity instead."
            )
            recommendation['next_steps'] = [
                "Evaluate cost of link upgrade vs shaping complexity",
                "If cost-sensitive, deploy shaping as interim solution"
            ]
            
        return recommendation
        
    def format_operator_report(self, recommendation: Dict) -> str:
        """
        Format recommendation as human-readable operator report.
        
        Args:
            recommendation: Output from recommend_action()
            
        Returns:
            Formatted string report
        """
        link_id = recommendation['link_id']
        
        report = f"\n{'='*70}\n"
        report += f"LINK {link_id} ANALYSIS & RECOMMENDATION\n"
        report += f"{'='*70}\n\n"
        
        # Metrics
        report += "📊 TRAFFIC METRICS:\n"
        report += f"   ├─ Current Peak Load:     {recommendation['current_peak_gbps']:.2f} Gbps\n"
        report += f"   ├─ Optimal Capacity:      {recommendation['optimal_capacity_gbps']:.2f} Gbps\n"
        report += f"   ├─ Capacity Reduction:    {recommendation['capacity_reduction_pct']:.1f}%\n"
        report += f"   ├─ Buffer Required:       {recommendation['buffer_required_us']} µs\n"
        report += f"   ├─ Current Link Rate:     {recommendation['current_link_rate']}\n"
        report += f"   ├─ Shaping Mode:          {recommendation['shaping_mode']}\n"
        report += f"   └─ Risk Level:            {recommendation['risk_level']}\n\n"
        
        # Recommendation
        report += "💡 RECOMMENDATION:\n"
        report += f"   {recommendation['recommendation']}\n\n"
        
        # Next steps
        report += "📋 NEXT STEPS:\n"
        for i, step in enumerate(recommendation['next_steps'], 1):
            report += f"   {i}. {step}\n"
            
        report += f"\n{'='*70}\n"
        
        return report
        
    def generate_all_recommendations(
        self,
        optimization_results: Dict[int, Dict],
        resilience_analyses: Dict[int, Dict]
    ) -> Dict[int, Dict]:
        """
        Generate recommendations for all links.
        
        Args:
            optimization_results: Dict of link_id → optimization result
            resilience_analyses: Dict of link_id → resilience analysis
            
        Returns:
            Dict of link_id → recommendation
        """
        recommendations = {}
        
        for link_id in optimization_results.keys():
            opt_result = optimization_results[link_id]
            res_analysis = resilience_analyses.get(link_id, {})
            
            recommendations[link_id] = self.recommend_action(
                link_id, opt_result, res_analysis
            )
            
        return recommendations
