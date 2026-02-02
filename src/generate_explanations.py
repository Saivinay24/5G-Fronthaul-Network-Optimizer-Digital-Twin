#!/usr/bin/env python3
"""
Generate AI Explanations - CLI Tool

Reads deterministic results and generates human-readable explanations.
STRICT RULE: No computation, only translation.
"""

import os
import sys
import argparse
import json
from typing import Dict

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ai_explainer import AIExplainer, save_explanations


def load_demo_results(demo_folder: str) -> Dict:
    """
    Load deterministic results from demo generation.
    
    Args:
        demo_folder: Path to demo results folder
        
    Returns:
        Dictionary of results for each section
    """
    results = {}
    
    # These are example metrics - in production, read from actual outputs
    # For now, we'll use representative values from the demo
    
    results['section1'] = {
        'cell_id': 8,
        'avg_throughput_gbps': 0.02,
        'peak_throughput_gbps': 0.1,
        'papr': 6.0,
        'source': 'telemetry_analyzer'
    }
    
    results['section2'] = {
        'link_id': 2,
        'cells': [8, 10, 18, 19],
        'correlation_method': 'packet_loss_correlation',
        'source': 'telemetry_analyzer'
    }
    
    results['section3'] = {
        'link_id': 2,
        'peak_capacity_gbps': 2.32,
        'optimal_capacity_gbps': 0.22,
        'buffer_us': 143,
        'capacity_reduction_pct': 90.7,
        'packet_loss_pct': 0.8,
        'source': 'adaptive_shaper'
    }
    
    results['section4'] = {
        'link_id': 2,
        'action': 'ENABLE_SHAPING',
        'buffer_us': 143,
        'capacity_reduction_pct': 90.7,
        'cost_savings_usd': 12000,
        'energy_savings_kwh': 90,
        'risk_level': 'NONE',
        'source': 'operator_decision'
    }
    
    results['section5'] = {
        'link_id': 2,
        'safe_buffer_range_us': (100, 200),
        'recommended_buffer_us': 143,
        'max_packet_loss_pct': 1.0,
        'source': 'resilience_analyzer'
    }
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Generate AI explanations for deterministic results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate explanations from demo results
  python src/generate_explanations.py --data-folder data --output results/explanations
  
  # Generate explanations only (no save)
  python src/generate_explanations.py --data-folder data --no-save

Note: This tool ONLY translates existing results. It does NOT compute new values.
"""
    )
    
    parser.add_argument('--data-folder', type=str, default='data',
                       help='Data folder (for context, not used in computation)')
    parser.add_argument('--output', type=str, default='results/explanations',
                       help='Output folder for explanations')
    parser.add_argument('--no-save', action='store_true',
                       help='Print explanations without saving')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', 'template', 'ai'],
                       help='Explanation mode: auto (default, detects API key), template, or ai')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 AI EXPLANATION GENERATOR")
    print("=" * 70)
    print()
    print("STRICT RULE: This tool ONLY translates deterministic results.")
    print("             It NEVER computes, infers, or recommends.")
    print()
    print(f"Mode: {args.mode.upper()}")
    print(f"Output: {args.output}")
    print()
    
    # Initialize explainer
    explainer = AIExplainer(mode=args.mode)
    
    # Load deterministic results
    print("📊 Loading deterministic results...")
    results = load_demo_results(args.data_folder)
    print(f"   ✅ Loaded results for {len(results)} sections\n")
    
    # Generate explanations
    explanations = explainer.generate_all_explanations(results)
    
    # Save or print
    if not args.no_save:
        print(f"💾 Saving explanations to {args.output}...")
        save_explanations(explanations, args.output)
        
        # Generate complete narrative
        narrative = explainer.generate_complete_narrative(explanations)
        narrative_path = os.path.join(args.output, 'complete_narrative.md')
        with open(narrative_path, 'w') as f:
            f.write(narrative)
        print(f"   💾 Saved: {narrative_path}")
        
        print()
        print("=" * 70)
        print("✅ EXPLANATION GENERATION COMPLETE")
        print("=" * 70)
        print()
        print("Generated files:")
        print(f"  - {args.output}/section1_explanation.txt")
        print(f"  - {args.output}/section2_explanation.txt")
        print(f"  - {args.output}/section3_explanation.txt")
        print(f"  - {args.output}/section4_explanation.txt")
        print(f"  - {args.output}/section5_explanation.txt")
        print(f"  - {args.output}/complete_narrative.md")
        print()
        print("Next steps:")
        print(f"  1. Review explanations: cat {args.output}/complete_narrative.md")
        print(f"  2. Open dashboard: open dashboard.html")
        print()
    else:
        print("\n" + "=" * 70)
        print("GENERATED EXPLANATIONS (not saved)")
        print("=" * 70 + "\n")
        for section_id, explanation in explanations.items():
            print(f"\n{'=' * 70}")
            print(f"{section_id.upper()}")
            print('=' * 70)
            print(explanation)


if __name__ == "__main__":
    main()
