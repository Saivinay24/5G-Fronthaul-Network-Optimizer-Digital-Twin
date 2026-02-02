"""
Layer 5: Impact & Sustainability Layer

Responsibilities:
- Quantify hardware cost avoidance
- Estimate energy savings (optics + switching + cooling)
- Calculate carbon impact (CO2 equivalent)
- Provide business case metrics for operators

Output: Clear ROI and sustainability benefits
"""

import sys
import os
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.constants import (
    OPTIC_COST, OPTIC_POWER_W, KG_CO2_PER_KWH, HOURS_PER_YEAR, LINK_RATES
)


class SustainabilityAnalyzer:
    """
    Calculate cost, energy, and carbon impact of optimization decisions.
    """
    
    def __init__(self):
        pass
        
    def determine_required_optic(self, capacity_gbps: float) -> str:
        """
        Determine minimum optic rate required for given capacity.
        
        Args:
            capacity_gbps: Required link capacity
            
        Returns:
            Optic rate string (e.g., '25G')
        """
        # Add 10% headroom for safety
        required = capacity_gbps * 1.1
        
        for rate_name in ['10G', '25G', '40G', '100G']:
            if LINK_RATES[rate_name] >= required:
                return rate_name
                
        return '100G'
        
    def calculate_hardware_savings(
        self,
        peak_capacity_gbps: float,
        optimal_capacity_gbps: float
    ) -> Dict:
        """
        Calculate avoided hardware costs.
        
        Args:
            peak_capacity_gbps: Capacity without shaping
            optimal_capacity_gbps: Capacity with shaping
            
        Returns:
            Hardware cost analysis
        """
        optic_without_shaping = self.determine_required_optic(peak_capacity_gbps)
        optic_with_shaping = self.determine_required_optic(optimal_capacity_gbps)
        
        cost_without = OPTIC_COST[optic_without_shaping]
        cost_with = OPTIC_COST[optic_with_shaping]
        savings = cost_without - cost_with
        
        return {
            'optic_without_shaping': optic_without_shaping,
            'optic_with_shaping': optic_with_shaping,
            'cost_without_usd': cost_without,
            'cost_with_usd': cost_with,
            'savings_usd': savings,
            'savings_pct': (savings / cost_without * 100) if cost_without > 0 else 0,
            'upgrade_avoided': optic_without_shaping != optic_with_shaping
        }
        
    def calculate_energy_impact(
        self,
        peak_capacity_gbps: float,
        optimal_capacity_gbps: float
    ) -> Dict:
        """
        Calculate energy savings from lower-rate optics.
        
        Args:
            peak_capacity_gbps: Capacity without shaping
            optimal_capacity_gbps: Capacity with shaping
            
        Returns:
            Energy impact analysis
        """
        optic_without = self.determine_required_optic(peak_capacity_gbps)
        optic_with = self.determine_required_optic(optimal_capacity_gbps)
        
        power_without_w = OPTIC_POWER_W[optic_without]
        power_with_w = OPTIC_POWER_W[optic_with]
        power_savings_w = power_without_w - power_with_w
        
        # Annual energy savings
        annual_kwh = (power_savings_w / 1000) * HOURS_PER_YEAR
        
        return {
            'optic_without': optic_without,
            'optic_with': optic_with,
            'power_without_w': power_without_w,
            'power_with_w': power_with_w,
            'power_savings_w': power_savings_w,
            'annual_energy_kwh': annual_kwh,
            'annual_energy_savings_pct': (power_savings_w / power_without_w * 100) if power_without_w > 0 else 0
        }
        
    def calculate_carbon_impact(
        self,
        energy_impact: Dict
    ) -> Dict:
        """
        Calculate carbon footprint reduction.
        
        Args:
            energy_impact: Output from calculate_energy_impact()
            
        Returns:
            Carbon impact analysis
        """
        annual_kwh = energy_impact['annual_energy_kwh']
        annual_co2_kg = annual_kwh * KG_CO2_PER_KWH
        
        return {
            'annual_co2_reduction_kg': annual_co2_kg,
            'annual_co2_reduction_tons': annual_co2_kg / 1000,
            'co2_intensity_kg_per_kwh': KG_CO2_PER_KWH
        }
        
    def analyze_link_sustainability(
        self,
        link_id: int,
        optimization_result: Dict
    ) -> Dict:
        """
        Comprehensive sustainability analysis for a single link.
        
        Args:
            link_id: Link identifier
            optimization_result: Output from Layer 2
            
        Returns:
            Complete sustainability metrics
        """
        peak_capacity = optimization_result['peak_capacity_gbps']
        optimal_capacity = optimization_result['optimal_capacity_gbps']
        
        hardware = self.calculate_hardware_savings(peak_capacity, optimal_capacity)
        energy = self.calculate_energy_impact(peak_capacity, optimal_capacity)
        carbon = self.calculate_carbon_impact(energy)
        
        return {
            'link_id': link_id,
            'hardware_savings': hardware,
            'energy_impact': energy,
            'carbon_impact': carbon
        }
        
    def format_sustainability_report(self, analysis: Dict) -> str:
        """
        Format sustainability analysis as human-readable report.
        
        Args:
            analysis: Output from analyze_link_sustainability()
            
        Returns:
            Formatted string report
        """
        link_id = analysis['link_id']
        hw = analysis['hardware_savings']
        energy = analysis['energy_impact']
        carbon = analysis['carbon_impact']
        
        report = f"\n{'='*70}\n"
        report += f"SUSTAINABILITY IMPACT - LINK {link_id}\n"
        report += f"{'='*70}\n\n"
        
        # Hardware savings
        report += "💰 HARDWARE COST AVOIDANCE:\n"
        if hw['upgrade_avoided']:
            report += f"   ├─ Without Shaping: {hw['optic_without_shaping']} optic (${hw['cost_without_usd']:,})\n"
            report += f"   ├─ With Shaping:    {hw['optic_with_shaping']} optic (${hw['cost_with_usd']:,})\n"
            report += f"   └─ SAVINGS:         ${hw['savings_usd']:,} ({hw['savings_pct']:.1f}% reduction)\n"
        else:
            report += f"   └─ No upgrade required (already using {hw['optic_with_shaping']})\n"
        report += "\n"
        
        # Energy savings
        report += "⚡ ENERGY IMPACT:\n"
        report += f"   ├─ Power Savings:   {energy['power_savings_w']:.1f} W per link\n"
        report += f"   ├─ Annual Energy:   {energy['annual_energy_kwh']:.1f} kWh saved\n"
        report += f"   └─ Reduction:       {energy['annual_energy_savings_pct']:.1f}%\n\n"
        
        # Carbon impact
        report += "🌍 CARBON FOOTPRINT:\n"
        report += f"   ├─ Annual CO₂ Reduction: {carbon['annual_co2_reduction_kg']:.1f} kg CO₂e\n"
        report += f"   └─ Equivalent to:        {carbon['annual_co2_reduction_tons']:.3f} tons CO₂e/year\n"
        
        report += f"\n{'='*70}\n"
        
        return report
        
    def aggregate_network_impact(
        self,
        link_analyses: Dict[int, Dict]
    ) -> Dict:
        """
        Aggregate sustainability impact across all links.
        
        Args:
            link_analyses: Dict of link_id → sustainability analysis
            
        Returns:
            Network-wide sustainability metrics
        """
        total_hw_savings = sum(
            a['hardware_savings']['savings_usd'] 
            for a in link_analyses.values()
        )
        
        total_energy_kwh = sum(
            a['energy_impact']['annual_energy_kwh']
            for a in link_analyses.values()
        )
        
        total_co2_kg = sum(
            a['carbon_impact']['annual_co2_reduction_kg']
            for a in link_analyses.values()
        )
        
        return {
            'num_links': len(link_analyses),
            'total_hardware_savings_usd': total_hw_savings,
            'total_annual_energy_kwh': total_energy_kwh,
            'total_annual_co2_kg': total_co2_kg,
            'total_annual_co2_tons': total_co2_kg / 1000
        }
