# Architecture

The Autonomous Cybersecurity Defense System is designed as a distributed multi-agent system where independent agents monitor individual network segments, communicate asynchronously, and use Multi-Agent Reinforcement Learning (MARL) to determine optimal joint defensive actions.

## 1. Network Simulation
The simulated environment represents a multi-segment network topology incorporating `Segment A`, `Segment B`, `Segment C`, and a `Critical Resource`. It supports configurable deterministic and stochastic transitions based on an internal `Attacker` state machine.

## 2. Defender Agents
Three independent `BaseDefenderAgent` instances observe local threat features (e.g., threat scores, node isolation status) and broadcast alerts to neighbors via the `CommunicationLayer`. 

## 3. Centralized Training, Decentralized Execution (CTDE)
Using the MAPPO algorithm, a centralized critic evaluates joint actions during training by observing the full global state. However, during execution, each agent acts purely on local observations and received messages, ensuring scalability and realistic SOC deployments.

## 4. Live Dashboard Visualization
The frontend React application maintains a continuous WebSocket stream with the FastAPI backend, offering real-time analytics on network topology, threat progression, MARL metrics, and agent communication packets.
