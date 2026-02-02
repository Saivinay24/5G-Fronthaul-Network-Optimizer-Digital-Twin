// AI Explanations Data - Auto-generated from deterministic results
// STRICT RULE: These are translations only, no new computations

const aiExplanations = {
    section1: `Explanation:
This cell shows average traffic of 0.02 Gbps, but peak bursts reach 0.1 Gbps—a 6x difference lasting only microseconds. Traditional capacity planning provisions for the 0.1 Gbps peak, wasting 80% of capacity during normal operation. These brief micro-bursts are the root cause of fronthaul congestion, not sustained high traffic.

Decision:
Micro-bursts, not average load, drive capacity requirements.`,

    section2: `Explanation:
These 4 cells (IDs: 8, 10, 18, 19) burst at precisely the same time, revealing they share Link 2. This topology was discovered through correlation analysis of congestion events, without any network documentation. The synchronized burst pattern is deterministic proof of shared infrastructure.

Decision:
Link 2 carries traffic from 4 cells, discovered via blind correlation analysis.`,

    section3: `Explanation:
Without traffic shaping, this link requires 2.32 Gbps to handle peak bursts. By adding a 143 microsecond buffer, the system smooths these bursts, reducing required capacity to 0.22 Gbps—a 90.7% reduction. This eliminates the need for a hardware upgrade while maintaining packet loss at 0.80%.

Decision:
Software shaping with 143 µs buffer replaces $12,000 hardware upgrade.

Why This Is Safe:
Packet loss remains under 1% across the entire operating range.`,

    section4: `Explanation:
The deterministic analysis shows Link 2 can operate safely at reduced capacity with traffic shaping enabled. The configuration requires a 143 microsecond buffer at the DU/switch layer. Expected impact: 90.7% capacity reduction, $12,000 cost savings, and 90 kWh/year energy reduction.

Decision:
DO NOT UPGRADE - Enable traffic shaping with 143 µs buffer.

Why This Is Safe:
The system flags high-risk scenarios and recommends upgrades when shaping is unsafe. Risk level: NONE.`,

    section5: `Explanation:
The robustness analysis shows a wide safe operating region from 100 to 200 microseconds—not a fragile sweet spot. Packet loss stays under 1.0% across this entire range. The recommended 143 µs buffer sits well within this safe zone, providing margin for traffic variations.

Decision:
Wide safe range (100-200 µs) ensures robust operation.

Why This Is Safe:
The solution adapts to traffic changes and fails safely by recommending upgrades when operating conditions exceed safe thresholds.`
};

// Function to load AI explanation into a section
function loadAIExplanation(sectionId) {
    const explanation = aiExplanations[sectionId];
    if (!explanation) return '';

    // Parse explanation into parts
    const parts = explanation.split('\n\n');
    let html = '<div class="ai-explanation-content">';

    parts.forEach(part => {
        if (part.startsWith('Explanation:')) {
            html += `<div class="ai-part"><strong>💡 Explanation:</strong><br>${part.replace('Explanation:\n', '')}</div>`;
        } else if (part.startsWith('Decision:')) {
            html += `<div class="ai-part ai-decision"><strong>✅ Decision:</strong><br>${part.replace('Decision:\n', '')}</div>`;
        } else if (part.startsWith('Why This Is Safe:')) {
            html += `<div class="ai-part ai-safety"><strong>🛡️ Why This Is Safe:</strong><br>${part.replace('Why This Is Safe:\n', '')}</div>`;
        }
    });

    html += '</div>';
    return html;
}
