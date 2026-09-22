from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models
from typing import Dict, Any, List, Optional
import datetime

# --- Episode Operations ---
def create_episode(db: Session, scenario: str, mode: str) -> models.Episode:
    db_episode = models.Episode(scenario=scenario, mode=mode, total_reward=0.0)
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    return db_episode

def finish_episode(db: Session, episode_id: int, total_reward: float, outcome: str):
    ep = db.query(models.Episode).filter(models.Episode.id == episode_id).first()
    if ep:
        ep.end_time = datetime.datetime.now()
        ep.total_reward = total_reward
        ep.outcome = outcome
        db.commit()

def get_episodes(db: Session, limit: int = 15) -> List[models.Episode]:
    return db.query(models.Episode).order_by(desc(models.Episode.id)).limit(limit).all()

# --- Agent Operations ---
def get_or_create_agent(db: Session, name: str, segment: str) -> models.Agent:
    agent = db.query(models.Agent).filter(models.Agent.name == name).first()
    if not agent:
        agent = models.Agent(name=name, assigned_segment=segment, status="MONITORING")
        db.add(agent)
        db.commit()
        db.refresh(agent)
    return agent

# --- Event Logging ---
def log_event(db: Session, episode_id: int, step: int, event_type: str, details: Dict[str, Any]):
    db_event = models.EnvironmentEvent(
        episode_id=episode_id,
        step=step,
        event_type=event_type,
        source=details.get("source"),
        target=details.get("target"),
        segment=details.get("segment"),
        threat_level=str(details.get("threat_level", "0.0")),
        description=details.get("description")
    )
    db.add(db_event)
    db.commit()

def get_events(db: Session, episode_id: Optional[int] = None, event_type: Optional[str] = None, limit: int = 50):
    q = db.query(models.EnvironmentEvent)
    if episode_id:
        q = q.filter(models.EnvironmentEvent.episode_id == episode_id)
    if event_type and event_type != "ALL":
        q = q.filter(models.EnvironmentEvent.event_type == event_type)
    return q.order_by(desc(models.EnvironmentEvent.id)).limit(limit).all()

# --- Observation Logging ---
def log_observation(db: Session, episode_id: int, step: int, agent_id: int, obs_data: Dict[str, Any], threat_score: float):
    db_obs = models.AgentObservation(
        episode_id=episode_id,
        step=step,
        agent_id=agent_id,
        observation_data=obs_data,
        threat_score=threat_score
    )
    db.add(db_obs)
    db.commit()

# --- Action Logging ---
def log_action(db: Session, episode_id: int, step: int, agent_id: int, action: str,
               probabilities: Optional[Dict[str, float]] = None, result: Optional[str] = None):
    db_action = models.AgentAction(
        episode_id=episode_id,
        step=step,
        agent_id=agent_id,
        selected_action=action,
        action_probabilities=probabilities,
        result=result
    )
    db.add(db_action)
    db.commit()

# --- Communication Logging ---
def log_communication(db: Session, episode_id: int, step: int, sender: str, receiver: str,
                      msg_type: str, content: Dict[str, Any], threat_level: str):
    db_comm = models.CommunicationEvent(
        episode_id=episode_id,
        step=step,
        sender_agent=sender,
        receiver_agent=receiver,
        message_type=msg_type,
        message_content=content,
        threat_level=threat_level
    )
    db.add(db_comm)
    db.commit()

def get_communications(db: Session, episode_id: Optional[int] = None, limit: int = 30):
    q = db.query(models.CommunicationEvent)
    if episode_id:
        q = q.filter(models.CommunicationEvent.episode_id == episode_id)
    return q.order_by(desc(models.CommunicationEvent.id)).limit(limit).all()

# --- Reward Logging ---
def log_reward(db: Session, episode_id: int, step: int, agent_id: int,
               detection_r: float, containment_r: float, attack_p: float, false_p: float, total_r: float):
    db_reward = models.Reward(
        episode_id=episode_id,
        step=step,
        agent_id=agent_id,
        detection_reward=detection_r,
        containment_reward=containment_r,
        attack_penalty=attack_p,
        false_action_penalty=false_p,
        total_reward=total_r
    )
    db.add(db_reward)
    db.commit()

# --- Training Run Operations ---
def record_training_run(db: Session, episodes: int, final_metrics: Dict[str, Any]):
    tr = models.TrainingRun(
        algorithm="MAPPO",
        configuration={"gamma": 0.99, "clip_param": 0.2, "architecture": "CTDE"},
        number_of_episodes=episodes,
        final_metrics=final_metrics,
        end_time=datetime.datetime.now()
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr

def get_training_runs(db: Session, limit: int = 10):
    return db.query(models.TrainingRun).order_by(desc(models.TrainingRun.id)).limit(limit).all()

# --- Checkpoint Operations ---
def record_checkpoint(db: Session, model_path: str, episode: int, reward: float):
    chk = models.ModelCheckpoint(
        algorithm="MAPPO",
        model_path=model_path,
        episode=episode,
        reward=reward
    )
    db.add(chk)
    db.commit()
    db.refresh(chk)
    return chk

def get_checkpoints(db: Session, limit: int = 10):
    return db.query(models.ModelCheckpoint).order_by(desc(models.ModelCheckpoint.id)).limit(limit).all()
