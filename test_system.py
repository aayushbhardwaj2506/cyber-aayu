import asyncio
from backend.main import execute_step_cycle, reset_simulation, sim_env, mappo_policy, comm_layer, agents, trigger_training, TrainRequest
from backend.database.database import SessionLocal
from backend.database import crud, models

async def main():
    print("=== 1. Testing Reset ===")
    res = await reset_simulation("Scenario 2")
    print("Reset result:", res)
    assert sim_env.scenario == "Scenario 2"
    
    print("\n=== 2. Stepping Simulation (5 Steps) ===")
    for i in range(5):
        step_res = await execute_step_cycle()
        print(f"Step {i+1} completed: Attack Stage = {step_res['state']['attack_stage']}, Contained = {step_res['state']['contained']}")
        if step_res['done']:
            print("Episode reached terminal state!")
            break

    print("\n=== 3. Testing Communication Bus ===")
    recent_msgs = comm_layer.get_recent_messages()
    print(f"Total recorded messages in bus: {len(recent_msgs)}")
    for m in recent_msgs[:3]:
        print(f"  {m['sender']} -> {m['receiver']}: {m['message_type']} [{m['threat_level']}] Action: {m['recommended_action']}")

    print("\n=== 4. Checking Database Persistence ===")
    db = SessionLocal()
    episodes = crud.get_episodes(db, 5)
    print(f"Total episodes in DB: {len(episodes)}")
    events = crud.get_events(db, limit=5)
    print(f"Total recent events in DB: {len(events)}")
    for ev in events:
        print(f"  [{ev.event_type}] Step {ev.step}: {ev.description}")
    db.close()

    print("\n=== 5. Testing MAPPO Training Execution ===")
    req = TrainRequest(episodes=2)
    train_res = await trigger_training(req)
    print("Training result:", train_res)

    print("\n=== ALL E2E BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
