# Literature Review

This document summarizes the foundational research informing the Autonomous Cybersecurity Defense System.

## 1. Multi-Agent Reinforcement Learning in Cybersecurity
**Title**: *Multi-Agent Reinforcement Learning in Cybersecurity: From Fundamentals to Applications*  
**Authors**: Christoph R. Landolt et al. (arXiv:2505.19837v1, 2025)

**Findings**:
- Cybersecurity scenarios naturally map to Dec-POMDPs where network sensors possess partial observability.
- CTDE scales effectively by decoupling training stability from execution dependencies.
- Communication among agents strictly improves containment efficiency against distributed lateral attacks.

**Connection to Project**:
We adapt their MAPPO formulation to create a visual simulation, proving that local segment agents can collaboratively prevent lateral movement by sharing observations.

## 2. Automated SOC & Distributed Intrusion Detection
**Research Gap**: Existing solutions often centralize anomaly detection, creating a single point of failure and bottlenecking incident response.
**Our Approach**: We decentralize the decision-making step to individual agent nodes (Segments A, B, C) while maintaining a cooperative MARL training foundation.
