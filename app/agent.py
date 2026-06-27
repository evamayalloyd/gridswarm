# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import google_search
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

MODEL = "gemini-3.5-flash"


def _model() -> Gemini:
    return Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


# --- Sub-agent A: Researcher (Google Search only) ---
researcher_agent = Agent(
    name="researcher_agent",
    model=_model(),
    instruction=(
        "You are the Researcher in an urban energy planning swarm. "
        "Use Google Search to find current, concrete figures for renewable "
        "energy planning: typical solar capacity factor, wind capacity factor, "
        "average household electricity demand (kWh/year), and current panel/turbine "
        "output assumptions. Return a short, bulleted list of the numbers you found "
        "with one-line sources. Do not do any math, only gather facts."
    ),
    tools=[google_search],
)

# --- Sub-agent B: Modeler (code execution only) ---
modeler_agent = Agent(
    name="modeler_agent",
    model=_model(),
    instruction=(
        "You are the Modeler in an urban energy planning swarm. "
        "You will receive researched figures and a target city population. "
        "Write and execute Python to compute: total annual electricity demand, "
        "the number of solar panels and wind turbines needed to meet it, a "
        "reasonable solar/wind generation split, and land-area estimates. "
        "Show the computed numbers clearly. Do not search the web, only compute "
        "from the figures provided."
    ),
    code_executor=BuiltInCodeExecutor(),
)

# --- Sub-agent C: Reporter (formatting only, no tools) ---
reporter_agent = Agent(
    name="reporter_agent",
    model=_model(),
    instruction=(
        "You are the Reporter in an urban energy planning swarm. "
        "Take the researched figures and the modeled results and synthesize them "
        "into one clean, well-structured markdown report titled 'Renewable Energy "
        "Plan'. Include sections: Assumptions, Demand, Recommended Generation Mix, "
        "Land and Build-out, and Caveats. Be concise and concrete. Add no new numbers "
        "that were not provided to you."
    ),
)

# --- Coordinator (root): decomposes and delegates in order ---
root_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[researcher_agent, modeler_agent, reporter_agent],
)

app = App(
    root_agent=root_agent,
    name="app",
)