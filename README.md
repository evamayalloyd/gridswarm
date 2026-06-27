# GridSwarm — A2A Urban Energy Planning Swarm

A multi-agent **Agent-to-Agent (A2A)** system built on Google's **Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Runtime**. Given a target city population, GridSwarm orchestrates a team of specialized Gemini agents to research current energy data, model the required renewable infrastructure, and synthesize a complete build-out plan.

Built for the Gemini AI Hackathon (Google I/O 2026 stack).

---

## What it does

Ask GridSwarm to *"Design a renewable energy plan for a city of 100,000 residents"* and a coordinator dispatches three tool-isolated sub-agents in sequence:

1. **Researcher** — uses **Google Search** to gather current, sourced figures (solar/wind capacity factors, household demand, panel/turbine output).
2. **Modeler** — uses **code execution** to compute total demand, required generation capacity, panel/turbine counts, generation mix, and land-use estimates from the researched figures.
3. **Reporter** — synthesizes the research and the model output into a clean, structured Markdown report (Assumptions, Demand, Generation Mix, Land & Build-out, Caveats).

Each agent is restricted to a single capability, which keeps execution traces clean and prevents tool-routing confusion — a deliberate design choice for reliability.

---

## Architecture

```
                        ┌──────────────────────────┐
   user prompt  ───────▶│   Coordinator (root)     │
                        │   SequentialAgent        │
                        └───────────┬──────────────┘
                                    │ delegates in fixed order
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │  Researcher     │    │   Modeler        │    │   Reporter       │
   │  google_search  │───▶│  code execution  │───▶│  synthesis only  │
   └─────────────────┘    └──────────────────┘    └──────────────────┘
        sourced               computed                final report
        figures               numbers                 (Markdown)
```

The root uses ADK's `SequentialAgent` for deterministic orchestration — each sub-agent's output is passed forward as context to the next, guaranteeing the full research → model → report chain completes on every run.

---

## Google Cloud stack

| Layer | Service |
|-------|---------|
| Model | Gemini 3.5 Flash (`gemini-3.5-flash`) on Vertex AI |
| Framework | Agent Development Kit (ADK) |
| Tools | ADK `google_search`, built-in code executor |
| Deployment | Vertex AI Agent Runtime (Agent Engine) |
| Infrastructure | Terraform (service accounts, IAM, storage) |
| Observability | Cloud Trace + OpenTelemetry (enabled at deploy) |
| Protocol | A2A agent card (`.well-known/agent-card.json`) |

---

## Project layout

```
app/
  agent.py              # Coordinator + 3 sub-agents (the swarm)
  agent_engine_app.py   # Agent Runtime application wrapper
deployment/terraform/   # Infrastructure-as-code
tests/                  # Unit, integration, eval datasets
Dockerfile
pyproject.toml
```

---

## Run locally

```bash
# install dependencies
agents-cli install

# launch the interactive playground (ADK web UI)
agents-cli playground
# open the dev UI and send: "Design a renewable energy plan for a city of 100,000 residents"
```

Or a single-shot query:

```bash
agents-cli run "Design a renewable energy plan for a city of 100,000 residents"
```

## Deploy to Agent Runtime

```bash
agents-cli scaffold enhance --deployment-target agent_runtime
agents-cli deploy --project <YOUR_PROJECT_ID>
```

Deployment packages the agent, builds a container, pushes to Artifact Registry, and provisions a Vertex AI reasoning engine with Cloud Trace enabled. The output includes the Agent Runtime ID, Agent Card URL, and Console link.

---

## Example output (city of 100,000, US baseline)

- **Total annual demand:** 431,640 MWh/year
- **Solar (50%):** 100.97 MW → 168,285 panels (600W) → ~606 acres
- **Wind (50%):** 72.04 MW → 24 turbines (3.0 MW) → 24 acres net footprint

All figures computed at runtime by the Modeler agent from live-researched inputs, with a Caveats section noting exclusions (commercial/industrial load, storage, intermittency).

---

## Design notes

- **Tool isolation** — search and code execution are split across agents because ADK does not reliably combine the built-in search tool and code executor in a single agent; separating them also produces cleaner, more legible traces.
- **Deterministic orchestration** — `SequentialAgent` was chosen over LLM-driven handoffs after observing that coordinator-style delegation could stall after the first sub-agent. The sequential pipeline guarantees completion.
- **Observability-first** — telemetry is enabled at deploy so every run produces Cloud Trace spans for each agent and tool call, making the multi-agent flow inspectable in the Console.
