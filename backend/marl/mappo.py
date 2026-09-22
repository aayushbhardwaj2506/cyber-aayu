import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

ACTION_MAP = {0: "MONITOR", 1: "ALERT", 2: "BLOCK", 3: "ISOLATE"}
REV_ACTION_MAP = {v: k for k, v in ACTION_MAP.items()}

class ActorNetwork(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 4, hidden_dim: int = 64):
        super(ActorNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
    def forward(self, obs: torch.Tensor) -> Categorical:
        logits = self.net(obs)
        return Categorical(logits=logits)

    def get_action_probs(self, obs: torch.Tensor) -> torch.Tensor:
        logits = self.net(obs)
        return torch.softmax(logits, dim=-1)

class CriticNetwork(nn.Module):
    def __init__(self, global_state_dim: int = 16, hidden_dim: int = 64):
        super(CriticNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(global_state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, global_state: torch.Tensor) -> torch.Tensor:
        return self.net(global_state)

class RolloutBuffer:
    def __init__(self):
        self.observations: List[torch.Tensor] = []
        self.global_states: List[torch.Tensor] = []
        self.actions: List[int] = []
        self.log_probs: List[torch.Tensor] = []
        self.rewards: List[float] = []
        self.dones: List[bool] = []
        self.values: List[torch.Tensor] = []

    def clear(self):
        self.observations.clear()
        self.global_states.clear()
        self.actions.clear()
        self.log_probs.clear()
        self.rewards.clear()
        self.dones.clear()
        self.values.clear()

    def add(self, obs: torch.Tensor, global_state: torch.Tensor, action: int,
            log_prob: torch.Tensor, reward: float, done: bool, value: torch.Tensor):
        self.observations.append(obs.detach())
        self.global_states.append(global_state.detach())
        self.actions.append(action)
        self.log_probs.append(log_prob.detach())
        self.rewards.append(reward)
        self.dones.append(done)
        self.values.append(value.detach())

    def compute_gae(self, next_value: float, gamma: float = 0.99, gae_lambda: float = 0.95):
        returns = []
        advantages = []
        gae = 0.0
        
        values = [v.item() if isinstance(v, torch.Tensor) else v for v in self.values] + [next_value]
        
        for step in reversed(range(len(self.rewards))):
            delta = self.rewards[step] + gamma * values[step + 1] * (1.0 - float(self.dones[step])) - values[step]
            gae = delta + gamma * gae_lambda * (1.0 - float(self.dones[step])) * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[step])
            
        return torch.tensor(returns, dtype=torch.float32), torch.tensor(advantages, dtype=torch.float32)

class CentralizedMAPPO:
    """
    MAPPO implementation with Centralized Training and Decentralized Execution (CTDE).
    - Decentralized Actors: 3 independent actors (or distinct networks per agent)
    - Centralized Critic: Single value function evaluating joint state S_t
    """
    def __init__(self, obs_dim: int = 4, action_dim: int = 4, global_state_dim: int = 16,
                 lr_actor: float = 3e-4, lr_critic: float = 1e-3,
                 gamma: float = 0.99, gae_lambda: float = 0.95,
                 clip_param: float = 0.2, entropy_coef: float = 0.01):
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.global_state_dim = global_state_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_param = clip_param
        self.entropy_coef = entropy_coef

        # 3 Decentralized Actors for Segment A, Segment B, Segment C
        self.agents = ["Agent 1", "Agent 2", "Agent 3"]
        self.actors = {
            agent_id: ActorNetwork(obs_dim, action_dim) for agent_id in self.agents
        }
        self.actor_optimizers = {
            agent_id: optim.Adam(self.actors[agent_id].parameters(), lr=lr_actor) for agent_id in self.agents
        }

        # Centralized Critic
        self.critic = CriticNetwork(global_state_dim)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr_critic)

        # Buffers per agent
        self.buffers = {agent_id: RolloutBuffer() for agent_id in self.agents}
        self.training_metrics = {
            "actor_loss": 0.0,
            "critic_loss": 0.0,
            "entropy": 0.0,
            "kl": 0.0,
            "episode_rewards": []
        }

    def _extract_obs_tensor(self, obs: Dict, inbox: List) -> torch.Tensor:
        threat = float(obs.get("threat_level", 0.0))
        isolated = 1.0 if obs.get("isolated", False) else 0.0
        compromised = 1.0 if obs.get("compromised", False) else 0.0
        has_alert = 1.0 if any(msg.get("message_type") == "THREAT_ALERT" for msg in (inbox or [])) else 0.0
        return torch.tensor([threat, isolated, compromised, has_alert], dtype=torch.float32)

    def extract_global_state_tensor(self, env_state: Dict) -> torch.Tensor:
        features = []
        segments = env_state.get("segments", {})
        for name in ["Segment A", "Segment B", "Segment C"]:
            seg = segments.get(name, {})
            features.extend([
                float(seg.get("threat_level", 0.0)),
                1.0 if seg.get("isolated", False) else 0.0,
                1.0 if seg.get("compromised", False) else 0.0,
                1.0 if env_state.get("attacker_location") == name else 0.0
            ])
        # 12 segment features + critical server status + attack stage numeric + step ratio + dummy
        crit = env_state.get("critical_resource", {})
        features.append(1.0 if crit.get("compromised", False) else 0.0)

        stage_map = {
            "NORMAL": 0.0, "RECONNAISSANCE": 0.2, "INITIAL COMPROMISE": 0.4,
            "LATERAL MOVEMENT": 0.6, "TARGET ATTEMPT": 0.8, "CONTAINED": 1.0, "COMPROMISED": 1.0
        }
        stage = env_state.get("attack_stage", "NORMAL")
        features.append(stage_map.get(stage, 0.0))

        step = float(env_state.get("step", 0)) / 100.0
        features.append(step)

        # Pad or slice to exactly global_state_dim (16)
        while len(features) < self.global_state_dim:
            features.append(0.0)
        return torch.tensor(features[:self.global_state_dim], dtype=torch.float32)

    def get_action_and_probs(self, agent_id: str, obs: Dict, inbox: List) -> Tuple[str, Dict[str, float], torch.Tensor, torch.Tensor]:
        actor = self.actors.get(agent_id, self.actors["Agent 1"])
        obs_t = self._extract_obs_tensor(obs, inbox)
        
        with torch.no_grad():
            dist = actor(obs_t)
            probs = actor.get_action_probs(obs_t).cpu().numpy().tolist()
            action_idx = dist.sample()
            log_prob = dist.log_prob(action_idx)
            
        prob_dict = {ACTION_MAP[i]: round(float(probs[i]), 4) for i in range(len(probs))}
        action_str = ACTION_MAP.get(action_idx.item(), "MONITOR")
        return action_str, prob_dict, log_prob, obs_t

    def get_value(self, global_state_t: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            val = self.critic(global_state_t)
        return val.squeeze()

    def store_transition(self, agent_id: str, obs_t: torch.Tensor, global_state_t: torch.Tensor,
                         action_str: str, log_prob: torch.Tensor, reward: float, done: bool, value: torch.Tensor):
        action_idx = REV_ACTION_MAP.get(action_str, 0)
        self.buffers[agent_id].add(obs_t, global_state_t, action_idx, log_prob, reward, done, value)

    def train_step(self, next_global_state_t: torch.Tensor, epochs: int = 4, batch_size: int = 32) -> Dict[str, float]:
        total_actor_loss = 0.0
        total_critic_loss = 0.0
        total_entropy = 0.0
        agent_count = 0

        next_val = self.get_value(next_global_state_t).item()

        for agent_id in self.agents:
            buffer = self.buffers[agent_id]
            if len(buffer.observations) == 0:
                continue

            returns, advantages = buffer.compute_gae(next_val, self.gamma, self.gae_lambda)
            # Normalize advantages
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            obs_batch = torch.stack(buffer.observations)
            actions_batch = torch.tensor(buffer.actions, dtype=torch.long)
            old_log_probs_batch = torch.stack(buffer.log_probs)
            global_states_batch = torch.stack(buffer.global_states)

            actor = self.actors[agent_id]
            actor_opt = self.actor_optimizers[agent_id]

            for _ in range(epochs):
                # Actor update
                dist = actor(obs_batch)
                new_log_probs = dist.log_prob(actions_batch)
                entropy = dist.entropy().mean()

                ratio = torch.exp(new_log_probs - old_log_probs_batch)
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1.0 - self.clip_param, 1.0 + self.clip_param) * advantages
                actor_loss = -torch.min(surr1, surr2).mean() - self.entropy_coef * entropy

                actor_opt.zero_grad()
                actor_loss.backward()
                nn.utils.clip_grad_norm_(actor.parameters(), 0.5)
                actor_opt.step()

                # Critic update (Centralized)
                pred_values = self.critic(global_states_batch).squeeze(-1)
                critic_loss = nn.MSELoss()(pred_values, returns)

                self.critic_optimizer.zero_grad()
                critic_loss.backward()
                nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
                self.critic_optimizer.step()

                total_actor_loss += actor_loss.item()
                total_critic_loss += critic_loss.item()
                total_entropy += entropy.item()

            buffer.clear()
            agent_count += 1

        if agent_count > 0:
            divisor = agent_count * epochs
            self.training_metrics["actor_loss"] = round(total_actor_loss / divisor, 4)
            self.training_metrics["critic_loss"] = round(total_critic_loss / divisor, 4)
            self.training_metrics["entropy"] = round(total_entropy / divisor, 4)

        return self.training_metrics

    def save_checkpoint(self, filepath: str, episode: int, total_reward: float):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        checkpoint = {
            "episode": episode,
            "total_reward": total_reward,
            "critic_state_dict": self.critic.state_dict(),
            "actors_state_dict": {agent_id: self.actors[agent_id].state_dict() for agent_id in self.agents},
            "metrics": self.training_metrics
        }
        torch.save(checkpoint, filepath)

    def load_checkpoint(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False
        checkpoint = torch.load(filepath, map_location=torch.device("cpu"))
        self.critic.load_state_dict(checkpoint["critic_state_dict"])
        for agent_id in self.agents:
            if agent_id in checkpoint["actors_state_dict"]:
                self.actors[agent_id].load_state_dict(checkpoint["actors_state_dict"][agent_id])
        return True

# Backwards compatible alias
MAPPOAgent = CentralizedMAPPO
