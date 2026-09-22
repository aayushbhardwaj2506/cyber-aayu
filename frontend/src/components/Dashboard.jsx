import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';
import Cyber3DVisualizer from './Cyber3DVisualizer';
import ArchitectureLiveSimulator from './ArchitectureLiveSimulator';

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [eventFilter, setEventFilter] = useState('ALL');
  const [eventLogs, setEventLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('events'); // 'events' or 'history'
  const [historyEpisodes, setHistoryEpisodes] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [showArchSimulator, setShowArchSimulator] = useState(false);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [visualizerMode, setVisualizerMode] = useState('3D'); // '3D' or '2D'

  const wsRef = useRef(null);

  // Connect WebSocket & Polling fallback
  useEffect(() => {
    let reconnectTimeout = null;

    const connectWS = () => {
      const socket = new WebSocket(WS_URL);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'telemetry_update') {
            setTelemetry(msg);
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connectWS, 2000);
      };

      socket.onerror = () => {
        setIsConnected(false);
      };
    };

    connectWS();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Fetch events periodically or on filter change
  useEffect(() => {
    fetchEvents(eventFilter);
    const interval = setInterval(() => {
      fetchEvents(eventFilter);
      if (activeTab === 'history') fetchHistory();
    }, 2500);
    return () => clearInterval(interval);
  }, [eventFilter, activeTab]);

  const fetchEvents = async (filter) => {
    try {
      const res = await fetch(`${API_BASE}/api/history/events?filter_type=${filter}&limit=35`);
      if (res.ok) {
        const data = await res.json();
        setEventLogs(data);
      }
    } catch (e) {
      console.warn('Could not fetch events:', e);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/history/episodes?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setHistoryEpisodes(data);
      }
    } catch (e) {
      console.warn('Could not fetch episodes history:', e);
    }
  };

  // Simulation Controls
  const handleStep = async () => {
    await fetch(`${API_BASE}/api/simulation/step`, { method: 'POST' });
    fetchEvents(eventFilter);
  };

  const handleTogglePlay = async () => {
    if (!telemetry) return;
    const endpoint = telemetry.is_running ? 'pause' : 'start';
    await fetch(`${API_BASE}/api/simulation/${endpoint}`, { method: 'POST' });
  };

  const handleReset = async () => {
    await fetch(`${API_BASE}/api/simulation/reset`, { method: 'POST' });
    fetchEvents(eventFilter);
  };

  const handleSpeedChange = async (speedStr) => {
    await fetch(`${API_BASE}/api/simulation/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed: speedStr })
    });
  };

  const handleScenarioChange = async (e) => {
    const sc = e.target.value;
    await fetch(`${API_BASE}/api/simulation/scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: sc })
    });
  };

  const handleModeChange = async (e) => {
    const md = e.target.value;
    await fetch(`${API_BASE}/api/simulation/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: md })
    });
  };

  const handleRunPanelDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch(`${API_BASE}/api/simulation/demo`, { method: 'POST' });
    } finally {
      setIsDemoRunning(false);
      fetchEvents(eventFilter);
    }
  };

  const handleTrainEpisodes = async () => {
    setIsTraining(true);
    try {
      await fetch(`${API_BASE}/api/training/train_episodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ episodes: 5 })
      });
      fetchEvents(eventFilter);
    } finally {
      setIsTraining(false);
    }
  };

  const handleAskAIExplanation = async () => {
    await fetch(`${API_BASE}/api/ai/explain`, { method: 'POST' });
  };

  if (!telemetry) {
    return (
      <div className="dashboard-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#94a3b8' }}>
          <div className="pulse-dot" style={{ margin: '0 auto 12px auto', width: 14, height: 14, background: '#00f0ff' }}></div>
          <h3>Connecting to Autonomous Cyber Defense System...</h3>
          <p style={{ fontSize: 13 }}>Initializing Decentralized POMDP Simulation Engine</p>
        </div>
      </div>
    );
  }

  const { environment, agents, communication, marl } = telemetry;
  const health = environment.network_health || 100;
  const healthColor = health > 75 ? '#10b981' : (health > 45 ? '#f59e0b' : '#ef4444');
  const attackStage = environment.attack_stage || 'NORMAL';
  const breakdown = environment.reward_breakdown || {};

  return (
    <div className="dashboard-root">
      {/* 1. TOP HEADER */}
      <header className="soc-header">
        <div className="brand-section">
          <span className="brand-icon">🛡️</span>
          <div className="brand-title">
            <h1>AUTONOMOUS CYBER DEFENSE</h1>
            <p>Dec-POMDP • CTDE MAPPO Engine • Academic Prototype</p>
          </div>
        </div>

        <div className="header-status-group">
          <div className={`pulse-badge ${isConnected ? '' : 'offline'}`}>
            <span className="pulse-dot"></span>
            {isConnected ? 'SYSTEM ONLINE' : 'RECONNECTING'}
          </div>

          <div className="health-bar-container">
            <span>HEALTH:</span>
            <div className="health-track">
              <div className="health-fill" style={{ width: `${health}%`, backgroundColor: healthColor }}></div>
            </div>
            <span style={{ color: healthColor, minWidth: 32 }}>{health}%</span>
          </div>

          <div className="metric-pill">
            EPISODE <strong style={{ color: '#fff' }}>{telemetry.episode}</strong> | STEP <strong style={{ color: '#fff' }}>{environment.step}</strong>
          </div>

          <div className="header-actions">
            <button className="btn-panel-demo" onClick={handleRunPanelDemo} disabled={isDemoRunning}>
              {isDemoRunning ? 'RUNNING DEMO...' : '▶ PANEL DEMO MODE'}
            </button>
            <button className="btn-arch-sim" onClick={() => setShowArchSimulator(true)}>
              🔬 LIVE RL & AI ENGINE
            </button>
            <button className="btn-help" onClick={() => setShowHowItWorks(true)}>
              HOW IT WORKS
            </button>
          </div>
        </div>
      </header>

      {/* 2. CONTROL & HORIZONTAL TIMELINE ROW */}
      <div className="control-timeline-row">
        <div className="control-bar">
          <div className="control-btn-group">
            <button
              className={`ctrl-btn ${telemetry.is_running ? 'pause' : 'play'}`}
              onClick={handleTogglePlay}
            >
              {telemetry.is_running ? '⏸ PAUSE' : '▶ RUN AUTO'}
            </button>
            <button className="ctrl-btn step" onClick={handleStep} disabled={telemetry.is_running}>
              ⏭ STEP
            </button>
            <button className="ctrl-btn reset" onClick={handleReset}>
              ⟳ RESET
            </button>
          </div>

          <div className="ctrl-select-group">
            <div className="select-wrapper">
              <label>SCENARIO:</label>
              <select className="soc-select" value={telemetry.scenario} onChange={handleScenarioChange}>
                <option value="Scenario 1">Scenario 1: Single Segment Anomaly</option>
                <option value="Scenario 2">Scenario 2: Lateral Movement</option>
                <option value="Scenario 3">Scenario 3: Distributed Attack</option>
                <option value="Scenario 4">Scenario 4: Multiple Simultaneous Threats</option>
              </select>
            </div>

            <div className="select-wrapper">
              <label>MODE:</label>
              <select className="soc-select" value={telemetry.mode} onChange={handleModeChange}>
                <option value="MARL">MARL (MAPPO Policy)</option>
                <option value="BASELINE">BASELINE (Deterministic Rules)</option>
                <option value="TRAINING">TRAINING (Online CTDE Learning)</option>
                <option value="EVALUATION">EVALUATION (Fixed Checkpoint)</option>
              </select>
            </div>

            <div className="select-wrapper">
              <label>SPEED:</label>
              <div className="speed-buttons">
                {['0.5x', '1x', '2x'].map((s) => (
                  <button
                    key={s}
                    className={`speed-btn ${telemetry.speed_label.includes(s.replace('x', '')) ? 'active' : ''}`}
                    onClick={() => handleSpeedChange(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* DECISION TIMELINE */}
        <div className="timeline-bar">
          {[
            { id: 'OBSERVE', num: '1', label: 'OBSERVE' },
            { id: 'DETECT', num: '2', label: 'DETECT' },
            { id: 'COMMUNICATE', num: '3', label: 'COMMUNICATE' },
            { id: 'DECIDE', num: '4', label: 'DECIDE' },
            { id: 'ACT', num: '5', label: 'ACT' },
            { id: 'REWARD', num: '6', label: 'REWARD' }
          ].map((st, idx, arr) => (
            <React.Fragment key={st.id}>
              <div className={`timeline-step ${telemetry.timeline_stage === st.id ? 'active' : ''}`}>
                <span className="step-num">{st.num}</span>
                <span>{st.label}</span>
              </div>
              {idx < arr.length - 1 && <span className="timeline-arrow">➔</span>}
            </React.Fragment>
          ))}
        </div>

        {/* NARRATION BANNER */}
        <div className="narration-banner">
          <div className="narration-text">
            <span className="narration-tag">● SOC INTELLIGENCE:</span>
            {telemetry.narration}
            <span className="ai-tag">NVIDIA AI SUPPORTED</span>
          </div>
          <button
            onClick={handleAskAIExplanation}
            style={{ background: 'transparent', border: '1px solid #64748b', color: '#94a3b8', borderRadius: 4, padding: '3px 8px', fontSize: 10, cursor: 'pointer' }}
          >
            Refresh Explanation
          </button>
        </div>
      </div>

      {/* 3. MAIN 3-COLUMN SOC GRID */}
      <div className="main-grid">
        {/* COLUMN 1: TOPOLOGY & ATTACK PROGRESSION */}
        <div className="panel-card">
          <h3 className="panel-title">
            <span>NETWORK TOPOLOGY</span>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <button
                className={`topo-mode-btn ${visualizerMode === '3D' ? 'active' : ''}`}
                onClick={() => setVisualizerMode('3D')}
              >
                🌐 3D SIMULATOR
              </button>
              <button
                className={`topo-mode-btn ${visualizerMode === '2D' ? 'active' : ''}`}
                onClick={() => setVisualizerMode('2D')}
              >
                📋 2D SCHEMATIC
              </button>
            </div>
          </h3>

          {visualizerMode === '3D' ? (
            <Cyber3DVisualizer telemetry={telemetry} onSelectAgent={setSelectedAgent} />
          ) : (
            <div className="topology-flow">
              {/* Attacker Node */}
              <div className="attacker-node">
                <span>⚠️</span>
                <span>ATTACKER [{environment.attacker_location || 'STANDBY'}]</span>
              </div>

              <div className={`topo-connector ${environment.attacker_location === 'Segment A' ? 'active' : ''}`}></div>

              {/* Segments A, B, C */}
              {['Segment A', 'Segment B', 'Segment C'].map((segName, idx) => {
                const segData = environment.segments[segName] || {};
                const agentData = agents[idx] || {};
                const isPresent = environment.attacker_location === segName;

                return (
                  <React.Fragment key={segName}>
                    <div className={`segment-node ${segData.compromised ? 'compromised' : ''} ${segData.isolated ? 'isolated' : ''}`}>
                      <div className="node-left">
                        <h4>{segName} • {agentData.agent_id}</h4>
                        <p>Threat: {(segData.threat_level * 100).toFixed(0)}% | Status: {segData.status}</p>
                      </div>
                      <div>
                        {isPresent && <span className="node-badge compromised" style={{ marginRight: 6 }}>ATTACKER</span>}
                        <span className={`node-badge ${segData.compromised ? 'compromised' : (segData.isolated ? 'isolated' : 'normal')}`}>
                          {segData.isolated ? 'ISOLATED' : (segData.compromised ? 'COMPROMISED' : 'NORMAL')}
                        </span>
                      </div>
                    </div>
                    {idx < 2 && (
                      <div className={`topo-connector ${segData.isolated ? 'severed' : (isPresent ? 'active' : '')}`}></div>
                    )}
                  </React.Fragment>
                );
              })}

              <div className="topo-connector"></div>

              {/* Critical Server Node */}
              <div className={`critical-node ${environment.critical_resource.compromised ? 'compromised' : ''}`}>
                🔒 CRITICAL SERVER : {environment.critical_resource.compromised ? '💥 COMPROMISED' : '🛡️ SECURED'}
              </div>
            </div>
          )}

          {/* ATTACK PROGRESSION STAGES */}
          <div style={{ marginTop: 8 }}>
            <h4 style={{ margin: '0 0 6px 0', fontSize: 12, color: '#94a3b8' }}>ATTACK PROGRESSION PIPELINE</h4>
            <div className="attack-pipeline">
              {[
                { stage: 'NORMAL', label: '1. NORMAL BASELINE' },
                { stage: 'RECONNAISSANCE', label: '2. RECONNAISSANCE' },
                { stage: 'INITIAL COMPROMISE', label: '3. INITIAL COMPROMISE' },
                { stage: 'LATERAL MOVEMENT', label: '4. LATERAL MOVEMENT' },
                { stage: 'TARGET ATTEMPT', label: '5. TARGET ATTEMPT' },
                { stage: 'CONTAINED', label: '6. CONTAINED (DEFENSE SUCCESS)' }
              ].map((st) => (
                <div
                  key={st.stage}
                  className={`stage-step ${attackStage === st.stage ? 'active' : ''} ${attackStage === 'COMPROMISED' ? 'compromised' : ''} ${attackStage === 'CONTAINED' && st.stage === 'CONTAINED' ? 'contained' : ''}`}
                >
                  <span>{st.label}</span>
                  {attackStage === st.stage && <span>● ACTIVE</span>}
                </div>
              ))}
            </div>
          </div>

          {/* CURRENT JOINT ACTION */}
          <div className="joint-action-box">
            <div style={{ color: '#94a3b8' }}>CURRENT JOINT ACTION:</div>
            <div className="joint-vector">
              [{agents.map(a => `${a.agent_id}: ${a.current_action}`).join(', ')}]
            </div>
          </div>
        </div>

        {/* COLUMN 2: DEFENDER AGENTS & INTER-AGENT COMMUNICATION */}
        <div className="panel-card">
          <h3 className="panel-title">
            <span>DEFENDER AGENTS (DECENTRALIZED)</span>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>CTDE Execution</span>
          </h3>

          <div className="agents-list">
            {agents.map((ag) => (
              <div
                key={ag.agent_id}
                className="agent-soc-card"
                onClick={() => setSelectedAgent(ag)}
                title="Click to inspect Agent Brain & Decision Pipeline"
              >
                <div className="agent-card-header">
                  <span className="agent-name">🤖 {ag.agent_id} ({ag.segment})</span>
                  <span className={`agent-status-tag ${ag.status.replace(' ', '_')}`}>
                    {ag.status}
                  </span>
                </div>

                <div className="threat-meter">
                  <span style={{ minWidth: 70, color: '#94a3b8' }}>Sensor Threat:</span>
                  <div className="threat-track">
                    <div
                      className="threat-bar"
                      style={{
                        width: `${Math.min(100, ag.threat_level * 100)}%`,
                        backgroundColor: ag.threat_level > 0.7 ? '#ef4444' : (ag.threat_level > 0.35 ? '#f59e0b' : '#10b981')
                      }}
                    ></div>
                  </div>
                  <span style={{ minWidth: 35, textAlign: 'right' }}>{(ag.threat_level * 100).toFixed(0)}%</span>
                </div>

                <div className="agent-metrics-grid">
                  <div className="agent-metric-item">
                    <span>ACTION</span>
                    <strong style={{ color: '#00f0ff' }}>{ag.current_action}</strong>
                  </div>
                  <div className="agent-metric-item">
                    <span>DETECTIONS</span>
                    <strong>{ag.detections}</strong>
                  </div>
                  <div className="agent-metric-item">
                    <span>MSGS (TX/RX)</span>
                    <strong>{ag.messages_sent} / {ag.messages_received}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* AGENT-TO-AGENT COMMUNICATION BUS */}
          <div style={{ marginTop: 6 }}>
            <h4 style={{ margin: '0 0 6px 0', fontSize: 12, color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>AGENT COMMUNICATION BUS</span>
              <span style={{ color: '#3b82f6' }}>LIVE PACKETS</span>
            </h4>
            <div className="comm-bus">
              {communication.recent_messages.length === 0 ? (
                <div style={{ padding: 12, textAlign: 'center', color: '#64748b', fontSize: 11 }}>
                  No inter-agent alerts broadcast yet. Defenders in baseline monitoring.
                </div>
              ) : (
                communication.recent_messages.slice(0, 5).map((pkt) => (
                  <div key={pkt.id} className="comm-packet-card">
                    <div className="packet-header">
                      <span>{pkt.sender} ➔ {pkt.receiver}</span>
                      <span className={`packet-badge ${pkt.threat_level}`}>{pkt.threat_level}</span>
                    </div>
                    <div className="packet-body">
                      [{pkt.timestamp}] {pkt.message_type} • Seg: {pkt.segment} • Rec: <strong style={{ color: '#fff' }}>{pkt.recommended_action}</strong>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* COLUMN 3: REWARDS, MARL & CENTRALIZED CRITIC */}
        <div className="panel-card">
          <h3 className="panel-title">
            <span>COOPERATIVE REWARDS</span>
            <span style={{ fontSize: 11, color: '#10b981' }}>Total: {breakdown.total || 0}</span>
          </h3>

          <div className="reward-breakdown-list">
            <div className="reward-row">
              <span style={{ color: '#94a3b8' }}>Detection Reward:</span>
              <span style={{ color: '#10b981', fontWeight: 700 }}>+{breakdown.detection || 0}</span>
            </div>
            <div className="reward-row">
              <span style={{ color: '#94a3b8' }}>Containment Bonus:</span>
              <span style={{ color: '#10b981', fontWeight: 700 }}>+{breakdown.containment || 0}</span>
            </div>
            <div className="reward-row">
              <span style={{ color: '#94a3b8' }}>Attack Progression Penalty:</span>
              <span style={{ color: '#ef4444', fontWeight: 700 }}>{breakdown.attack_penalty || 0}</span>
            </div>
            <div className="reward-row">
              <span style={{ color: '#94a3b8' }}>False Action Penalty:</span>
              <span style={{ color: '#ef4444', fontWeight: 700 }}>{breakdown.false_action_penalty || 0}</span>
            </div>
            <div className="reward-row total">
              <span>TOTAL COOPERATIVE:</span>
              <span style={{ color: (breakdown.total || 0) >= 0 ? '#10b981' : '#ef4444', fontSize: 14 }}>
                {breakdown.total || 0}
              </span>
            </div>
          </div>

          {/* CENTRALIZED CRITIC (CTDE TRAINING VIEW) */}
          <div className="critic-view" style={{ marginTop: 8 }}>
            <div className="critic-header">
              <span>CENTRALIZED CRITIC V(s)</span>
              <span style={{ fontSize: 9, background: '#2e1065', padding: '2px 5px', borderRadius: 3 }}>
                TRAINING ONLY
              </span>
            </div>
            <div className="critic-flow">
              [Agent 1 Obs, Agent 2 Obs, Agent 3 Obs] ➔ Centralized Critic ➔ V(s)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>State Value Estimate:</span>
              <span className="critic-val">{marl.critic_value_v_s}</span>
            </div>
            <p style={{ margin: '6px 0 0 0', fontSize: 10, color: '#6b7280' }}>
              Decentralized actors rely purely on local observations during execution.
            </p>
          </div>

          {/* MARL CONTROL CENTER */}
          <div style={{ marginTop: 6, background: '#090e1a', padding: 10, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <strong style={{ fontSize: 12, color: '#fff' }}>MARL CONTROL CENTER</strong>
              <button
                onClick={handleTrainEpisodes}
                disabled={isTraining}
                style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer' }}
              >
                {isTraining ? 'Training...' : '⚡ Train 5 Ep'}
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
              <div>Actor Loss: <strong style={{ color: '#e2e8f0' }}>{marl.metrics.actor_loss || '0.00'}</strong></div>
              <div>Critic Loss: <strong style={{ color: '#e2e8f0' }}>{marl.metrics.critic_loss || '0.00'}</strong></div>
              <div>Entropy: <strong style={{ color: '#e2e8f0' }}>{marl.metrics.entropy || '0.00'}</strong></div>
              <div>Architecture: <strong style={{ color: '#00f0ff' }}>CTDE</strong></div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. BOTTOM PANEL: EVENT STREAM & EXPERIMENT HISTORY */}
      <div className="bottom-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className={`event-tab ${activeTab === 'events' ? 'active' : ''}`}
              onClick={() => setActiveTab('events')}
            >
              LIVE TELEMETRY STREAM
            </button>
            <button
              className={`event-tab ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => { setActiveTab('history'); fetchHistory(); }}
            >
              EXPERIMENT RUNS (SQLITE)
            </button>
          </div>

          {activeTab === 'events' && (
            <div className="event-tabs">
              {['ALL', 'ATTACK', 'DETECTION', 'COMMUNICATION', 'ACTION', 'REWARD', 'LEARNING'].map((ft) => (
                <button
                  key={ft}
                  className={`event-tab ${eventFilter === ft ? 'active' : ''}`}
                  onClick={() => setEventFilter(ft)}
                >
                  {ft}
                </button>
              ))}
            </div>
          )}
        </div>

        {activeTab === 'events' ? (
          <div className="event-log-container">
            {eventLogs.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 20 }}>
                No events matching filter '{eventFilter}'.
              </div>
            ) : (
              eventLogs.map((ev) => (
                <div key={ev.id} className="event-row">
                  <span className="event-time">[{ev.timestamp}]</span>
                  <span className={`event-type-badge type-${ev.event_type}`}>{ev.event_type}</span>
                  <span style={{ color: '#cbd5e1' }}>Step {ev.step}: {ev.description}</span>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="event-log-container">
            {historyEpisodes.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 20 }}>No past episodes found in database.</div>
            ) : (
              historyEpisodes.map((ep) => (
                <div key={ep.id} className="event-row" style={{ justifyContent: 'space-between', borderBottom: '1px solid #1a2333', paddingBottom: 4 }}>
                  <span>Episode #{ep.id} | {ep.scenario_name} ({ep.mode})</span>
                  <span>Outcome: <strong style={{ color: ep.outcome === 'CONTAINED' ? '#10b981' : '#ef4444' }}>{ep.outcome || 'IN_PROGRESS'}</strong></span>
                  <span>Total Reward: <strong style={{ color: ep.total_reward >= 0 ? '#10b981' : '#ef4444' }}>{ep.total_reward}</strong></span>
                  <span className="event-time">{ep.start_time}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* 5. AGENT BRAIN INSPECTOR MODAL */}
      {selectedAgent && (
        <div className="modal-overlay" onClick={() => setSelectedAgent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🧠 AGENT DECISION PROCESS : {selectedAgent.agent_id} ({selectedAgent.segment})</h3>
              <button className="btn-close-modal" onClick={() => setSelectedAgent(null)}>✕</button>
            </div>

            <div style={{ fontSize: 13, lineHeight: 1.6 }}>
              <div style={{ background: '#090e1a', padding: 10, borderRadius: 6, marginBottom: 12 }}>
                <strong>LOCAL OBSERVATION FEATURES</strong>
                <pre style={{ margin: '6px 0 0 0', color: '#00f0ff', fontSize: 12 }}>
                  {JSON.stringify(selectedAgent.current_observation, null, 2)}
                </pre>
              </div>

              <div>
                <strong>MAPPO POLICY SOFTMAX ACTION PROBABILITIES:</strong>
                <div className="probs-list">
                  {Object.entries(selectedAgent.action_probabilities || {}).map(([actName, prob]) => (
                    <div key={actName} className="prob-row">
                      <span className="prob-name" style={{ color: actName === selectedAgent.current_action ? '#00f0ff' : '#94a3b8' }}>
                        {actName}
                      </span>
                      <div className="prob-track">
                        <div
                          className="prob-bar"
                          style={{
                            width: `${(prob * 100).toFixed(1)}%`,
                            backgroundColor: actName === selectedAgent.current_action ? '#00f0ff' : '#334155'
                          }}
                        ></div>
                      </div>
                      <span className="prob-val">{(prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ background: '#0e182b', border: '1px solid #1e3a8a', padding: 10, borderRadius: 6, marginTop: 12 }}>
                <div>SELECTED ACTION: <strong style={{ color: '#00f0ff', fontSize: 14 }}>{selectedAgent.current_action}</strong></div>
                <div style={{ color: '#94a3b8', fontSize: 11, marginTop: 2 }}>
                  Agent Status: <strong>{selectedAgent.status}</strong> | Cumulative Reward: <strong>{selectedAgent.reward}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. HOW THE SYSTEM WORKS (VIVA EXPLAINABILITY MODAL) */}
      {showHowItWorks && (
        <div className="modal-overlay" onClick={() => setShowHowItWorks(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>ARCHITECTURE & VIVA EXPLAINABILITY</h3>
              <button className="btn-close-modal" onClick={() => setShowHowItWorks(false)}>✕</button>
            </div>

            <div style={{ fontSize: 13, lineHeight: 1.6, color: '#cbd5e1' }}>
              <h4 style={{ color: '#00f0ff', margin: '0 0 6px 0' }}>1. Problem Formulation: Dec-POMDP</h4>
              <p style={{ margin: '0 0 10px 0' }}>
                Cybersecurity defense operates under partial observability. Each agent monitors only its assigned network segment (Segment A, B, or C) and receives noisy local threat telemetry.
              </p>

              <h4 style={{ color: '#00f0ff', margin: '0 0 6px 0' }}>2. Centralized Training, Decentralized Execution (CTDE)</h4>
              <p style={{ margin: '0 0 10px 0' }}>
                <strong>Training:</strong> A Centralized Critic evaluates global state <code>S_t</code> to compute Generalized Advantage Estimation (GAE), stabilizing multi-agent policy gradients.<br />
                <strong>Execution:</strong> During live runtime, decentralized actors select actions strictly from local observations and received messages.
              </p>

              <h4 style={{ color: '#00f0ff', margin: '0 0 6px 0' }}>3. Inter-Agent Communication Bus</h4>
              <p style={{ margin: '0 0 10px 0' }}>
                When an agent observes elevated anomaly scores, it broadcasts structured alert packets (Threat Level, Segment, Recommended Action) to neighboring segment defenders.
              </p>

              <h4 style={{ color: '#00f0ff', margin: '0 0 6px 0' }}>4. Cooperative Reward Function</h4>
              <p style={{ margin: '0 0 10px 0' }}>
                Rewards encourage collaborative containment: +10 for detecting high threat, +15 for full containment, -10 to -50 for compromise, and -5 for false-positive isolation.
              </p>

              <div style={{ background: '#090e1a', padding: 10, borderRadius: 6, border: '1px solid #1f293d', marginTop: 12 }}>
                <strong style={{ color: '#f59e0b' }}>Key Viva Distinction:</strong><br />
                <em>Database ≠ Agent Memory ≠ MARL Learning</em><br />
                • <strong>SQLite DB:</strong> Persists experiment logs, events, and metrics.<br />
                • <strong>Rollout Buffer:</strong> Stores short-term Dec-POMDP experience trajectories for PPO updates.<br />
                • <strong>Model Weights:</strong> PyTorch neural network parameters defining actor & critic policies.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. ARCHITECTURE & RL ENGINE LIVE SIMULATOR MODAL */}
      {showArchSimulator && (
        <ArchitectureLiveSimulator
          telemetry={telemetry}
          onClose={() => setShowArchSimulator(false)}
        />
      )}
    </div>
  );
}
