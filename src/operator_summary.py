"""
Operator Summary Generator

Creates operator-facing summaries with clear, actionable decisions.
Designed for 10-second scanning by network planning engineers.

Usage:
    from operator_summary import OperatorSummaryGenerator
    
    generator = OperatorSummaryGenerator(recommendations, sustainability_analyses)
    generator.generate_markdown_summary('results/OPERATOR_SUMMARY.md')
    generator.generate_html_summary('results/OPERATOR_SUMMARY.html')
"""

from typing import Dict, List
import os
from datetime import datetime


class OperatorSummaryGenerator:
    """
    Generate operator-focused summaries with clear decision indicators.
    """
    
    def __init__(
        self,
        recommendations: Dict[int, Dict],
        sustainability_analyses: Dict[int, Dict] = None
    ):
        """
        Initialize summary generator.
        
        Args:
            recommendations: Dict of link_id → recommendation from OperatorDecisionEngine
            sustainability_analyses: Optional dict of link_id → sustainability analysis
        """
        self.recommendations = recommendations
        self.sustainability = sustainability_analyses or {}
        
    def _get_risk_emoji(self, risk_level: str) -> str:
        """Get emoji for risk level."""
        risk_map = {
            'NONE': '✅',
            'LOW': '⚠️',
            'MEDIUM': '⚠️',
            'HIGH': '🔴',
            'CRITICAL': '🔴'
        }
        return risk_map.get(risk_level, '❓')
        
    def _get_decision_badge(self, action: str) -> str:
        """Get decision badge text."""
        badge_map = {
            'ENABLE_SHAPING': '✅ NO UPGRADE REQUIRED',
            'CONDITIONAL_SHAPING': '⚠️ MONITOR REQUIRED',
            'UPGRADE_REQUIRED': '🔴 UPGRADE REQUIRED',
            'UPGRADE_RECOMMENDED': '⚡ UPGRADE RECOMMENDED'
        }
        return badge_map.get(action, action)
        
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color for risk level (HTML)."""
        color_map = {
            'NONE': '#27ae60',
            'LOW': '#f39c12',
            'MEDIUM': '#e67e22',
            'HIGH': '#e74c3c',
            'CRITICAL': '#c0392b'
        }
        return color_map.get(risk_level, '#95a5a6')
        
    def generate_cli_summary(self) -> str:
        """
        Generate CLI-friendly summary.
        
        Returns:
            Formatted string for terminal output
        """
        output = []
        output.append("\n" + "="*80)
        output.append("OPERATOR SUMMARY - FRONTHAUL LINK DECISIONS")
        output.append("="*80 + "\n")
        
        # Sort by link ID
        sorted_links = sorted(self.recommendations.items())
        
        for link_id, rec in sorted_links:
            risk_emoji = self._get_risk_emoji(rec['risk_level'])
            decision = self._get_decision_badge(rec['action'])
            
            output.append(f"Link {link_id}: {decision}")
            output.append(f"  Risk Level: {risk_emoji} {rec['risk_level']}")
            output.append(f"  Current Peak: {rec['current_peak_gbps']:.2f} Gbps")
            output.append(f"  Optimal Capacity: {rec['optimal_capacity_gbps']:.2f} Gbps")
            output.append(f"  Reduction: {rec['capacity_reduction_pct']:.1f}%")
            
            if rec['action'] == 'ENABLE_SHAPING':
                output.append(f"  → Enable shaping with {rec['buffer_required_us']} µs buffer")
                if link_id in self.sustainability:
                    sus = self.sustainability[link_id]
                    output.append(f"  → Cost savings: ${sus['hardware_savings']['savings_usd']:,}")
            elif rec['action'] in ['UPGRADE_REQUIRED', 'UPGRADE_RECOMMENDED']:
                output.append(f"  → Plan capacity upgrade to {rec['current_link_rate']}")
            
            output.append("")
            
        output.append("="*80 + "\n")
        return "\n".join(output)
        
    def generate_markdown_summary(self, output_path: str) -> None:
        """
        Generate Markdown summary report.
        
        Args:
            output_path: Path to save Markdown file
        """
        lines = []
        lines.append("# Fronthaul Network Operator Summary")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n**Total Links Analyzed:** {len(self.recommendations)}\n")
        
        # Executive summary
        lines.append("## Executive Summary\n")
        
        no_upgrade = sum(1 for r in self.recommendations.values() if r['action'] == 'ENABLE_SHAPING')
        monitor = sum(1 for r in self.recommendations.values() if r['action'] == 'CONDITIONAL_SHAPING')
        upgrade = sum(1 for r in self.recommendations.values() if r['action'] in ['UPGRADE_REQUIRED', 'UPGRADE_RECOMMENDED'])
        
        lines.append(f"- ✅ **No Upgrade Required:** {no_upgrade} links")
        lines.append(f"- ⚠️ **Monitor Required:** {monitor} links")
        lines.append(f"- 🔴 **Upgrade Required:** {upgrade} links\n")
        
        if self.sustainability:
            total_savings = sum(s['hardware_savings']['savings_usd'] 
                              for s in self.sustainability.values())
            total_energy = sum(s['energy_impact']['annual_energy_kwh'] 
                             for s in self.sustainability.values())
            
            lines.append("### Network-Wide Impact\n")
            lines.append(f"- **Hardware Cost Avoidance:** ${total_savings:,}")
            lines.append(f"- **Annual Energy Savings:** {total_energy:.1f} kWh/year\n")
        
        # Link-by-link decisions
        lines.append("---\n")
        lines.append("## Link-by-Link Decisions\n")
        
        sorted_links = sorted(self.recommendations.items())
        
        for link_id, rec in sorted_links:
            risk_emoji = self._get_risk_emoji(rec['risk_level'])
            decision = self._get_decision_badge(rec['action'])
            
            lines.append(f"### Link {link_id}: {decision}\n")
            
            # Metrics table
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Current Peak Capacity | {rec['current_peak_gbps']:.2f} Gbps |")
            lines.append(f"| Required Capacity (Optimized) | {rec['optimal_capacity_gbps']:.2f} Gbps |")
            lines.append(f"| Capacity Reduction | {rec['capacity_reduction_pct']:.1f}% |")
            lines.append(f"| Buffer Size | {rec['buffer_required_us']} µs |")
            lines.append(f"| Risk Level | {risk_emoji} {rec['risk_level']} |")
            lines.append(f"| Current Link Rate | {rec['current_link_rate']} |\n")
            
            # Recommendation
            if rec['action'] == 'ENABLE_SHAPING':
                lines.append("> [!NOTE]")
                lines.append("> **Recommendation:** Enable traffic shaping - no hardware upgrade needed.")
                lines.append(f"> Configure {rec['shaping_mode']} shaping with {rec['buffer_required_us']} µs buffer.")
                
                if link_id in self.sustainability:
                    sus = self.sustainability[link_id]
                    lines.append(f"> **Cost Savings:** ${sus['hardware_savings']['savings_usd']:,}")
                    lines.append(f"> **Energy Savings:** {sus['energy_impact']['annual_energy_kwh']:.1f} kWh/year")
                    
            elif rec['action'] == 'CONDITIONAL_SHAPING':
                lines.append("> [!WARNING]")
                lines.append("> **Recommendation:** Deploy shaping with close monitoring.")
                lines.append("> Address identified risk factors before full deployment.")
                
            elif rec['action'] in ['UPGRADE_REQUIRED', 'UPGRADE_RECOMMENDED']:
                lines.append("> [!CAUTION]")
                lines.append("> **Recommendation:** Plan link capacity upgrade.")
                lines.append("> Shaping alone cannot safely meet requirements.")
            
            lines.append("")
            
            # Next steps
            lines.append("**Next Steps:**")
            for i, step in enumerate(rec['next_steps'], 1):
                lines.append(f"{i}. {step}")
            
            lines.append("\n---\n")
        
        # Save to file
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
            
        print(f"✅ Operator summary saved to: {output_path}")
        
    def generate_html_summary(self, output_path: str) -> None:
        """
        Generate HTML summary report with styling.
        
        Args:
            output_path: Path to save HTML file
        """
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("  <title>Fronthaul Network Operator Summary</title>")
        html.append("  <style>")
        html.append("""
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background: #f5f5f5;
    }
    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; margin-top: 30px; }
    .summary-box {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin: 20px 0;
    }
    .link-card {
      background: white;
      padding: 20px;
      margin: 15px 0;
      border-radius: 8px;
      border-left: 5px solid #3498db;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .decision-badge {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 20px;
      font-weight: bold;
      margin: 10px 0;
    }
    .badge-green { background: #27ae60; color: white; }
    .badge-yellow { background: #f39c12; color: white; }
    .badge-red { background: #e74c3c; color: white; }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin: 15px 0;
    }
    .metric-box {
      background: #ecf0f1;
      padding: 15px;
      border-radius: 5px;
      text-align: center;
    }
    .metric-label { font-size: 0.9em; color: #7f8c8d; }
    .metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
    .next-steps { background: #e8f4f8; padding: 15px; border-radius: 5px; margin-top: 15px; }
    .risk-indicator {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      margin-right: 5px;
    }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background: #3498db; color: white; }
        """)
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        
        html.append("  <h1>🌐 Fronthaul Network Operator Summary</h1>")
        html.append(f"  <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        # Executive summary
        html.append("  <div class='summary-box'>")
        html.append("    <h2>Executive Summary</h2>")
        
        no_upgrade = sum(1 for r in self.recommendations.values() if r['action'] == 'ENABLE_SHAPING')
        monitor = sum(1 for r in self.recommendations.values() if r['action'] == 'CONDITIONAL_SHAPING')
        upgrade = sum(1 for r in self.recommendations.values() if r['action'] in ['UPGRADE_REQUIRED', 'UPGRADE_RECOMMENDED'])
        
        html.append("    <div class='metrics-grid'>")
        html.append("      <div class='metric-box'>")
        html.append("        <div class='metric-label'>No Upgrade Required</div>")
        html.append(f"       <div class='metric-value' style='color: #27ae60;'>✅ {no_upgrade}</div>")
        html.append("      </div>")
        html.append("      <div class='metric-box'>")
        html.append("        <div class='metric-label'>Monitor Required</div>")
        html.append(f"       <div class='metric-value' style='color: #f39c12;'>⚠️ {monitor}</div>")
        html.append("      </div>")
        html.append("      <div class='metric-box'>")
        html.append("        <div class='metric-label'>Upgrade Required</div>")
        html.append(f"       <div class='metric-value' style='color: #e74c3c;'>🔴 {upgrade}</div>")
        html.append("      </div>")
        html.append("    </div>")
        
        if self.sustainability:
            total_savings = sum(s['hardware_savings']['savings_usd'] 
                              for s in self.sustainability.values())
            total_energy = sum(s['energy_impact']['annual_energy_kwh'] 
                             for s in self.sustainability.values())
            
            html.append("    <h3>Network-Wide Impact</h3>")
            html.append("    <div class='metrics-grid'>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Hardware Cost Avoidance</div>")
            html.append(f"       <div class='metric-value'>${total_savings:,}</div>")
            html.append("      </div>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Annual Energy Savings</div>")
            html.append(f"       <div class='metric-value'>{total_energy:.1f} kWh</div>")
            html.append("      </div>")
            html.append("    </div>")
        
        html.append("  </div>")
        
        # Link-by-link cards
        html.append("  <h2>Link-by-Link Decisions</h2>")
        
        sorted_links = sorted(self.recommendations.items())
        
        for link_id, rec in sorted_links:
            badge_class = 'badge-green' if rec['action'] == 'ENABLE_SHAPING' else \
                         'badge-yellow' if rec['action'] == 'CONDITIONAL_SHAPING' else 'badge-red'
            decision = self._get_decision_badge(rec['action'])
            risk_color = self._get_risk_color(rec['risk_level'])
            
            html.append("  <div class='link-card'>")
            html.append(f"   <h3>Link {link_id}</h3>")
            html.append(f"   <span class='decision-badge {badge_class}'>{decision}</span>")
            
            html.append("    <div class='metrics-grid'>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Current Peak</div>")
            html.append(f"       <div class='metric-value'>{rec['current_peak_gbps']:.2f} Gbps</div>")
            html.append("      </div>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Optimal Capacity</div>")
            html.append(f"       <div class='metric-value'>{rec['optimal_capacity_gbps']:.2f} Gbps</div>")
            html.append("      </div>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Reduction</div>")
            html.append(f"       <div class='metric-value' style='color: #27ae60;'>{rec['capacity_reduction_pct']:.1f}%</div>")
            html.append("      </div>")
            html.append("      <div class='metric-box'>")
            html.append("        <div class='metric-label'>Risk Level</div>")
            html.append(f"       <div class='metric-value'><span class='risk-indicator' style='background: {risk_color};'></span>{rec['risk_level']}</div>")
            html.append("      </div>")
            html.append("    </div>")
            
            html.append("    <div class='next-steps'>")
            html.append("      <strong>Next Steps:</strong>")
            html.append("      <ol>")
            for step in rec['next_steps']:
                html.append(f"       <li>{step}</li>")
            html.append("      </ol>")
            html.append("    </div>")
            
            html.append("  </div>")
        
        html.append("</body>")
        html.append("</html>")
        
        # Save to file
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(html))
            
        print(f"✅ HTML summary saved to: {output_path}")


if __name__ == '__main__':
    print("Operator Summary Generator - Use via import")
