from typing import Dict, List, Any, Optional, Tuple
import datetime

class BaseDefenderAgent:
    def __init__(self, agent_id: str, segment: str):
        self.agent_id = agent_id
        self.segment = segment
        self.status = "MONITORING"
        self.inbox: List[Dict[str, Any]] = []
        self.outbox: List[Dict[str, Any]] = []
        
        # Statistics
        self.detections = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.cumulative_reward = 0.0
        
        # Current and historical state
        self.last_action = "MONITOR"
        self.current_action = "MONITOR"
        self.action_probabilities = {"MONITOR": 0.9, "ALERT": 0.05, "BLOCK": 0.03, "ISOLATE": 0.02}
        self.current_observation: Dict[str, Any] = {}
        self.decision_history: List[Dict[str, Any]] = []

    def reset(self):
        self.status = "MONITORING"
        self.inbox.clear()
        self.outbox.clear()
        self.detections = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.cumulative_reward = 0.0
        self.last_action = "MONITOR"
        self.current_action = "MONITOR"
        self.action_probabilities = {"MONITOR": 0.9, "ALERT": 0.05, "BLOCK": 0.03, "ISOLATE": 0.02}
        self.decision_history.clear()

    def receive_message(self, message: Dict[str, Any]):
        self.inbox.append(message)
        self.messages_received += 1
        if self.status not in ["ISOLATING", "RESPONDING"]:
            self.status = "ANALYZING"

    def select_action(self, observation: Dict[str, Any], policy: Any, mode: str = "MARL") -> Tuple[str, Dict[str, float], Any, Any]:
        self.current_observation = observation
        threat = float(observation.get("threat_level", 0.0))
        is_isolated = observation.get("isolated", False)
        is_compromised = observation.get("compromised", False)
        
        has_alert = any(msg.get("message_type") == "THREAT_ALERT" for msg in self.inbox)

        # Update detection counts
        if threat >= 0.4 or is_compromised:
            self.detections += 1

        action_str = "MONITOR"
        prob_dict = {"MONITOR": 1.0, "ALERT": 0.0, "BLOCK": 0.0, "ISOLATE": 0.0}
        log_prob = None
        obs_tensor = None

        if mode == "BASELINE" or policy is None:
            # Deterministic rule-based baseline
            if is_isolated:
                action_str = "MONITOR"
                prob_dict = {"MONITOR": 0.95, "ALERT": 0.0, "BLOCK": 0.0, "ISOLATE": 0.05}
            elif threat >= 0.75 or is_compromised:
                action_str = "ISOLATE"
                prob_dict = {"MONITOR": 0.05, "ALERT": 0.10, "BLOCK": 0.25, "ISOLATE": 0.60}
            elif threat >= 0.45 or has_alert:
                action_str = "BLOCK"
                prob_dict = {"MONITOR": 0.10, "ALERT": 0.20, "BLOCK": 0.60, "ISOLATE": 0.10}
            elif threat >= 0.20:
                action_str = "ALERT"
                prob_dict = {"MONITOR": 0.15, "ALERT": 0.70, "BLOCK": 0.10, "ISOLATE": 0.05}
            else:
                action_str = "MONITOR"
                prob_dict = {"MONITOR": 0.85, "ALERT": 0.10, "BLOCK": 0.03, "ISOLATE": 0.02}
        else:
            # MARL (MAPPO policy inference)
            action_str, prob_dict, log_prob, obs_tensor = policy.get_action_and_probs(
                self.agent_id, observation, self.inbox
            )

        # Dynamic Status Mapping
        if action_str == "ISOLATE":
            self.status = "ISOLATING"
        elif action_str == "BLOCK":
            self.status = "RESPONDING"
        elif action_str == "ALERT":
            self.status = "COMMUNICATING"
        elif threat >= 0.5:
            self.status = "THREAT DETECTED"
        elif threat >= 0.2 or has_alert:
            self.status = "ANALYZING"
        else:
            self.status = "MONITORING"

        self.last_action = self.current_action
        self.current_action = action_str
        self.action_probabilities = prob_dict

        return action_str, prob_dict, log_prob, obs_tensor

    def record_step_result(self, step: int, reward: float, reason: str = ""):
        self.cumulative_reward += reward
        entry = {
            "step": step,
            "observation": dict(self.current_observation),
            "action": self.current_action,
            "reward": round(reward, 2),
            "status": self.status,
            "reason": reason or f"Threat: {round(float(self.current_observation.get('threat_level', 0.0)), 2)}"
        }
        self.decision_history.append(entry)
        if len(self.decision_history) > 20:
            self.decision_history.pop(0)

    def get_public_state(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "segment": self.segment,
            "status": self.status,
            "threat_level": round(float(self.current_observation.get("threat_level", 0.0)), 3),
            "current_observation": self.current_observation,
            "current_action": self.current_action,
            "last_action": self.last_action,
            "action_probabilities": self.action_probabilities,
            "reward": round(self.cumulative_reward, 2),
            "detections": self.detections,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "recent_history": self.decision_history[-5:]
        }
