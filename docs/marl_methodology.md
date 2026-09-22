# MARL Methodology (MAPPO & CTDE)

This project leverages Multi-Agent Proximal Policy Optimization (MAPPO) with Centralized Training and Decentralized Execution (CTDE) as outlined in the foundational research paper.

## 1. Mathematical Formulation
The environment operates as a cooperative Dec-POMDP:
`G = <N, S, {O_i}, {A_i}, P, R, γ>`
Where:
- **N**: Number of agents (3).
- **O_i**: Local observation of agent `i`.
- **A_i**: Discrete action space (MONITOR, ALERT, BLOCK, ISOLATE).
- **R**: Global cooperative reward function penalizing compromises and rewarding timely containment.

## 2. Centralized Critic
During training, a centralized critic network `V_φ(s)` assesses the global state `s` to compute advantage estimates `Â_t`. This mitigates the non-stationarity of concurrent multi-agent learning by stabilizing the variance in gradient updates.

## 3. Decentralized Actors
Each actor `π_θi(a_i | o_i)` learns a stochastic policy using the PPO clipped surrogate objective function:
`L_CLIP(θ) = E_t[ min( r_t(θ)Â_t, clip(r_t(θ), 1-ε, 1+ε)Â_t ) ]`
Agents rely entirely on their limited `O_i` during execution.

## 4. Cooperative Reward Function
Agents share a unified reward schema:
- **Detection**: +10.0 for isolating a segment with `threat_level > 0.7`.
- **Containment**: Success minimizes the target-compromise penalty.
- **False Positive Penalty**: -5.0 for isolating a healthy segment.
- **Target Loss**: -50.0 if the critical resource is compromised.
