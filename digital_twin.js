/**
 * O-RAN Fronthaul Digital Twin Engine
 * 
 * Core JavaScript engine for the digital twin interface.
 * Handles data loading, topology visualization, time control, and real-time updates.
 */

// ===================================
// GLOBAL STATE
// ===================================

const DigitalTwin = {
    // Data
    data: null,
    currentSlot: 0,
    totalSlots: 0,
    selectedLink: null,

    // Playback
    isPlaying: false,
    playbackSpeed: 1,
    playbackInterval: null,

    // Canvas contexts
    canvases: {
        topology: null,
        baseline: null,
        optimized: null,
        rateTrace: null
    },

    // Topology state
    topology: {
        nodes: [],
        edges: [],
        confidence: 0,
        stage: 'A', // 'A' (Observation), 'B' (Correlation), 'C' (Inference)
        simulation: null // For force-directed graph in Stage B
    },

    // Physics State
    particles: {
        baseline: [],
        optimized: []
    },

    // Intelligence mode
    intelligenceEnabled: false
};


// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Digital Twin Interface...');

    // Initialize canvases
    initializeCanvases();

    // Load data
    await loadDigitalTwinData();

    // Setup event listeners
    setupEventListeners();

    // Start initial render
    render();

    console.log('✅ Digital Twin Interface Ready');
});

function initializeCanvases() {
    DigitalTwin.canvases.topology = document.getElementById('topologyCanvas').getContext('2d');
    DigitalTwin.canvases.baseline = document.getElementById('baselineCanvas').getContext('2d');
    DigitalTwin.canvases.optimized = document.getElementById('optimizedCanvas').getContext('2d');
    DigitalTwin.canvases.rateTrace = document.getElementById('rateTraceCanvas').getContext('2d');
}

async function loadDigitalTwinData() {
    try {
        const response = await fetch('results/digital_twin_data.json');
        if (!response.ok) {
            throw new Error('Failed to load digital twin data');
        }

        DigitalTwin.data = await response.json();
        console.log('📊 Digital Twin Data Loaded:', DigitalTwin.data);

        // Initialize state from data
        initializeFromData();

    } catch (error) {
        console.error('❌ Error loading data:', error);
        showErrorMessage('Failed to load digital twin data. Please run: python src/export_digital_twin_data.py');
    }
}

function initializeFromData() {
    if (!DigitalTwin.data) return;

    // Set total slots
    const telemetry = DigitalTwin.data.telemetry;
    if (telemetry && telemetry.slot_data) {
        const firstCell = Object.values(telemetry.slot_data)[0];
        if (firstCell) {
            DigitalTwin.totalSlots = firstCell.total_slots || 1000;
        }
    }

    // Initialize topology
    initializeTopology();

    // Populate link selector
    populateLinkSelector();

    // Update UI
    document.getElementById('totalSlots').textContent = DigitalTwin.totalSlots.toLocaleString();
}

function initializeTopology() {
    const topology = DigitalTwin.data.topology;
    if (!topology) return;

    // Create nodes for each cell
    const allCells = new Set();
    // Get all cells from links
    topology.links.forEach(link => {
        link.cells.forEach(cell => allCells.add(cell));
    });
    // Also add cells from correlation matrix to be safe
    if (topology.correlation_matrix) {
        topology.correlation_matrix.forEach(c => {
            allCells.add(c.cell1);
            allCells.add(c.cell2);
        });
    }

    const cellArray = Array.from(allCells).sort((a, b) => a - b);

    // Initialize nodes
    // For Stage B (Correlation), we want them initially scrambled or in a circle
    const centerX = 600;
    const centerY = 200;

    DigitalTwin.topology.nodes = cellArray.map((cell, index) => {
        // Random start position for "Observation" phase logic or Circle
        const angle = (index / cellArray.length) * 2 * Math.PI;
        return {
            id: cell,
            x: centerX + 100 * Math.cos(angle),
            y: centerY + 100 * Math.sin(angle),
            vx: 0,
            vy: 0,
            targetX: centerX + 150 * Math.cos(angle), // Final circle position for Stage C
            targetY: centerY + 150 * Math.sin(angle)
        };
    });

    // Initialize timeliens for Stage A
    initializeTimelines(cellArray);
}

function initializeTimelines(cells) {
    const container = document.getElementById('lossTimelines');
    container.innerHTML = '';

    cells.forEach(cellId => {
        const row = document.createElement('div');
        row.className = 'cell-timeline-row';
        row.innerHTML = `
            <div class="timeline-label">Cell ${cellId}</div>
            <div class="timeline-track-view" id="timeline-track-${cellId}">
                <!-- Ticks added here -->
            </div>
        `;
        container.appendChild(row);
    });

    // Populate ticks
    if (DigitalTwin.data.telemetry.loss_events) {
        const totalSlots = DigitalTwin.totalSlots || 1000;

        DigitalTwin.data.telemetry.loss_events.forEach(event => {
            event.cells.forEach(cellId => {
                const track = document.getElementById(`timeline-track-${cellId}`);
                if (track) {
                    const tick = document.createElement('div');
                    tick.className = 'loss-tick';
                    const leftPct = (event.slot / totalSlots) * 100;
                    tick.style.left = `${leftPct}%`;
                    track.appendChild(tick);
                }
            });
        });
    }

    // Add current time indicator to all tracks (optional, or just one global overlay)
    // We will update a "current time line" in render loop
}

function populateLinkSelector() {
    const select = document.getElementById('linkSelect');
    select.innerHTML = '';

    if (!DigitalTwin.data || !DigitalTwin.data.topology) return;

    DigitalTwin.data.topology.links.forEach(link => {
        const option = document.createElement('option');
        option.value = link.link_id;
        option.textContent = `Link ${link.link_id} (${link.cells.length} cells)`;
        select.appendChild(option);
    });

    // Select first link
    if (DigitalTwin.data.topology.links.length > 0) {
        DigitalTwin.selectedLink = DigitalTwin.data.topology.links[0].link_id;
        select.value = DigitalTwin.selectedLink;
    }
}

// ===================================
// EVENT LISTENERS
// ===================================

function setupEventListeners() {
    // Mode toggle
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            e.target.closest('.mode-btn').classList.add('active');
        });
    });

    // Intelligence toggle
    const intelBtn = document.querySelector('.intel-btn');
    intelBtn.addEventListener('click', () => {
        DigitalTwin.intelligenceEnabled = !DigitalTwin.intelligenceEnabled;
        intelBtn.dataset.state = DigitalTwin.intelligenceEnabled ? 'on' : 'off';
        intelBtn.querySelector('.state-text').textContent = DigitalTwin.intelligenceEnabled ? 'ON' : 'OFF';
        render();
    });

    // Time controls
    document.getElementById('playPauseBtn').addEventListener('click', togglePlayback);
    document.getElementById('prevBtn').addEventListener('click', () => stepSlot(-1));
    document.getElementById('nextBtn').addEventListener('click', () => stepSlot(1));
    document.getElementById('rewindBtn').addEventListener('click', () => jumpToSlot(0));
    document.getElementById('fastForwardBtn').addEventListener('click', () => jumpToSlot(DigitalTwin.totalSlots - 1));

    // Speed control
    document.getElementById('speedSelect').addEventListener('change', (e) => {
        DigitalTwin.playbackSpeed = parseFloat(e.target.value);
        if (DigitalTwin.isPlaying) {
            stopPlayback();
            startPlayback();
        }
    });

    // Jump controls
    document.getElementById('jumpToStartBtn').addEventListener('click', () => jumpToSlot(0));
    document.getElementById('jumpToEndBtn').addEventListener('click', () => jumpToSlot(DigitalTwin.totalSlots - 1));
    document.getElementById('jumpToLossBtn').addEventListener('click', jumpToNextLossEvent);

    // Timeline scrubbing
    const timeline = document.getElementById('timeline');
    timeline.addEventListener('click', (e) => {
        const rect = timeline.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = x / rect.width;
        const slot = Math.floor(percent * DigitalTwin.totalSlots);
        jumpToSlot(slot);
    });

    // Link selector
    document.getElementById('linkSelect').addEventListener('change', (e) => {
        DigitalTwin.selectedLink = parseInt(e.target.value);
        render();
    });

    // Topology controls
    document.getElementById('nextStageBtn').addEventListener('click', () => {
        const stages = ['A', 'B', 'C'];
        const currentIdx = stages.indexOf(DigitalTwin.topology.stage);
        if (currentIdx < stages.length - 1) {
            DigitalTwin.topology.stage = stages[currentIdx + 1];
            render();
        }
    });

    document.getElementById('resetTopologyBtn').addEventListener('click', () => {
        DigitalTwin.topology.stage = 'A';
        initializeTopology(); // Re-scramble positions
        render();
    });

    // Stage indicators click
    document.querySelectorAll('.stage-indicator').forEach(el => {
        el.addEventListener('click', (e) => {
            const newStage = e.currentTarget.id.replace('stage', '');
            if (['A', 'B', 'C'].includes(newStage)) {
                DigitalTwin.topology.stage = newStage;
                render();
            }
        });
    });
}

// ===================================
// PLAYBACK CONTROL
// ===================================

function togglePlayback() {
    if (DigitalTwin.isPlaying) {
        stopPlayback();
    } else {
        startPlayback();
    }
}

function startPlayback() {
    DigitalTwin.isPlaying = true;
    document.getElementById('playPauseBtn').querySelector('.icon').textContent = '⏸';

    const interval = 50 / DigitalTwin.playbackSpeed; // 50ms base interval
    DigitalTwin.playbackInterval = setInterval(() => {
        stepSlot(1);
        if (DigitalTwin.currentSlot >= DigitalTwin.totalSlots - 1) {
            stopPlayback();
        }
    }, interval);
}

function stopPlayback() {
    DigitalTwin.isPlaying = false;
    document.getElementById('playPauseBtn').querySelector('.icon').textContent = '▶';

    if (DigitalTwin.playbackInterval) {
        clearInterval(DigitalTwin.playbackInterval);
        DigitalTwin.playbackInterval = null;
    }
}

function stepSlot(delta) {
    DigitalTwin.currentSlot = Math.max(0, Math.min(DigitalTwin.totalSlots - 1, DigitalTwin.currentSlot + delta));
    render();
}

function jumpToSlot(slot) {
    DigitalTwin.currentSlot = Math.max(0, Math.min(DigitalTwin.totalSlots - 1, slot));

    // Clear particles on jump
    DigitalTwin.particles.baseline = [];
    DigitalTwin.particles.optimized = [];

    render();
}

function jumpToNextLossEvent() {
    if (!DigitalTwin.data || !DigitalTwin.data.telemetry.loss_events) return;

    const lossEvents = DigitalTwin.data.telemetry.loss_events;
    const nextEvent = lossEvents.find(event => event.slot > DigitalTwin.currentSlot);

    if (nextEvent) {
        jumpToSlot(nextEvent.slot);
    } else if (lossEvents.length > 0) {
        // Loop back to first event
        jumpToSlot(lossEvents[0].slot);
    }
}

// ===================================
// RENDERING
// ===================================

function render() {
    updateTimeDisplay();
    updateTopologyConfidence();
    renderTopology();
    renderTwinPhysics();
    renderLinkPhysics();
    renderOperatorDecision();
}

function updateTimeDisplay() {
    document.getElementById('currentSlot').textContent = DigitalTwin.currentSlot.toLocaleString();

    // Update timeline
    const percent = (DigitalTwin.currentSlot / DigitalTwin.totalSlots) * 100;
    document.getElementById('timelineProgress').style.width = `${percent}%`;
    document.getElementById('timelineHandle').style.left = `${percent}%`;
}

function updateTopologyConfidence() {
    if (!DigitalTwin.data || !DigitalTwin.data.topology.confidence_timeline) return;

    const timeline = DigitalTwin.data.topology.confidence_timeline;
    const currentEntry = timeline.find(entry => entry.slot >= DigitalTwin.currentSlot) || timeline[timeline.length - 1];

    if (currentEntry) {
        const confidence = currentEntry.confidence * 100;
        document.querySelector('.confidence-value').textContent = `${confidence.toFixed(0)}%`;
        document.querySelector('.confidence-fill').style.width = `${confidence}%`;
        DigitalTwin.topology.confidence = confidence;
    }
}

function renderTopology() {
    const stage = DigitalTwin.topology.stage;

    // Update stage visibility
    document.querySelectorAll('.stage-indicator').forEach(el => el.classList.remove('active'));
    document.getElementById(`stage${stage}`).classList.add('active');

    document.querySelectorAll('.topo-stage').forEach(el => el.classList.add('hidden'));
    document.getElementById(`topologyStage${stage}`).classList.remove('hidden');

    // Render specific stage
    if (stage === 'A') {
        renderStageA();
    } else if (stage === 'B') {
        renderStageB();
    } else if (stage === 'C') {
        renderStageC();
    }
}

function renderStageA() {
    // Update current time line position
    // We need to create it if it doesn't exist, or update it
    // Actually, let's just create a vertical line that moves across the timeline container
    // We'll use a single overlay for performance if possible, or update the left position of a marker

    // For now, let's just scroll the timeline to center the current time? 
    // Or simpler: Move a "current time" vertical bar.

    const totalSlots = DigitalTwin.totalSlots || 1000;
    const currentPct = (DigitalTwin.currentSlot / totalSlots) * 100;

    // We need to add the current time line to the container if not present
    // But since this runs every frame, we should check existence.
    // Better: Add it in initialization.
    // For now, let's just leave the ticks.

    // Ideally we want to see the "head" moving.
    // Let's add a vertical line to each track? No, too heavy.
    // A single overlay div in css? 
    // Let's hack it: search for an element with id 'current-time-overlay' inside 'lossTimelines'
    let overlay = document.getElementById('current-time-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'current-time-overlay';
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.bottom = '0';
        overlay.style.width = '2px';
        overlay.style.background = '#eab308';
        overlay.style.zIndex = '20';
        overlay.style.pointerEvents = 'none';
        document.getElementById('lossTimelines').appendChild(overlay);
    }
    overlay.style.left = `${currentPct}%`;
}

function renderStageB() {
    const ctx = document.getElementById('correlationCanvas').getContext('2d');
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Physics Step: Move nodes based on attraction/repulsion
    updateForceLayout();

    // Draw Nodes
    DigitalTwin.topology.nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
        ctx.fillStyle = '#3b82f6';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.5)';
        ctx.stroke();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(`C${node.id}`, node.x, node.y - 12);
    });

    // Draw "Correlation Links" (faint lines appearing when close)
    // Only if correlation exists in data
    const topology = DigitalTwin.data.topology;
    if (topology.correlation_matrix) {
        topology.correlation_matrix.forEach(corr => {
            if (corr.correlation > 0.5) {
                const n1 = DigitalTwin.topology.nodes.find(n => n.id === corr.cell1);
                const n2 = DigitalTwin.topology.nodes.find(n => n.id === corr.cell2);
                if (n1 && n2) {
                    const dist = Math.hypot(n2.x - n1.x, n2.y - n1.y);
                    if (dist < 200) { // Only draw if relatively close
                        const alpha = (1 - dist / 200) * corr.correlation;
                        ctx.beginPath();
                        ctx.moveTo(n1.x, n1.y);
                        ctx.lineTo(n2.x, n2.y);
                        ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`; // Redish for correlation
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }
            }
        });
    }
}

function updateForceLayout() {
    const nodes = DigitalTwin.topology.nodes;
    const repulsion = 500;
    const attraction = 0.05;
    const centerAttract = 0.005;
    const centerX = 600;
    const centerY = 200;

    // Apply forces
    nodes.forEach((node, i) => {
        let fx = 0, fy = 0;

        // Center Gravity
        fx += (centerX - node.x) * centerAttract;
        fy += (centerY - node.y) * centerAttract;

        // Repulsion between all nodes
        nodes.forEach((other, j) => {
            if (i === j) return;
            const dx = node.x - other.x;
            const dy = node.y - other.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 300) {
                const f = repulsion / (dist * dist);
                fx += (dx / dist) * f;
                fy += (dy / dist) * f;
            }
        });

        // Attraction for correlated nodes
        // We need to look up correlation. O(N*M) - acceptable for small N
        const correlations = DigitalTwin.data.topology.correlation_matrix || [];
        correlations.forEach(corr => {
            let otherId = null;
            if (corr.cell1 === node.id) otherId = corr.cell2;
            else if (corr.cell2 === node.id) otherId = corr.cell1;

            if (otherId !== null && corr.correlation > 0.5) {
                const other = nodes.find(n => n.id === otherId);
                if (other) {
                    const dx = other.x - node.x;
                    const dy = other.y - node.y;
                    fx += dx * attraction * corr.correlation;
                    fy += dy * attraction * corr.correlation;
                }
            }
        });

        // Apply velocity
        node.vx = (node.vx || 0) * 0.9 + fx;
        node.vy = (node.vy || 0) * 0.9 + fy;
        node.x += node.vx;
        node.y += node.vy;
    });
}


function renderStageC() {
    const ctx = document.getElementById('inferenceCanvas').getContext('2d');
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Move nodes to target positions (Circle)
    const nodes = DigitalTwin.topology.nodes;
    nodes.forEach(node => {
        node.x = node.x * 0.95 + node.targetX * 0.05; // Ease to target
        node.y = node.y * 0.95 + node.targetY * 0.05;

        // Draw Node
        ctx.beginPath();
        ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = '#10b981'; // Green for inferred
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = '12px JetBrains Mono';
        ctx.fillText(`C${node.id}`, node.x, node.y - 15);
    });

    // Draw Inferred Links
    // We use the actual links from data
    const links = DigitalTwin.data.topology.links;
    links.forEach(link => {
        // Find center of this link (centroid of cells)
        let cx = 0, cy = 0;
        let validNodes = 0;

        // Draw lines from cells to Link Center (DU/Switch)
        // Or just connect cells together?
        // Let's connect cells to a virtual "Link Node" if shared, or just to each other.
        // Better: Connect directly to a "Fronthaul" point?
        // Let's draw the "Shared Link" style: A line connecting all cells.

        // Simple visualization: Draw lines between all cells in the link
        // Or finding a "Link Node" position (average of cell positions)
        link.cells.forEach(cellId => {
            const node = nodes.find(n => n.id === cellId);
            if (node) {
                cx += node.x;
                cy += node.y;
                validNodes++;
            }
        });

        if (validNodes > 0) {
            cx /= validNodes;
            cy /= validNodes;

            // Draw lines from cells to centroid
            link.cells.forEach(cellId => {
                const node = nodes.find(n => n.id === cellId);
                if (node) {
                    ctx.beginPath();
                    ctx.moveTo(node.x, node.y);
                    ctx.lineTo(cx, cy);
                    ctx.strokeStyle = '#10b981';
                    ctx.lineWidth = 3;
                    ctx.stroke();
                }
            });

            // Draw "Link" bubble at centroid
            ctx.beginPath();
            ctx.arc(cx, cy, 15, 0, 2 * Math.PI);
            ctx.fillStyle = '#1e293b';
            ctx.fill();
            ctx.strokeStyle = '#10b981';
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = '#10b981';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = '10px sans-serif';
            ctx.fillText(`L${link.link_id}`, cx, cy);
        }
    });

    // Draw confidence
    document.getElementById('confidenceScore').textContent = '98%'; // Mock or from data
}

function renderTwinPhysics() {
    if (!DigitalTwin.data || !DigitalTwin.selectedLink) return;

    const optimization = DigitalTwin.data.optimization[DigitalTwin.selectedLink];
    if (!optimization) return;

    // Get current data points
    // We map currentSlot to the dataset index
    // The data might be sparse or different length, assuming 1-to-1 for now as per export
    const trafficProfile = optimization.baseline.traffic_timeline;
    // Map currentSlot to timeline index
    const totalSlots = DigitalTwin.totalSlots;
    const dataIndex = Math.floor((DigitalTwin.currentSlot / totalSlots) * trafficProfile.length);

    // 1. Update Particle System
    spawnParticles(trafficProfile[dataIndex], optimization);
    updateParticles(optimization);

    // 2. Render Baseline
    const ctxBase = DigitalTwin.canvases.baseline;
    renderPhysicsScene(ctxBase, DigitalTwin.particles.baseline, 'baseline', optimization);

    // 3. Render Optimized
    const ctxOpt = DigitalTwin.canvases.optimized;
    renderPhysicsScene(ctxOpt, DigitalTwin.particles.optimized, 'optimized', optimization);

    // 4. Update Metrics (Text)
    updatePhysicsMetrics(optimization);
}

function spawnParticles(currentTrafficGbps, optimization) {
    // Traffic determines spawn rate
    // 1 particle per 0.5 Gbps?
    // Scale down for visual sanity
    if (!currentTrafficGbps) return;

    const spawnChance = currentTrafficGbps / 5; // Adjust factor
    const count = Math.floor(spawnChance) + (Math.random() < (spawnChance % 1) ? 1 : 0);

    for (let i = 0; i < count; i++) {
        // Shared properties
        const y = 50 + Math.random() * 200; // Spread vertically

        // Baseline Particle
        DigitalTwin.particles.baseline.push({
            x: 0,
            y: y,
            speed: 5 + Math.random(),
            state: 'moving', // moving, dropped, success
            type: 'data'
        });

        // Optimized Particle
        DigitalTwin.particles.optimized.push({
            x: 0,
            y: y,
            speed: 5 + Math.random(),
            state: 'moving', // moving, buffering, dropped, success
            type: 'data',
            bufferWait: 0
        });
    }
}

function updateParticles(optimization) {
    const width = 550; // Canvas width
    const bottleneckX = 300; // Where link physics happens

    // Get loss status for current slot
    const lossEvents = DigitalTwin.data.telemetry.loss_events || [];
    // Check if ANY loss event includes current slot
    // Optimization: Pre-calc map. For now linear scan is ok for 100 events
    const isLossSlot = lossEvents.some(e => Math.abs(e.slot - DigitalTwin.currentSlot) < 5); // Window of effect

    // Get buffer status
    const bufferTimeline = optimization.buffer_timeline;
    const currentBuffer = bufferTimeline.find(b => b.slot >= DigitalTwin.currentSlot) || {};
    const isOverflow = currentBuffer.is_overflow;

    // --- Baseline Update ---
    DigitalTwin.particles.baseline.forEach(p => {
        if (p.state !== 'moving') return;

        p.x += p.speed;

        // Check Bottleneck
        if (p.x > bottleneckX && p.x < bottleneckX + 10) {
            // Chance to drop corresponds to "Is there loss now?"
            // In baseline, ANY burst over cap causes loss
            // We simplify: If we are in a loss slot, drop 20% of particles
            if (isLossSlot && Math.random() < 0.2) {
                p.state = 'dropped';
            }
        }

        // Cleanup
        if (p.x > width) p.state = 'success';
    });
    // Remove dead particles
    DigitalTwin.particles.baseline = DigitalTwin.particles.baseline.filter(p => p.x <= width && p.state !== 'gone');

    // --- Optimized Update ---
    // Buffer area is approx x=250 to x=350
    const bufferEntry = 250;
    const bufferExit = 350;

    DigitalTwin.particles.optimized.forEach(p => {
        if (p.state === 'moving') {
            p.x += p.speed;

            // Enter Buffer
            if (p.x > bufferEntry && p.x < bufferExit) {
                // Determine behavior based on buffer occupancy
                if (currentBuffer.occupancy_pct > 0) {
                    // Slow down or "wait" visually?
                    // Let's make them flow slower through buffer area
                    p.x -= p.speed * 0.5;
                }

                if (isOverflow && Math.random() < 0.1) {
                    p.state = 'dropped';
                }
            }
        } else if (p.state === 'dropped') {
            // Fall down
            p.y += 2;
            if (p.y > 300) p.state = 'gone';
        }

        if (p.x > width) p.state = 'success';
    });

    DigitalTwin.particles.optimized = DigitalTwin.particles.optimized.filter(p => p.state !== 'gone' && p.state !== 'success');
}

function renderPhysicsScene(ctx, particles, type, optimization) {
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const width = canvas.width;
    const height = canvas.height;

    // Draw Environment
    // 1. Cells (Left)
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, 50, height);
    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.fillText("CELLS", 10, height / 2);

    // 2. Bottleneck / Link
    const bottleneckX = 300;

    if (type === 'baseline') {
        // Draw Capacity Line constraint
        ctx.beginPath();
        ctx.moveTo(bottleneckX, 0);
        ctx.lineTo(bottleneckX, height);
        ctx.strokeStyle = '#ef4444';
        ctx.setLineDash([5, 5]);
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = '#ef4444';
        ctx.fillText("CAPACITY LIMIT", bottleneckX + 10, 20);
    } else {
        // Draw Buffer Tank
        const bufferX = 250;
        const bufferW = 100;

        // Buffer Fill Visual
        const bufferTimeline = optimization.buffer_timeline;
        const currentBuffer = bufferTimeline.find(b => b.slot >= DigitalTwin.currentSlot) || {};
        const fillPct = (currentBuffer.occupancy_pct || 0) / 100;

        ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
        ctx.fillRect(bufferX, height - (height * fillPct), bufferW, height * fillPct);

        ctx.strokeStyle = '#10b981';
        ctx.strokeRect(bufferX, 0, bufferW, height);

        ctx.fillStyle = '#10b981';
        ctx.fillText("TRAFFIC SHAPING BUFFER", bufferX, 20);
    }

    // Draw Particles
    particles.forEach(p => {
        ctx.beginPath();
        if (p.state === 'dropped') {
            ctx.fillStyle = '#ef4444';
            ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
        } else {
            ctx.fillStyle = type === 'baseline' ? '#f59e0b' : '#06b6d4';
            ctx.arc(p.x, p.y, 2, 0, 2 * Math.PI);
        }
        ctx.fill();
    });
}

function updatePhysicsMetrics(optimization) {
    // Reuse existing DOM update logic, simpler text
    document.getElementById('baselinePeak').textContent = `${optimization.baseline.peak_capacity_gbps.toFixed(2)} Gbps`;
    document.getElementById('baselineLoss').textContent = '> 1%';
    document.getElementById('optimizedPeak').textContent = `${optimization.optimized.optimal_capacity_gbps.toFixed(2)} Gbps`;
    document.getElementById('optimizedLoss').textContent = `${optimization.simulation_stats.loss_pct.toFixed(3)}%`;

    // Also call renderLinkPhysics to update the meters at the bottom
    renderLinkPhysics(); // This function stays mostly same but needs check
}

function renderLinkPhysics() {
    if (!DigitalTwin.data || !DigitalTwin.selectedLink) return;

    const optimization = DigitalTwin.data.optimization[DigitalTwin.selectedLink];
    if (!optimization) return;

    // Find current buffer state
    const bufferTimeline = optimization.buffer_timeline;
    const currentBuffer = bufferTimeline.find(b => b.slot >= DigitalTwin.currentSlot) || bufferTimeline[0];

    if (currentBuffer) {
        // Update buffer visualization
        const bufferFill = document.getElementById('bufferFill');
        bufferFill.style.height = `${currentBuffer.occupancy_pct}%`;
        bufferFill.classList.toggle('overflow', currentBuffer.is_overflow);

        document.getElementById('bufferOccupancy').textContent = `${currentBuffer.occupancy_pct.toFixed(1)}%`;
        document.getElementById('bufferStatus').textContent = currentBuffer.is_overflow ? 'OVERFLOW' : 'NORMAL';
    }

    // Update capacity meter
    const traffic = optimization.baseline.traffic_timeline;
    const currentTraffic = traffic[Math.floor((DigitalTwin.currentSlot / DigitalTwin.totalSlots) * traffic.length)] || 0;
    const capacity = optimization.optimized.optimal_capacity_gbps;
    const utilization = (currentTraffic / capacity) * 100;

    document.getElementById('capacityFill').style.width = `${Math.min(100, utilization)}%`;
    document.getElementById('capacityValue').textContent = `${currentTraffic.toFixed(2)} Gbps`;
    document.getElementById('capacityMax').textContent = `${capacity.toFixed(2)} Gbps`;

    // Update buffer depth
    document.getElementById('bufferDepth').textContent = `${optimization.optimized.buffer_us} µs`;

    // Update loss counter
    const lossEvents = DigitalTwin.data.telemetry.loss_events || [];
    const lossCount = lossEvents.filter(e => e.slot <= DigitalTwin.currentSlot).length;
    document.getElementById('lossCounter').textContent = lossCount;
    document.getElementById('lossPct').textContent = `${optimization.simulation_stats.loss_pct.toFixed(3)}%`;

    // Render rate trace
    renderRateTrace(traffic);
}

function renderRateTrace(traffic) {
    const ctx = DigitalTwin.canvases.rateTrace;
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!traffic || traffic.length === 0) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = 20;

    // Show last 100 samples
    const windowSize = 100;
    const currentIndex = Math.floor((DigitalTwin.currentSlot / DigitalTwin.totalSlots) * traffic.length);
    const startIndex = Math.max(0, currentIndex - windowSize);
    const window = traffic.slice(startIndex, currentIndex + 1);

    if (window.length === 0) return;

    const maxValue = Math.max(...window);
    const avgValue = window.reduce((a, b) => a + b, 0) / window.length;
    const papr = maxValue / avgValue;

    // Update stats
    document.getElementById('tracePeak').textContent = `${maxValue.toFixed(2)} Gbps`;
    document.getElementById('traceAvg').textContent = `${avgValue.toFixed(2)} Gbps`;
    document.getElementById('tracePAPR').textContent = `${papr.toFixed(1)}x`;

    // Draw trace
    const xScale = (width - 2 * padding) / windowSize;
    const yScale = (height - 2 * padding) / maxValue;

    ctx.beginPath();
    window.forEach((value, index) => {
        const x = padding + index * xScale;
        const y = height - padding - (value * yScale);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 2;
    ctx.stroke();
}

function renderOperatorDecision() {
    if (!DigitalTwin.data || !DigitalTwin.selectedLink) return;

    const decision = DigitalTwin.data.decisions.per_link[DigitalTwin.selectedLink];
    if (!decision) return;

    // Update risk level
    const riskLevel = decision.risk_level || 'NONE';
    document.getElementById('riskLevel').textContent = riskLevel;

    const riskColors = {
        'NONE': '#10b981',
        'LOW': '#22c55e',
        'MEDIUM': '#f59e0b',
        'HIGH': '#ef4444',
        'CRITICAL': '#dc2626'
    };

    const riskLevelEl = document.getElementById('riskLevel');
    riskLevelEl.style.color = riskColors[riskLevel] || '#10b981';

    // Update risk bar
    const riskPercents = { 'NONE': 0, 'LOW': 20, 'MEDIUM': 50, 'HIGH': 75, 'CRITICAL': 100 };
    document.getElementById('riskFill').style.width = `${riskPercents[riskLevel] || 0}%`;

    // Update metrics
    document.getElementById('riskLossPct').textContent = `${(decision.confidence * 100).toFixed(1)}%`;
    document.getElementById('riskConfidence').textContent = `${(decision.confidence * 100).toFixed(0)}%`;

    // Update recommendation
    const recommendationBox = document.getElementById('recommendationBox');
    const recommendationIcon = document.getElementById('recommendationIcon');
    const recommendationText = document.getElementById('recommendationText');
    const rationaleText = document.getElementById('rationaleText');

    const actionIcons = {
        'ENABLE_SHAPING': '✅',
        'CONDITIONAL_SHAPING': '⚠️',
        'UPGRADE_REQUIRED': '❌',
        'UPGRADE_RECOMMENDED': '⬆️'
    };

    const actionColors = {
        'ENABLE_SHAPING': '#10b981',
        'CONDITIONAL_SHAPING': '#f59e0b',
        'UPGRADE_REQUIRED': '#ef4444',
        'UPGRADE_RECOMMENDED': '#f59e0b'
    };

    recommendationIcon.textContent = actionIcons[decision.action] || '✅';
    recommendationText.textContent = decision.recommendation;
    recommendationBox.style.borderColor = actionColors[decision.action] || '#10b981';
    rationaleText.textContent = decision.rationale;

    // Update deployment summary
    const summary = DigitalTwin.data.decisions.risk_summary;
    if (summary) {
        document.getElementById('enableCount').textContent = summary.enable_shaping || 0;
        document.getElementById('conditionalCount').textContent = summary.conditional || 0;
        document.getElementById('upgradeCount').textContent = summary.upgrade_required || 0;
    }

    // Update system status
    document.getElementById('systemStatus').textContent = DigitalTwin.intelligenceEnabled ? 'OPTIMIZING' : 'MONITORING';
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1a1f2e;
        border: 2px solid #ef4444;
        padding: 2rem;
        border-radius: 8px;
        color: #e8eaed;
        max-width: 500px;
        z-index: 1000;
        text-align: center;
    `;
    errorDiv.innerHTML = `
        <h2 style="color: #ef4444; margin-bottom: 1rem;">⚠️ Error</h2>
        <p style="margin-bottom: 1rem;">${message}</p>
        <button onclick="this.parentElement.remove()" style="
            background: #ef4444;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
        ">Close</button>
    `;
    document.body.appendChild(errorDiv);
}

// ===================================
// EXPORT
// ===================================

window.DigitalTwin = DigitalTwin;
