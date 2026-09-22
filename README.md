# Autonomous Multi-Agent Cybersecurity Defense System

A demonstrable autonomous multi-agent cybersecurity defense prototype utilizing **Multi-Agent Proximal Policy Optimization (MAPPO)** with **Centralized Training and Decentralized Execution (CTDE)** and a real-time **SOC Visualizer**.

---

## 🏛️ System Architecture

- **Backend**: Python 3 + FastAPI + SQLAlchemy + SQLite
- **Multi-Agent Reinforcement Learning**: PyTorch (MAPPO with CTDE)
- **Communication Layer**: Inter-agent asynchronous message broadcasting
- **Persistence & Logging**: SQLite database recording episodes, observations, actions with probability distributions, messages, and rewards
- **Supporting AI Analyst**: NVIDIA API integration (reads `NVIDIA_API_KEY` from `.env`) with reliable offline local heuristic fallback
- **Frontend SOC Visualizer**: React 19 + Vite (Dark mode, 16:9 SOC layout, WebSockets streaming)

---

## 🚀 Running the Prototype

### 1. Prerequisites & Dependencies
```bash
# Install backend requirements
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment (Optional NVIDIA API)
The `.env` file contains your API keys:
```env
NVIDIA_API_KEY=your_key_here
```
*(The system automatically operates with built-in SOC intelligence if the API key is not present or offline).*

### 3. Run Backend Server
```bash
uvicorn backend.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- WebSocket Telemetry: `ws://localhost:8000/ws`

### 4. Run Frontend Dashboard
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🛡️ Core Visualizer Features

1. **Central Network Topology**:
   - Visual nodes: `Attacker` ➔ `Segment A (Agent 1)` ➔ `Segment B (Agent 2)` ➔ `Segment C (Agent 3)` ➔ `Critical Server`.
   - Dynamic severance of links on segment isolation, lateral traversal tracking, and pulsing status.
2. **Three Decentralized Agent Cards**:
   - Live status badges: `MONITORING`, `ANALYZING`, `THREAT DETECTED`, `COMMUNICATING`, `DECIDING`, `RESPONDING`, `ISOLATING`.
   - Sensor threat progress bar, current action, detections, and message counters.
3. **Internal Agent Brain Inspector**:
   - Click any agent card to view its internal decision pipeline:
     `Local Observation ➔ Threat Features ➔ MAPPO Policy ➔ Softmax Action Probabilities Bar Chart ➔ Selected Action`.
4. **Agent-to-Agent Communication Bus**:
   - Visual packet log displaying sender, receiver, timestamp, message type, threat level, and recommended actions (`BLOCK`/`ISOLATE`).
5. **Attack Progression Pipeline**:
   - Horizontal pipeline tracking: `NORMAL` ➔ `RECONNAISSANCE` ➔ `INITIAL COMPROMISE` ➔ `LATERAL MOVEMENT` ➔ `TARGET ATTEMPT` ➔ `CONTAINED`.
6. **Horizontal Decision Timeline**:
   - Highlighted active loop: `OBSERVE` ➔ `DETECT` ➔ `COMMUNICATE` ➔ `DECIDE` ➔ `ACT` ➔ `REWARD`.
7. **Cooperative Reward Breakdown**:
   - Transparent reward components: Detection (+10), Containment (+15), Attack Penalty (-10 / -50), False Action Penalty (-5).
8. **Centralized Critic Training View (CTDE)**:
   - Displays centralized value estimate $V(s)$ from joint observation vector, clearly labeled *"Training Only"*.
9. **Simulation Controls**:
   - `RUN AUTO`, `PAUSE`, `STEP`, `RESET`, Speed (`0.5×`, `1×`, `2×`).
   - 4 Scenarios: *Single Segment Anomaly, Lateral Movement, Distributed Attack, Multiple Simultaneous Threats*.
   - Operating Modes: *MARL, BASELINE, TRAINING, EVALUATION*.
10. **Panel Demo Mode**:
    - One-click scripted demonstration sequence with live step-by-step panel narration.

---

## 🎓 Viva Presentation Talking Points

- **Dec-POMDP Formulation**: Cybersecurity represents a Decentralized Partially Observable Markov Decision Process. Agents observe noisy local segment telemetry, necessitating inter-agent communication to defend against lateral traversal.
- **CTDE (Centralized Training, Decentralized Execution)**:
  - *Training*: Centralized Critic evaluates the global state $S_t$ and computes Generalized Advantage Estimation (GAE) to stabilize gradient updates across multiple learning agents.
  - *Execution*: Decentralized Actors execute policies strictly conditioned on local observations $O_i$ and inbox messages.
- **Crucial Academic Distinction**:
  - **SQLite Database**: Persists experiment history, step events, actions, and evaluation metrics for academic reproducibility.
  - **Rollout Buffer**: Stores Dec-POMDP experience trajectories $(o_t, a_t, r_t, o_{t+1})$ needed for PPO gradient updates.
  - **Model Weights**: PyTorch neural network checkpoints (`models/mappo/`).
