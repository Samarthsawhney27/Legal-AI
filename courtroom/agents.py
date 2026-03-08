# courtroom/agents.py

import os
import ollama
from dotenv import load_dotenv
from courtroom.prompts import (
    PROSECUTOR_SYSTEM_PROMPT,
    DEFENSE_SYSTEM_PROMPT,
    JUDGE_SYSTEM_PROMPT,
)

load_dotenv()

OLLAMA_MODEL = os.environ.get("MODEL", "llama3.2")


def build_prosecutor_message(
    case: str,
    legal_context: str,
    precedent_context: str = "",
) -> list:
    return [
        {"role": "system", "content": PROSECUTOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
CASE BEFORE THE COURT:
{case}

STATUTORY LEGAL CONTEXT (cite these sections):
{legal_context}

{precedent_context}

Present your prosecution arguments now.
Cite both statutory sections AND past judgments as precedents.
            """,
        },
    ]


def build_defense_message(
    case: str,
    legal_context: str,
    prosecution_argument: str,
    precedent_context: str = "",
) -> list:
    return [
        {"role": "system", "content": DEFENSE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
CASE BEFORE THE COURT:
{case}

STATUTORY LEGAL CONTEXT (cite these sections):
{legal_context}

{precedent_context}

PROSECUTION HAS ARGUED:
{prosecution_argument}

Present your defense. Counter prosecution arguments.
Where prosecution cited a precedent, find a counter-precedent or
distinguish the facts from that case.
            """,
        },
    ]


def build_judge_message(case: str, prosecution: str, defense: str) -> list:
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
CASE BEFORE THE COURT:
{case}

PROSECUTION ARGUED:
{prosecution}

DEFENSE ARGUED:
{defense}

Deliver your observations and verdict.
            """,
        },
    ]


def stream_agent(messages: list):
    """
    Generator function that streams response token by token from Ollama.
    Use with Streamlit's st.write_stream()
    """
    stream = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token


def run_agent_no_stream(messages: list) -> str:
    """Non-streaming version for getting full response at once."""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        stream=False,
    )
    return response["message"]["content"]
