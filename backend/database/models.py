from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    assigned_segment = Column(String)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    scenario = Column(String)
    mode = Column(String)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_reward = Column(Float, default=0.0)
    outcome = Column(String, nullable=True)

class EnvironmentEvent(Base):
    __tablename__ = "environment_events"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    step = Column(Integer)
    event_type = Column(String)
    source = Column(String, nullable=True)
    target = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    threat_level = Column(String, nullable=True)
    description = Column(Text, nullable=True)

class AgentObservation(Base):
    __tablename__ = "agent_observations"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    step = Column(Integer)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    observation_data = Column(JSON)
    threat_score = Column(Float)

class AgentAction(Base):
    __tablename__ = "agent_actions"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    step = Column(Integer)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    selected_action = Column(String)
    action_probabilities = Column(JSON, nullable=True)
    result = Column(String, nullable=True)

class CommunicationEvent(Base):
    __tablename__ = "communication_events"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    step = Column(Integer)
    sender_agent = Column(String)
    receiver_agent = Column(String)
    message_type = Column(String)
    message_content = Column(JSON)
    threat_level = Column(String)

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    step = Column(Integer)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    detection_reward = Column(Float, default=0.0)
    containment_reward = Column(Float, default=0.0)
    attack_penalty = Column(Float, default=0.0)
    false_action_penalty = Column(Float, default=0.0)
    total_reward = Column(Float, default=0.0)

class TrainingRun(Base):
    __tablename__ = "training_runs"
    id = Column(Integer, primary_key=True, index=True)
    algorithm = Column(String)
    configuration = Column(JSON)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    number_of_episodes = Column(Integer, default=0)
    final_metrics = Column(JSON, nullable=True)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String)
    scenario = Column(String)
    episodes = Column(Integer)
    metrics = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ModelCheckpoint(Base):
    __tablename__ = "model_checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    algorithm = Column(String)
    model_path = Column(String)
    episode = Column(Integer)
    reward = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
