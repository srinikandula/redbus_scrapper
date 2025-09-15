import asyncio
from browser_use import Agent, ChatOpenAI
import time
import json

# Track step count
step_counter = 0

async def run_browser_use():
    global step_counter
    start_time = time.time()

    # LLM
    llm = ChatOpenAI(model="gpt-4.1-mini")

    # Callback for each step
    def on_step(event):
        global step_counter
        step_counter += 1

        usage = {
            "prompt_tokens": agent.token_cost_service.prompt_tokens,
            "completion_tokens": agent.token_cost_service.completion_tokens,
            "total_tokens": agent.token_cost_service.total_tokens,
            "usd_cost": agent.token_cost_service.total_cost,
        }

        print(
            f"\n🪙 Step {step_counter} Token Report:\n"
            f"   🔹 Prompt tokens: {usage['prompt_tokens']}\n"
            f"   🔹 Completion tokens: {usage['completion_tokens']}\n"
            f"   🔢 Total so far: {usage['total_tokens']}\n"
            f"   💰 Cost so far: ${usage['usd_cost']:.6f}"
        )

    # Create agent with callbacks
    agent = Agent(
        #task=(
        #    "Go to https://www.redbus.in. "
        #    "In the 'From' input, type Hyderabad, then select the first option from the dropdown. "
        #    "In the 'To' input, type Chennai, then select the first option from the dropdown. "
        #    "In the date picker, select today's date. "
        #    "Click the Search Buses button. "
        #    "Wait until the results list of buses is visible. "
        #    "Extract the first 10 buses with fields: bus_name, fare, rating. "
        #    "Return them strictly as JSON."
        #),
        task = (
        "Go to https://www.redbus.in. "
        "Find the 'From' input with placeholder 'FROM' and type Hyderabad, then select the first dropdown option. "
        "Find the 'To' input with placeholder 'TO' and type Chennai, then select the first dropdown option. "
        "Find the date picker input with id 'onward_cal' and select today's date. "
        "Click the button with id 'search_btn'. "
        "Wait until the bus results are visible, then extract the first 10 buses with fields: bus_name, fare, rating. "
        "Return them strictly as JSON."
        ),
        llm=llm,
        callbacks={"step": on_step},   # 👈 step hook
    )

    # Run agent
    result = await agent.run()

    # End timing
    elapsed = time.time() - start_time

    # Save final JSON result (if valid)
    try:
        with open("bus_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n📄 bus_results.json saved successfully.")
    except Exception:
        print("\n⚠️ Could not save result as JSON. Raw result below:")
        print(result)

    # Final token + cost summary
    usage = {
        "prompt_tokens": agent.token_cost_service.prompt_tokens,
        "completion_tokens": agent.token_cost_service.completion_tokens,
        "total_tokens": agent.token_cost_service.total_tokens,
        "usd_cost": agent.token_cost_service.total_cost,
    }

    print("\n📊 Execution Summary:")
    print(f"  ⏱️ Time taken: {elapsed:.2f} seconds")
    print(f"  🔹 Prompt tokens: {usage['prompt_tokens']}")
    print(f"  🔹 Completion tokens: {usage['completion_tokens']}")
    print(f"  🔢 Total tokens: {usage['total_tokens']}")
    print(f"  💰 Total cost: ${usage['usd_cost']:.6f}")


if __name__ == "__main__":
    asyncio.run(run_browser_use())

