from typing import List, Dict, Any, Optional
import datetime
import uuid

class CommunicationLayer:
    def __init__(self, agents: List[Any]):
        self.agents = {agent.agent_id: agent for agent in agents}
        self.event_log: List[Dict[str, Any]] = []
        self.active_packets: List[Dict[str, Any]] = []

    def clear(self):
        self.event_log.clear()
        self.active_packets.clear()

    def broadcast(self, sender_id: str, message_type: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        sender_agent = self.agents.get(sender_id)
        if sender_agent:
            sender_agent.messages_sent += (len(self.agents) - 1)

        threat_val = float(content.get("threat_level", 0.0))
        if threat_val >= 0.75:
            threat_label = "CRITICAL"
        elif threat_val >= 0.5:
            threat_label = "HIGH"
        elif threat_val >= 0.2:
            threat_label = "MEDIUM"
        else:
            threat_label = "LOW"

        created_msgs = []
        now_ts = datetime.datetime.now().strftime("%H:%M:%S")

        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                msg = {
                    "id": str(uuid.uuid4())[:8],
                    "sender": sender_id,
                    "receiver": agent_id,
                    "timestamp": now_ts,
                    "message_type": message_type,
                    "threat_level": threat_label,
                    "threat_score": threat_val,
                    "segment": content.get("segment", "Unknown"),
                    "recommended_action": content.get("recommended_action", "BLOCK"),
                    "content": content
                }
                agent.receive_message(msg)
                self.event_log.append(msg)
                self.active_packets.append(msg)
                created_msgs.append(msg)

        # Keep active packets to most recent 10
        if len(self.active_packets) > 10:
            self.active_packets = self.active_packets[-10:]
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]

        return created_msgs

    def get_recent_messages(self, limit: int = 15) -> List[Dict[str, Any]]:
        return self.event_log[-limit:]

    def get_active_packets(self) -> List[Dict[str, Any]]:
        return list(self.active_packets)
