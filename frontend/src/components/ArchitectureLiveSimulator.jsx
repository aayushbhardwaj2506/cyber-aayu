import React, { useState, useEffect } from 'react';
import './ArchitectureLiveSimulator.css';

export default function ArchitectureLiveSimulator({ telemetry, onClose }) {
  const [activeTab, setActiveTab] = useState('PIPELINE'); // 'PIPELINE', 'NEURAL_NET', 'RL_TRAINING', 'NVIDIA_API'
  const [pulseIndex, setPulseIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseIndex((prev) => (prev + 1) % 6);
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  const agents = telemetry?.agents || [];
  const env = telemetry?.environment || {};
  const marl = telemetry?.marl || {};
  const timelineStage = telemetry?.timeline_stage || 'OBSERVE';

  return (
    <div className="arch-sim-overlay" onClick={onClose}>
      <div className="arch-sim-modal" onClick={(e) => e.stopPropagation()}>
        {/* MODAL HEADER */}
        <div className="arch-sim-header">
          <div className="arch-header-left">
            <span className="arch-icon">🔬</span>
            <div>
              <h2>SYSTEM ARCHITECTURE & NEURAL PIPELINE SIMULATOR</h2>
              <p>Live Visualizer of Orchestrator • PyTorch Neural Networks • PPO Learning • NVIDIA API</p>
            </div>
          </div>
          <button className="arch-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* NAVIGATION TABS */}
        <div className="arch-tabs">
          {[
            { id: 'PIPELINE', label: '1. FULL END-TO-END ORCHESTRATION' },
            { id: 'NEURAL_NET', label: '2. PYTORCH NEURAL NETWORKS (DEEP LEARNING)' },
            { id: 'RL_TRAINING', label: '3. MARL PPO & CTDE CRITIC LOOP' },
            { id: 'NVIDIA_API', label: '4. NVIDIA AI TRANSLATOR PIPELINE' }
          ].map((t) => (
            <button
              key={t.id}
              className={`arch-tab-btn ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* TAB 1: FULL END-TO-END ORCHESTRATION */}
        {activeTab === 'PIPELINE' && (
          <div className="arch-content-pane">
            <div className="pipeline-container">
              {/* ORCHESTRATOR HUB */}
              <div className="orchestrator-core">
                <div className="orch-pulse"></div>
                <h3>SIMULATION RUNTIME ORCHESTRATOR</h3>
                <code>backend/main.py • execute_step_cycle()</code>
                <div className="orch-state-badge">
                  CURRENT PHASE: <strong>{timelineStage}</strong> | TICK INTERVAL: <strong>{telemetry?.speed_label || '1×'}</strong>
                </div>
              </div>

              {/* FLOW DIAGRAM */}
              <div className="flow-grid">
                {/* Step 1: Observe */}
                <div className={`flow-card ${timelineStage === 'OBSERVE' ? 'active-step' : ''}`}>
                  <div className="flow-step-num">STAGE 1</div>
                  <h4>OBSERVE</h4>
                  <div className="flow-details">
                    <p>Sensor Telemetry Ingestion</p>
                    <code>o_i = [threat, iso, comp, alert]</code>
                  </div>
                  <div className="flow-status">✓ 3 Segments Sampled</div>
                </div>

                <div className="flow-arrow">➔</div>

                {/* Step 2: Detect & Message Bus */}
                <div className={`flow-card ${timelineStage === 'COMMUNICATE' || timelineStage === 'DETECT' ? 'active-step' : ''}`}>
                  <div className="flow-step-num">STAGE 2</div>
                  <h4>COMMUNICATE</h4>
                  <div className="flow-details">
                    <p>Inter-Agent Message Bus</p>
                    <code>backend/agents/communication.py</code>
                  </div>
                  <div className="flow-status">
                    ⚡ {telemetry?.communication?.recent_messages?.length || 0} Packets In Bus
                  </div>
                </div>

                <div className="flow-arrow">➔</div>

                {/* Step 3: PyTorch Actor Inference */}
                <div className={`flow-card ${timelineStage === 'DECIDE' ? 'active-step' : ''}`}>
                  <div className="flow-step-num">STAGE 3</div>
                  <h4>PYTORCH INFERENCE</h4>
                  <div className="flow-details">
                    <p>Actor Forward Pass</p>
                    <code>ActorNetwork(obs) ➔ Softmax</code>
                  </div>
                  <div className="flow-status" style={{ color: '#00f0ff' }}>
                    Joint: [{agents.map((a) => a.current_action).join(', ')}]
                  </div>
                </div>

                <div className="flow-arrow">➔</div>

                {/* Step 4: Environment Transition */}
                <div className={`flow-card ${timelineStage === 'ACT' ? 'active-step' : ''}`}>
                  <div className="flow-step-num">STAGE 4</div>
                  <h4>ENV TRANSITION</h4>
                  <div className="flow-details">
                    <p>Dec-POMDP State Machine</p>
                    <code>env.step(joint_actions)</code>
                  </div>
                  <div className="flow-status">
                    Health: {env.network_health}% | {env.attack_stage}
                  </div>
                </div>

                <div className="flow-arrow">➔</div>

                {/* Step 5: Reward & NVIDIA Translation */}
                <div className={`flow-card ${timelineStage === 'REWARD' ? 'active-step' : ''}`}>
                  <div className="flow-step-num">STAGE 5</div>
                  <h4>REWARD & NVIDIA AI</h4>
                  <div className="flow-details">
                    <p>Reward Decomposition + LLM</p>
                    <code>Total: {env.reward_breakdown?.total || 0}</code>
                  </div>
                  <div className="flow-status" style={{ color: '#8b5cf6' }}>
                    NVIDIA Incident Intel Generated
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: PYTORCH NEURAL NETWORKS (DEEP LEARNING) */}
        {activeTab === 'NEURAL_NET' && (
          <div className="arch-content-pane">
            <div className="nn-visualizer-container">
              <div className="nn-header">
                <h3>DECENTRALIZED ACTOR NEURAL NETWORK ARCHITECTURE</h3>
                <p>Live visualization of forward-pass tensor calculations for <strong>Agent 1 (Segment A)</strong></p>
              </div>

              <div className="nn-layers-grid">
                {/* Input Layer */}
                <div className="nn-layer">
                  <div className="layer-title">INPUT LAYER (4D)</div>
                  <div className="layer-neurons">
                    {[
                      { name: 'Threat Level', val: (agents[0]?.threat_level || 0).toFixed(2) },
                      { name: 'Is Isolated', val: agents[0]?.current_observation?.isolated ? '1.0' : '0.0' },
                      { name: 'Compromised', val: agents[0]?.current_observation?.compromised ? '1.0' : '0.0' },
                      { name: 'Alert Flag', val: agents[0]?.messages_received > 0 ? '1.0' : '0.0' }
                    ].map((neuron, idx) => (
                      <div key={idx} className="neuron-box input-neuron">
                        <div className="neuron-circle pulsing"></div>
                        <div className="neuron-label">{neuron.name}</div>
                        <div className="neuron-val">{neuron.val}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="synapse-beam">➔ Linear(4, 64) ➔ LayerNorm ➔ ReLU ➔</div>

                {/* Hidden Layers */}
                <div className="nn-layer">
                  <div className="layer-title">HIDDEN LAYERS (64 NODES)</div>
                  <div className="hidden-matrix">
                    <div className="matrix-badge">Layer 1: 64 Neurons (ReLU)</div>
                    <div className="matrix-graphic">
                      {Array.from({ length: 32 }).map((_, i) => (
                        <span key={i} className={`mini-node ${i % 3 === pulseIndex % 3 ? 'active' : ''}`}></span>
                      ))}
                    </div>
                    <div className="synapse-sub-beam">⬇ LayerNorm + Linear(64, 64) ⬇</div>
                    <div className="matrix-badge">Layer 2: 64 Neurons (ReLU)</div>
                    <div className="matrix-graphic">
                      {Array.from({ length: 32 }).map((_, i) => (
                        <span key={i} className={`mini-node ${(i + 1) % 3 === pulseIndex % 3 ? 'active' : ''}`}></span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="synapse-beam">➔ Linear(64, 4) ➔ Softmax ➔</div>

                {/* Output Layer */}
                <div className="nn-layer">
                  <div className="layer-title">OUTPUT LAYER (4 ACTIONS)</div>
                  <div className="layer-neurons">
                    {Object.entries(agents[0]?.action_probabilities || { MONITOR: 0.85, ALERT: 0.05, BLOCK: 0.05, ISOLATE: 0.05 }).map(
                      ([act, prob]) => {
                        const isChosen = agents[0]?.current_action === act;
                        return (
                          <div key={act} className={`neuron-box output-neuron ${isChosen ? 'chosen' : ''}`}>
                            <div className={`neuron-circle ${isChosen ? 'selected' : ''}`}></div>
                            <div className="neuron-label">{act}</div>
                            <div className="neuron-val">{(prob * 100).toFixed(1)}%</div>
                            {isChosen && <span className="chosen-tag">SELECTED</span>}
                          </div>
                        );
                      }
                    )}
                  </div>
                </div>
              </div>

              <div className="code-anchor-box">
                <strong>Source Code Location:</strong> <code>backend/marl/mappo.py • class ActorNetwork(nn.Module)</code>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: MARL PPO & CTDE CRITIC LOOP */}
        {activeTab === 'RL_TRAINING' && (
          <div className="arch-content-pane">
            <div className="ctde-visualizer">
              <div className="ctde-dual-plane">
                {/* EXECUTION PLANE */}
                <div className="plane-card decentralized-plane">
                  <div className="plane-header">
                    <h4>DECENTRALIZED EXECUTION PLANE (RUNTIME)</h4>
                    <span className="badge-plane">LOCAL AGENTS ONLY</span>
                  </div>
                  <div className="plane-body">
                    <p>Agents act independently with zero global state cheat codes:</p>
                    <div className="agent-mini-row">
                      <div className="agent-tag">Agent 1 (Segment A) ➔ Actor 1</div>
                      <div className="agent-tag">Agent 2 (Segment B) ➔ Actor 2</div>
                      <div className="agent-tag">Agent 3 (Segment C) ➔ Actor 3</div>
                    </div>
                  </div>
                </div>

                {/* SYNCHRONIZATION CONDUIT */}
                <div className="ctde-conduit">
                  <span>⬇ Trajectory Rollouts (o_t, a_t, r_t, o_t+1) Stored In RolloutBuffer ⬇</span>
                </div>

                {/* TRAINING PLANE */}
                <div className="plane-card centralized-plane">
                  <div className="plane-header">
                    <h4>CENTRALIZED TRAINING PLANE (CTDE CRITIC)</h4>
                    <span className="badge-plane training">TRAINING ONLY</span>
                  </div>
                  <div className="plane-body">
                    <div className="critic-eq-box">
                      <div className="critic-title">CENTRALIZED CRITIC V_φ(S_global)</div>
                      <p>Global State Vector: 16 Features (All 3 Segments + Critical Core + Attacker Stage)</p>
                      <div className="critic-metric-row">
                        <div>V(S_t) Value Estimate: <strong style={{ color: '#c084fc' }}>{marl.critic_value_v_s || '0.00'}</strong></div>
                        <div>GAE Advantage: <strong style={{ color: '#00f0ff' }}>Â_t = Σ (γλ)^l δ_(t+l)</strong></div>
                        <div>PPO Loss: <strong style={{ color: '#f59e0b' }}>L_CLIP(θ)</strong></div>
                      </div>
                    </div>

                    <div className="backprop-animation-box">
                      <div className="backprop-title">🔥 BACKPROPAGATION & OPTIMIZATION LOOP</div>
                      <code>loss.backward() ➔ Adam Optimizer (lr=3e-4) ➔ .pt Checkpoint Generated</code>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: NVIDIA AI TRANSLATOR PIPELINE */}
        {activeTab === 'NVIDIA_API' && (
          <div className="arch-content-pane">
            <div className="nvidia-pipeline-container">
              <h3>NVIDIA AI INCIDENT EXPLAINER & TRANSLATOR</h3>
              <p>How the simulation telemetry is formatted and translated into natural language SOC intelligence:</p>

              <div className="nvidia-flow-diagram">
                {/* 1. Raw Telemetry */}
                <div className="nv-box">
                  <div className="nv-box-num">1. TELEMETRY PACKAGER</div>
                  <code>
                    &#123;<br />
                    &nbsp;&nbsp;scenario: "{env.scenario || 'Scenario 2'}",<br />
                    &nbsp;&nbsp;stage: "{env.attack_stage || 'NORMAL'}",<br />
                    &nbsp;&nbsp;joint_action: {JSON.stringify(env.last_joint_action || {})},<br />
                    &nbsp;&nbsp;network_health: {env.network_health}%<br />
                    &#125;
                  </code>
                </div>

                <div className="nv-arrow">➔ HTTP POST Payload ➔</div>

                {/* 2. Cloud Endpoint */}
                <div className="nv-box nv-cloud">
                  <div className="nv-box-num">2. NVIDIA NIM CLOUD API</div>
                  <div className="nv-cloud-badge">meta/llama-3.1-8b-instruct</div>
                  <p>Endpoint: <code>https://integrate.api.nvidia.com/v1/chat/completions</code></p>
                  <div className="key-protected-pill">🔒 NVIDIA_API_KEY (Loaded securely from .env)</div>
                </div>

                <div className="nv-arrow">➔ 2-Sentence Analysis ➔</div>

                {/* 3. Dashboard Intel */}
                <div className="nv-box nv-output">
                  <div className="nv-box-num">3. DASHBOARD SOC BANNER</div>
                  <div className="nv-speech-bubble">
                    "{telemetry?.narration || 'Autonomous agents executing coordinated perimeter defense.'}"
                  </div>
                  <span className="live-tag">LIVE ON DASHBOARD</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
