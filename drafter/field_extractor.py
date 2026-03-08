# drafter/field_extractor.py
# Uses Ollama to extract all required fields from user's plain description

import json
import re
from datetime import datetime

import ollama

from drafter.document_types import DOCUMENT_TYPES

OLLAMA_MODEL = "llama3.2"


def extract_fields_for_document(
    user_description: str,
    document_type: str,
) -> dict:
    """
    Given a user's plain language description and confirmed document type,
    extract all required fields using Ollama.

    Returns a dict with all field values.
    Missing fields get value "NOT PROVIDED — please fill manually"
    """
    doc_config = DOCUMENT_TYPES[document_type]
    required = doc_config["required_fields"]
    today = datetime.today().strftime("%d %B %Y")
    ipc_sections = doc_config["ipc_sections"]

    prompt = f"""
You are an expert Indian legal document specialist.
A user wants to draft a {document_type} ({doc_config['full_name']}).

USER'S DESCRIPTION:
{user_description[:2000]}

TODAY'S DATE: {today}

RELEVANT LAW SECTIONS FOR THIS DOCUMENT TYPE:
{json.dumps(ipc_sections, indent=2)}

Extract ALL of the following fields from the user's description.
For fields not mentioned, write exactly: "NOT PROVIDED — please fill manually"
For date field, use today's date if not specified: {today}
For city/state, extract from description or write "NOT PROVIDED"

FIELDS TO EXTRACT:
{chr(10).join(f'- {field}' for field in required)}

ADDITIONAL FIELDS TO ALWAYS INCLUDE:
- applicable_sections: list the most relevant law sections from the 
  RELEVANT LAW SECTIONS above that apply to this specific case
- urgency_level: LOW / MEDIUM / HIGH based on severity of the issue
- estimated_compensation: if monetary relief is involved, estimate amount
  based on description, or write "As per actual loss"

Return ONLY valid JSON. No markdown, no backticks, no explanation.
Every field from the list above must be a key in the JSON.

Example format:
{{
  "complainant_name": "Extracted or NOT PROVIDED",
  "incident_description": "Formal description extracted...",
  "applicable_sections": ["IPC Section 420", "IPC Section 415"],
  "urgency_level": "HIGH",
  "estimated_compensation": "₹45,000"
}}
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        raw = response["message"]["content"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        extracted = json.loads(raw)

        # Ensure all required fields exist
        for field in required + [
            "applicable_sections",
            "urgency_level",
            "estimated_compensation",
        ]:
            if field not in extracted:
                extracted[field] = "NOT PROVIDED — please fill manually"

        extracted["_document_type"] = document_type
        extracted["_generated_date"] = today
        return extracted

    except json.JSONDecodeError:
        # Fallback — return empty template
        fallback = {
            field: "NOT PROVIDED — please fill manually" for field in required
        }
        fallback.update(
            {
                "applicable_sections": list(ipc_sections.values())[:3],
                "urgency_level": "MEDIUM",
                "estimated_compensation": "As per actual loss",
                "_document_type": document_type,
                "_generated_date": today,
            }
        )
        return fallback

    except Exception as e:
        fallback = {
            field: "NOT PROVIDED — please fill manually" for field in required
        }
        fallback["_error"] = str(e)
        fallback["_document_type"] = document_type
        fallback["_generated_date"] = today
        return fallback

