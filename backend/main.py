import asyncio
import json
import os
import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import models, crud
from backend.database.database import engine, get_db, SessionLocal
from backend.environment.env import NetworkEnvironment, SCENARIOS
from backend.agents.agent import BaseDefenderAgent
from backend.agents.communication import CommunicationLayer
from backend.marl.mappo import CentralizedMAPPO, ACTION_MAP
from backend.services.nvidia_analyst import test_nvidia_connection, explain_cyber_event

# Initialize database schema
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Autonomous Cybersecurity Defense System API", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Instances
sim_env = NetworkEnvironment(scenario="Scenario 2")
agent_1 = BaseDefenderAgent("Agent 1", "Segment A")
agent_2 = BaseDefenderAgent("Agent 2", "Segment B")
agent_3 = BaseDefenderAgent("Agent 3", "Segment C")
agents = [agent_1, agent_2, agent_3]
comm_layer = CommunicationLayer(agents)
mappo_policy = CentralizedMAPPO()

# Global State Control
active_connections: List[WebSocket] = []
simulation_state = {
    "mode": "MARL",                # DEMO, BASELINE, MARL, TRAINING, EVALUATION
    "scenario": "Scenario 2",
    "is_running": False,
    "tick_interval": 1.0,         # seconds per tick (1x = 1.0, 0.5x = 2.0, 2x = 0.5)
    "speed_label": "1×",
    "current_episode_id": 1,
    "episode_number": 1,
    "timeline_stage": "OBSERVE",   # OBSERVE, DETECT, COMMUNICATE, DECIDE, ACT, REWARD
    "narration": "System online. Decentralized defender agents initialized with MAPPO policy.",
    "is_demo_mode": False
}

# Auto-runner background task reference
runner_task: Optional[asyncio.Task] = None

def get_complete_telemetry() -> Dict[str, Any]:
    env_state = sim_env.get_state()
    global_state_t = mappo_policy.extract_global_state_tensor(env_state)
    critic_v = round(mappo_policy.get_value(global_state_t).item(), 3)
    
    agent_states = [a.get_public_state() for a in agents]

    return {
        "type": "telemetry_update",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "mode": simulation_state["mode"],
        "scenario": simulation_state["scenario"],
        "scenario_name": SCENARIOS.get(simulation_state["scenario"], "Lateral Movement"),
        "is_running": simulation_state["is_running"],
        "speed_label": simulation_state["speed_label"],
        "episode": simulation_state["episode_number"],
        "timeline_stage": simulation_state["timeline_stage"],
        "narration": simulation_state["narration"],
        "environment": env_state,
        "agents": agent_states,
        "communication": {
            "recent_messages": comm_layer.get_recent_messages(10),
            "active_packets": comm_layer.get_active_packets()
        },
        "marl": {
            "algorithm": "MAPPO",
            "architecture": "CTDE",
            "critic_value_v_s": critic_v,
            "metrics": mappo_policy.training_metrics
        }
    }

async def broadcast_state():
    telemetry = get_complete_telemetry()
    message_json = json.dumps(telemetry)
    for ws in list(active_connections):
        try:
            await ws.send_text(message_json)
        except Exception:
            if ws in active_connections:
                active_connections.remove(ws)

async def execute_step_cycle() -> Dict[str, Any]:
    """
    Executes one complete Dec-POMDP decision cycle:
    OBSERVE -> DETECT -> COMMUNICATE -> DECIDE -> ACT -> REWARD -> (LEARN)
    """
    db = SessionLocal()
    ep_id = simulation_state["current_episode_id"]
    step_num = sim_env.step_count + 1

    try:
        # 1. OBSERVE
        simulation_state["timeline_stage"] = "OBSERVE"
        obs_map = {a.agent_id: sim_env.get_observation(a.agent_id) for a in agents}
        for a in agents:
            obs = obs_map[a.agent_id]
            crud.log_observation(db, ep_id, step_num, 0, obs, obs["threat_level"])

        # 2. DETECT
        simulation_state["timeline_stage"] = "DETECT"
        detected_threats = []
        for a in agents:
            threat = obs_map[a.agent_id]["threat_level"]
            if threat >= 0.35 or obs_map[a.agent_id]["compromised"]:
                detected_threats.append((a, threat))
                crud.log_event(db, ep_id, step_num, "DETECTION", {
                    "source": a.agent_id, "segment": a.segment,
                    "threat_level": threat, "description": f"Threat detected in {a.segment}: {threat:.2f}"
                })

        # 3. COMMUNICATE
        simulation_state["timeline_stage"] = "COMMUNICATE"
        for a, threat in detected_threats:
            rec_action = "ISOLATE" if threat >= 0.7 else "BLOCK"
            sent_msgs = comm_layer.broadcast(
                sender_id=a.agent_id,
                message_type="THREAT_ALERT",
                content={
                    "segment": a.segment,
                    "threat_level": threat,
                    "recommended_action": rec_action,
                    "info": f"Threat elevated in {a.segment}. Coordinate defense!"
                }
            )
            for m in sent_msgs:
                crud.log_communication(db, ep_id, step_num, m["sender"], m["receiver"],
                                       m["message_type"], m["content"], m["threat_level"])
                crud.log_event(db, ep_id, step_num, "COMMUNICATION", {
                    "source": m["sender"], "target": m["receiver"], "segment": a.segment,
                    "threat_level": threat, "description": f"{m['sender']} ➔ {m['receiver']}: THREAT_ALERT ({m['threat_level']})"
                })

        # 4. DECIDE
        simulation_state["timeline_stage"] = "DECIDE"
        joint_actions = {}
        decisions_data = {}
        mode = simulation_state["mode"]
        current_env_state = sim_env.get_state()
        global_state_t = mappo_policy.extract_global_state_tensor(current_env_state)
        val_t = mappo_policy.get_value(global_state_t)

        for a in agents:
            action_str, prob_dict, log_prob, obs_tensor = a.select_action(
                obs_map[a.agent_id], mappo_policy, mode=mode
            )
            joint_actions[a.agent_id] = action_str
            decisions_data[a.agent_id] = {
                "action": action_str, "probs": prob_dict,
                "log_prob": log_prob, "obs_tensor": obs_tensor
            }
            crud.log_action(db, ep_id, step_num, 0, action_str, prob_dict, "EXECUTED")
            crud.log_event(db, ep_id, step_num, "ACTION", {
                "source": a.agent_id, "segment": a.segment,
                "threat_level": obs_map[a.agent_id]["threat_level"],
                "description": f"{a.agent_id} decided: {action_str}"
            })

        # 5. ACT
        simulation_state["timeline_stage"] = "ACT"
        new_state, rewards, done, step_info = sim_env.step(joint_actions)

        # Log environmental attack events
        for ev in step_info.get("events", []):
            crud.log_event(db, ep_id, step_num, ev["type"], {
                "source": "Attacker", "target": new_state.get("attacker_location"),
                "threat_level": 0.8, "description": ev["desc"]
            })

        # 6. REWARD
        simulation_state["timeline_stage"] = "REWARD"
        breakdown = step_info.get("reward_breakdown", {})
        for a in agents:
            r = rewards.get(a.agent_id, 0.0)
            a.record_step_result(step_num, r)
            crud.log_reward(db, ep_id, step_num, 0,
                            breakdown.get("detection", 0.0),
                            breakdown.get("containment", 0.0),
                            breakdown.get("attack_penalty", 0.0),
                            breakdown.get("false_action_penalty", 0.0),
                            r)

        crud.log_event(db, ep_id, step_num, "REWARD", {
            "source": "CooperativeEnvironment",
            "threat_level": 0.0,
            "description": f"Cooperative Reward: {breakdown.get('total', 0.0)} (Detection: +{breakdown.get('detection', 0.0)}, Cont: +{breakdown.get('containment', 0.0)})"
        })

        # 7. MARL ROLLOUT STORAGE & LEARNING (if TRAINING mode)
        if mode == "TRAINING":
            simulation_state["timeline_stage"] = "LEARNING"
            for a in agents:
                d = decisions_data[a.agent_id]
                if d["obs_tensor"] is not None and d["log_prob"] is not None:
                    mappo_policy.store_transition(
                        agent_id=a.agent_id,
                        obs_t=d["obs_tensor"],
                        global_state_t=global_state_t,
                        action_str=d["action"],
                        log_prob=d["log_prob"],
                        reward=rewards[a.agent_id],
                        done=done,
                        value=val_t
                    )
            if done:
                next_global_state_t = mappo_policy.extract_global_state_tensor(new_state)
                train_metrics = mappo_policy.train_step(next_global_state_t)
                crud.record_training_run(db, simulation_state["episode_number"], train_metrics)
                crud.log_event(db, ep_id, step_num, "LEARNING", {
                    "source": "MAPPO_Critic",
                    "description": f"MAPPO CTDE Update: Actor Loss={train_metrics['actor_loss']}, Critic Loss={train_metrics['critic_loss']}"
                })

        # Generate live AI incident narration
        summary_payload = {
            "scenario": sim_env.scenario,
            "attack_stage": new_state["attack_stage"],
            "joint_action": joint_actions,
            "network_health": new_state["network_health"],
            "contained": new_state["contained"]
        }
        simulation_state["narration"] = explain_cyber_event(summary_payload)

        # Handle episode termination
        if done:
            outcome = "CONTAINED" if new_state["contained"] else ("COMPROMISED" if new_state["critical_resource"]["compromised"] else "MAX_STEPS")
            tot_reward = sum(a.cumulative_reward for a in agents)
            crud.finish_episode(db, ep_id, tot_reward, outcome)
            if not simulation_state["is_demo_mode"]:
                # Auto start next episode if running continuous
                pass

        await broadcast_state()
        return {"state": new_state, "rewards": rewards, "done": done, "timeline": simulation_state["timeline_stage"]}
    finally:
        db.close()

async def auto_simulation_loop():
    while True:
        try:
            if simulation_state["is_running"]:
                result = await execute_step_cycle()
                if result.get("done", False):
                    # Pause on episode finish
                    simulation_state["is_running"] = False
                    await broadcast_state()
            await asyncio.sleep(simulation_state["tick_interval"])
        except asyncio.CancelledError:
            break
        except Exception as e:
            print("Auto loop error:", e)
            await asyncio.sleep(1.0)

@app.on_event("startup")
async def startup_event():
    global runner_task
    # Record initial episode in DB
    db = SessionLocal()
    ep = crud.create_episode(db, sim_env.scenario, simulation_state["mode"])
    simulation_state["current_episode_id"] = ep.id
    db.close()
    runner_task = asyncio.create_task(auto_simulation_loop())

@app.on_event("shutdown")
async def shutdown_event():
    global runner_task
    if runner_task:
        runner_task.cancel()

# --- WebSocket Telemetry Stream ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send immediate initial state on connect
        await websocket.send_text(json.dumps(get_complete_telemetry()))
        while True:
            data = await websocket.receive_text()
            # Can receive frontend command payloads if needed
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

# --- REST Endpoints ---
@app.get("/api/health")
def read_root():
    return {"status": "System Online", "version": "2.0.0", "marl": "MAPPO with CTDE"}

@app.get("/api/state")
def get_state():
    return get_complete_telemetry()

@app.post("/api/simulation/step")
async def step_simulation():
    res = await execute_step_cycle()
    return res

@app.post("/api/simulation/start")
async def start_simulation():
    simulation_state["is_running"] = True
    await broadcast_state()
    return {"status": "started", "is_running": True}

@app.post("/api/simulation/pause")
async def pause_simulation():
    simulation_state["is_running"] = False
    await broadcast_state()
    return {"status": "paused", "is_running": False}

@app.post("/api/simulation/resume")
async def resume_simulation():
    simulation_state["is_running"] = True
    await broadcast_state()
    return {"status": "resumed", "is_running": True}

@app.post("/api/simulation/reset")
async def reset_simulation(scenario: Optional[str] = None):
    chosen_scenario = scenario or simulation_state["scenario"]
    sim_env.reset(chosen_scenario)
    for a in agents:
        a.reset()
    comm_layer.clear()
    
    simulation_state["is_running"] = False
    simulation_state["timeline_stage"] = "OBSERVE"
    simulation_state["episode_number"] += 1
    simulation_state["narration"] = f"Simulation reset. Topology refreshed under {SCENARIOS.get(chosen_scenario, chosen_scenario)}."
    
    db = SessionLocal()
    ep = crud.create_episode(db, chosen_scenario, simulation_state["mode"])
    simulation_state["current_episode_id"] = ep.id
    db.close()

    await broadcast_state()
    return {"message": "Simulation reset", "episode": simulation_state["episode_number"]}

class SpeedModel(BaseModel):
    speed: str # "0.5x", "1x", "2x"

@app.post("/api/simulation/speed")
async def set_speed(payload: SpeedModel):
    spd = payload.speed
    if spd == "0.5x":
        simulation_state["tick_interval"] = 2.0
        simulation_state["speed_label"] = "0.5×"
    elif spd == "2x":
        simulation_state["tick_interval"] = 0.5
        simulation_state["speed_label"] = "2×"
    else:
        simulation_state["tick_interval"] = 1.0
        simulation_state["speed_label"] = "1×"
    await broadcast_state()
    return {"speed": simulation_state["speed_label"], "interval": simulation_state["tick_interval"]}

class ModeModel(BaseModel):
    mode: str # DEMO, BASELINE, MARL, TRAINING, EVALUATION

@app.post("/api/simulation/mode")
async def set_mode(payload: ModeModel):
    simulation_state["mode"] = payload.mode
    simulation_state["narration"] = f"Operating mode switched to {payload.mode}."
    await broadcast_state()
    return {"mode": simulation_state["mode"]}

class ScenarioModel(BaseModel):
    scenario: str # Scenario 1, Scenario 2, Scenario 3, Scenario 4

@app.post("/api/simulation/scenario")
async def set_scenario(payload: ScenarioModel):
    simulation_state["scenario"] = payload.scenario
    await reset_simulation(payload.scenario)
    return {"scenario": simulation_state["scenario"]}

@app.post("/api/simulation/demo")
async def run_panel_demo():
    """
    Executes a structured Panel Demo sequence:
    Reset -> Healthy baseline -> Penetration -> Threat Broadcast -> Coordinated Containment -> Reward -> Narration
    """
    simulation_state["is_demo_mode"] = True
    simulation_state["is_running"] = False
    
    # 1. Reset
    await reset_simulation("Scenario 2")
    simulation_state["narration"] = "Panel Demo Stage 1: Healthy network baseline. Defenders monitoring traffic."
    await broadcast_state()
    await asyncio.sleep(1.2)

    # 2. Advance steps through the attack-defense cycle
    while not sim_env.contained and not sim_env.critical_resource["compromised"] and sim_env.step_count < 6:
        await execute_step_cycle()
        await asyncio.sleep(1.5)

    simulation_state["is_demo_mode"] = False
    return {"status": "demo_complete", "contained": sim_env.contained}

# --- Database & History APIs ---
@app.get("/api/history/episodes")
def get_history_episodes(limit: int = 15, db: Session = Depends(get_db)):
    episodes = crud.get_episodes(db, limit)
    return [
        {
            "id": ep.id,
            "scenario": ep.scenario,
            "scenario_name": SCENARIOS.get(ep.scenario, ep.scenario),
            "mode": ep.mode,
            "total_reward": round(ep.total_reward, 2) if ep.total_reward else 0.0,
            "outcome": ep.outcome,
            "start_time": ep.start_time.strftime("%H:%M:%S") if ep.start_time else ""
        }
        for ep in episodes
    ]

@app.get("/api/history/events")
def get_history_events(filter_type: str = "ALL", limit: int = 50, db: Session = Depends(get_db)):
    events = crud.get_events(db, event_type=filter_type, limit=limit)
    return [
        {
            "id": ev.id,
            "step": ev.step,
            "event_type": ev.event_type,
            "source": ev.source,
            "target": ev.target,
            "segment": ev.segment,
            "threat_level": ev.threat_level,
            "description": ev.description,
            "timestamp": ev.timestamp.strftime("%H:%M:%S") if ev.timestamp else ""
        }
        for ev in events
    ]

@app.get("/api/training/metrics")
def get_training_metrics():
    return {
        "metrics": mappo_policy.training_metrics,
        "algorithm": "MAPPO (CTDE)",
        "status": "Active" if simulation_state["mode"] == "TRAINING" else "Ready"
    }

class TrainRequest(BaseModel):
    episodes: int = 5

@app.post("/api/training/train_episodes")
async def trigger_training(req: TrainRequest):
    """Runs N simulated episodes to train MAPPO actor and critic networks."""
    db = SessionLocal()
    rewards_history = []
    
    for _ in range(req.episodes):
        sim_env.reset()
        for a in agents: a.reset()
        comm_layer.clear()
        done = False
        
        while not done:
            curr_state = sim_env.get_state()
            g_t = mappo_policy.extract_global_state_tensor(curr_state)
            v_t = mappo_policy.get_value(g_t)
            
            joint_actions = {}
            step_actions = {}
            for a in agents:
                obs = sim_env.get_observation(a.agent_id)
                act, p, log_p, obs_t = a.select_action(obs, mappo_policy, mode="TRAINING")
                joint_actions[a.agent_id] = act
                step_actions[a.agent_id] = (act, log_p, obs_t)
                
            n_state, r_dict, done, _ = sim_env.step(joint_actions)
            for a in agents:
                act, log_p, obs_t = step_actions[a.agent_id]
                mappo_policy.store_transition(
                    a.agent_id, obs_t, g_t, act, log_p, r_dict[a.agent_id], done, v_t
                )
                
        next_g = mappo_policy.extract_global_state_tensor(n_state)
        metrics = mappo_policy.train_step(next_g)
        rewards_history.append(sum(r_dict.values()))

    # Save checkpoint
    chk_path = f"models/mappo/checkpoint_ep_{simulation_state['episode_number']}.pt"
    mappo_policy.save_checkpoint(chk_path, simulation_state['episode_number'], float(sum(rewards_history)/len(rewards_history)))
    crud.record_checkpoint(db, chk_path, simulation_state['episode_number'], float(sum(rewards_history)/len(rewards_history)))
    crud.record_training_run(db, req.episodes, metrics)
    db.close()
    
    await broadcast_state()
    return {"status": "trained", "episodes": req.episodes, "metrics": metrics, "checkpoint": chk_path}

@app.get("/api/nvidia/status")
def get_nvidia_status():
    return test_nvidia_connection()

@app.post("/api/ai/explain")
def request_ai_explanation():
    env_state = sim_env.get_state()
    summary = {
        "scenario": sim_env.scenario,
        "attack_stage": env_state["attack_stage"],
        "joint_action": env_state["last_joint_action"],
        "network_health": env_state["network_health"],
        "contained": env_state["contained"]
    }
    explanation = explain_cyber_event(summary)
    simulation_state["narration"] = explanation
    return {"narration": explanation}

# --- Serve Frontend Static Build (Unified Single Service) ---
from fastapi.staticfiles import StaticFiles
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

