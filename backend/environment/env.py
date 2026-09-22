import random
from typing import Dict, List, Tuple, Any, Optional

SCENARIOS = {
    "Scenario 1": "Single Segment Anomaly",
    "Scenario 2": "Lateral Movement",
    "Scenario 3": "Distributed Attack",
    "Scenario 4": "Multiple Simultaneous Threats"
}

class NetworkEnvironment:
    def __init__(self, scenario: str = "Scenario 2"):
        self.scenario = scenario
        self.segments = {
            "Segment A": {"status": "normal", "compromised": False, "isolated": False, "threat_level": 0.0},
            "Segment B": {"status": "normal", "compromised": False, "isolated": False, "threat_level": 0.0},
            "Segment C": {"status": "normal", "compromised": False, "isolated": False, "threat_level": 0.0},
        }
        self.critical_resource = {"status": "normal", "compromised": False}
        self.attacker_location = "ENTRY"
        self.attack_stage = "NORMAL"
        self.step_count = 0
        self.max_steps = 100
        self.contained = False
        self.last_joint_action: Dict[str, str] = {}
        self.before_segments: Dict[str, Any] = {}
        self.after_segments: Dict[str, Any] = {}
        self.last_reward_breakdown: Dict[str, Dict[str, float]] = {}

    def reset(self, scenario: Optional[str] = None) -> Dict[str, Any]:
        if scenario:
            self.scenario = scenario
        self.step_count = 0
        self.contained = False
        for seg in self.segments:
            self.segments[seg] = {
                "status": "normal",
                "compromised": False,
                "isolated": False,
                "threat_level": 0.0
            }
        self.critical_resource = {"status": "normal", "compromised": False}
        self.attacker_location = "ENTRY"
        self.attack_stage = "NORMAL"
        self.last_joint_action = {"Agent 1": "MONITOR", "Agent 2": "MONITOR", "Agent 3": "MONITOR"}
        self.before_segments = {k: dict(v) for k, v in self.segments.items()}
        self.after_segments = {k: dict(v) for k, v in self.segments.items()}
        self.last_reward_breakdown = {
            "detection": 0.0, "containment": 0.0,
            "attack_penalty": 0.0, "false_action_penalty": 0.0, "total": 0.0
        }
        return self.get_state()

    def get_network_health(self) -> float:
        """Computes real environment network health percentage (0 to 100%)."""
        total_health = 100.0
        if self.critical_resource["compromised"]:
            return 10.0
        
        for name, data in self.segments.items():
            if data["compromised"]:
                total_health -= 25.0
            elif data["isolated"]:
                total_health -= 10.0 # Isolation reduces operational capacity slightly
            else:
                total_health -= data["threat_level"] * 15.0
                
        return max(5.0, min(100.0, round(total_health, 1)))

    def get_state(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario,
            "scenario_name": SCENARIOS.get(self.scenario, "Lateral Movement"),
            "segments": {k: dict(v) for k, v in self.segments.items()},
            "critical_resource": dict(self.critical_resource),
            "attacker_location": self.attacker_location,
            "attack_stage": self.attack_stage,
            "step": self.step_count,
            "contained": self.contained,
            "network_health": self.get_network_health(),
            "last_joint_action": self.last_joint_action,
            "before_segments": self.before_segments,
            "after_segments": self.after_segments,
            "reward_breakdown": self.last_reward_breakdown
        }

    def get_observation(self, agent_id: str) -> Dict[str, Any]:
        mapping = {"Agent 1": "Segment A", "Agent 2": "Segment B", "Agent 3": "Segment C"}
        seg = mapping.get(agent_id, "Segment A")
        base_threat = self.segments[seg]["threat_level"]
        
        # Local sensor observation with subtle variance
        observed_threat = min(1.0, max(0.0, base_threat + random.uniform(-0.03, 0.03)))
        
        return {
            "segment": seg,
            "threat_level": round(observed_threat, 3),
            "isolated": self.segments[seg]["isolated"],
            "compromised": self.segments[seg]["compromised"],
            "status": self.segments[seg]["status"]
        }

    def apply_action(self, agent_id: str, action: str):
        mapping = {"Agent 1": "Segment A", "Agent 2": "Segment B", "Agent 3": "Segment C"}
        seg = mapping.get(agent_id, "Segment A")
        
        if action == "ISOLATE":
            self.segments[seg]["isolated"] = True
            self.segments[seg]["threat_level"] = max(0.0, self.segments[seg]["threat_level"] - 0.7)
            self.segments[seg]["status"] = "isolated"
        elif action == "BLOCK":
            # Active packet inspection and blocking
            self.segments[seg]["threat_level"] = max(0.0, self.segments[seg]["threat_level"] - 0.45)
            self.segments[seg]["status"] = "traffic_filtered"
        elif action == "ALERT":
            self.segments[seg]["status"] = "heightened_monitoring"
        elif action == "MONITOR":
            if not self.segments[seg]["isolated"]:
                self.segments[seg]["status"] = "normal" if self.segments[seg]["threat_level"] < 0.2 else "suspicious"

    def step(self, joint_actions: Dict[str, str]) -> Tuple[Dict[str, Any], Dict[str, float], bool, Dict[str, Any]]:
        self.step_count += 1
        self.last_joint_action = dict(joint_actions)
        self.before_segments = {k: dict(v) for k, v in self.segments.items()}

        # 1. Apply defensive actions
        for agent_id, action in joint_actions.items():
            self.apply_action(agent_id, action)

        # 2. Simulate scenario-specific attack progression
        events = self._simulate_attacker_step()

        # 3. Snapshot segments after actions & attack progression
        self.after_segments = {k: dict(v) for k, v in self.segments.items()}

        # 4. Calculate cooperative rewards with clear breakdown
        rewards, breakdown = self._calculate_rewards(joint_actions)
        self.last_reward_breakdown = breakdown

        done = self.step_count >= self.max_steps or self.critical_resource["compromised"] or self.contained

        state = self.get_state()
        return state, rewards, done, {"events": events, "reward_breakdown": breakdown}

    def _simulate_attacker_step(self) -> List[Dict[str, Any]]:
        events = []
        segA = self.segments["Segment A"]
        segB = self.segments["Segment B"]
        segC = self.segments["Segment C"]

        # === Scenario 1: Single Segment Anomaly ===
        if self.scenario == "Scenario 1":
            if self.attack_stage == "NORMAL":
                self.attack_stage = "RECONNAISSANCE"
                self.attacker_location = "Segment A"
                segA["threat_level"] = 0.55
                events.append({"type": "ATTACK", "desc": "Port scanning detected on Segment A"})
            elif self.attack_stage == "RECONNAISSANCE":
                if segA["isolated"] or segA["threat_level"] < 0.2:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment A attack contained by defender!"})
                else:
                    self.attack_stage = "INITIAL COMPROMISE"
                    segA["compromised"] = True
                    segA["threat_level"] = 0.85
                    events.append({"type": "ATTACK", "desc": "Segment A host compromised!"})
            elif self.attack_stage == "INITIAL COMPROMISE":
                if segA["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment A isolated; anomaly quarantined."})
                else:
                    segA["threat_level"] = 0.95

        # === Scenario 2: Lateral Movement ===
        elif self.scenario == "Scenario 2":
            if self.attack_stage == "NORMAL":
                self.attack_stage = "RECONNAISSANCE"
                self.attacker_location = "Segment A"
                segA["threat_level"] = 0.45
                events.append({"type": "ATTACK", "desc": "External reconnaissance against Segment A."})

            elif self.attack_stage == "RECONNAISSANCE":
                if segA["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment A isolated early; lateral attack thwarted!"})
                else:
                    self.attack_stage = "INITIAL COMPROMISE"
                    segA["compromised"] = True
                    segA["threat_level"] = 0.85
                    events.append({"type": "ATTACK", "desc": "Segment A compromised! Attacker establishing foothold."})

            elif self.attack_stage == "INITIAL COMPROMISE":
                if segA["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment A quarantined; lateral pivot prevented."})
                elif segB["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment B isolated preemptively; lateral movement blocked!"})
                else:
                    self.attack_stage = "LATERAL MOVEMENT"
                    self.attacker_location = "Segment B"
                    segB["threat_level"] = 0.75
                    events.append({"type": "ATTACK", "desc": "Attacker pivoted laterally into Segment B!"})

            elif self.attack_stage == "LATERAL MOVEMENT":
                if segB["isolated"] or (segB["threat_level"] < 0.3):
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment B defender successfully contained lateral threat!"})
                elif segC["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment C isolated; access to Critical Server denied!"})
                else:
                    self.attack_stage = "TARGET ATTEMPT"
                    self.attacker_location = "Segment C"
                    segB["compromised"] = True
                    segC["threat_level"] = 0.92
                    events.append({"type": "ATTACK", "desc": "Attacker bypassed Segment B, targeting Critical Server in Segment C!"})

            elif self.attack_stage == "TARGET ATTEMPT":
                if segC["isolated"] or segC["threat_level"] < 0.3:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment C defender blocked target breach at critical gateway!"})
                else:
                    self.critical_resource["compromised"] = True
                    self.attack_stage = "COMPROMISED"
                    events.append({"type": "ATTACK", "desc": "CRITICAL SERVER COMPROMISED!"})

        # === Scenario 3: Distributed Attack ===
        elif self.scenario == "Scenario 3":
            if self.attack_stage == "NORMAL":
                self.attack_stage = "RECONNAISSANCE"
                self.attacker_location = "Segments A & B"
                segA["threat_level"] = 0.50
                segB["threat_level"] = 0.50
                events.append({"type": "ATTACK", "desc": "Distributed scanning detected simultaneously on Segments A & B"})
            elif self.attack_stage == "RECONNAISSANCE":
                if segA["isolated"] and segB["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Both target segments isolated; distributed attack neutralized."})
                else:
                    self.attack_stage = "LATERAL MOVEMENT"
                    if not segA["isolated"]: segA["threat_level"] = 0.8
                    if not segB["isolated"]: segB["threat_level"] = 0.85
                    events.append({"type": "ATTACK", "desc": "Dual penetration into internal segments."})
            elif self.attack_stage == "LATERAL MOVEMENT":
                if (segA["isolated"] or segA["threat_level"] < 0.3) and (segB["isolated"] or segB["threat_level"] < 0.3):
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Coordinated defensive action contained multi-segment threat."})
                elif segC["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Segment C isolated; gateway protected."})
                else:
                    self.attack_stage = "TARGET ATTEMPT"
                    self.attacker_location = "Segment C"
                    segC["threat_level"] = 0.95
                    events.append({"type": "ATTACK", "desc": "Distributed threat converged on Segment C!"})
            elif self.attack_stage == "TARGET ATTEMPT":
                if segC["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                else:
                    self.critical_resource["compromised"] = True
                    self.attack_stage = "COMPROMISED"

        # === Scenario 4: Multiple Simultaneous Threats ===
        elif self.scenario == "Scenario 4":
            if self.attack_stage == "NORMAL":
                self.attack_stage = "INITIAL COMPROMISE"
                self.attacker_location = "Segments A & C"
                segA["threat_level"] = 0.70
                segC["threat_level"] = 0.70
                events.append({"type": "ATTACK", "desc": "Simultaneous multi-vector breach on edge and core networks!"})
            elif self.attack_stage == "INITIAL COMPROMISE":
                if segA["isolated"] and segC["isolated"]:
                    self.attack_stage = "CONTAINED"
                    self.contained = True
                    events.append({"type": "DEFENSE", "desc": "Multi-agent isolation suppressed concurrent intrusions."})
                else:
                    self.attack_stage = "TARGET ATTEMPT"
                    if not segC["isolated"]:
                        self.critical_resource["compromised"] = True
                        self.attack_stage = "COMPROMISED"
                    else:
                        self.attack_stage = "CONTAINED"
                        self.contained = True

        return events

    def _calculate_rewards(self, joint_actions: Dict[str, str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Cooperative reward decomposition:
        - Detection: +10.0 for detecting high threat and taking action (BLOCK/ISOLATE/ALERT)
        - Containment: +15.0 when system reaches CONTAINED state
        - Attack progression penalty: -10.0 for lateral step, -50.0 for critical server loss
        - False action penalty: -5.0 for isolating a healthy segment (<0.2 threat)
        """
        detection_reward = 0.0
        containment_reward = 0.0
        attack_penalty = 0.0
        false_action_penalty = 0.0

        if self.contained:
            containment_reward = 15.0

        if self.critical_resource["compromised"]:
            attack_penalty -= 50.0
        elif self.attack_stage in ["LATERAL MOVEMENT", "TARGET ATTEMPT"]:
            attack_penalty -= 10.0

        mapping = {"Agent 1": "Segment A", "Agent 2": "Segment B", "Agent 3": "Segment C"}
        agent_rewards = {}

        for agent_id, action in joint_actions.items():
            seg_name = mapping.get(agent_id, "Segment A")
            threat = self.segments[seg_name]["threat_level"]
            agent_det = 0.0
            agent_false = 0.0

            if threat >= 0.5 and action in ["BLOCK", "ISOLATE", "ALERT"]:
                agent_det += 10.0
            elif threat < 0.2 and action == "ISOLATE":
                agent_false -= 5.0

            detection_reward += agent_det
            false_action_penalty += agent_false

            total_agent = agent_det + agent_false + (attack_penalty / 3.0) + (containment_reward / 3.0)
            agent_rewards[agent_id] = round(total_agent, 2)

        total_reward = round(detection_reward + containment_reward + attack_penalty + false_action_penalty, 2)
        breakdown = {
            "detection": round(detection_reward, 2),
            "containment": round(containment_reward, 2),
            "attack_penalty": round(attack_penalty, 2),
            "false_action_penalty": round(false_action_penalty, 2),
            "total": total_reward
        }

        return agent_rewards, breakdown
