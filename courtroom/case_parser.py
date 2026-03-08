import json
import re
from typing import Dict

import ollama

OLLAMA_MODEL = "llama3.2"

ALL_CASE_TYPES = [
    # Contract / Civil
    "Contract Breach",
    "Landlord-Tenant Dispute",
    "Employment Contract Dispute",
    "Property Sale Agreement Dispute",
    "Specific Performance of Contract",
    "Coercion / Misrepresentation in Contract",
    # Constitutional
    "Fundamental Rights Violation (Government Action)",
    "Arbitrary State Action (Article 14)",
    # Criminal / IPC
    "Criminal / IPC",
    "Assault / Hurt",
    "Theft / Robbery",
    "Cheating / Fraud (Criminal)",
    "Murder / Culpable Homicide",
    # Consumer
    "Consumer Rights / Defective Product",
    "E-commerce Fraud / Online Shopping",
    "Service Deficiency",
    "Misleading Advertisement",
    "Medical Negligence (Consumer)",
    # Fallback
    "General Legal Dispute",
]

CASE_TYPE_DESCRIPTIONS = {
    "Contract Breach": "One party violated terms of a signed agreement",
    "Landlord-Tenant Dispute": "Dispute between property owner and tenant",
    "Employment Contract Dispute": "Employer violated employment contract terms",
    "Property Sale Agreement Dispute": "Buyer/seller dispute over property purchase agreement",
    "Specific Performance of Contract": "Seeking court order to force completion of a contract",
    "Coercion / Misrepresentation in Contract": "Contract signed under pressure or based on false information",
    "Fundamental Rights Violation (Government Action)": "Government/state violated a citizen's fundamental rights",
    "Arbitrary State Action (Article 14)": "Government acted arbitrarily violating equality before law",
    "Criminal / IPC": "General criminal matter under Indian Penal Code",
    "Assault / Hurt": "Physical attack causing injury — IPC Section 319-326",
    "Theft / Robbery": "Stealing of property — IPC Section 378-395",
    "Cheating / Fraud (Criminal)": "Criminal deception causing wrongful loss — IPC Section 415-420",
    "Murder / Culpable Homicide": "Unlawful killing — IPC Section 299-304",
    "Consumer Rights / Defective Product": "Defective goods sold to consumer",
    "E-commerce Fraud / Online Shopping": "Fake/wrong product delivered, refund denied",
    "Service Deficiency": "Service provider failed to deliver promised service",
    "Misleading Advertisement": "False advertising caused consumer harm",
    "Medical Negligence (Consumer)": "Doctor/hospital caused harm through negligence",
    "General Legal Dispute": "Does not fit other categories clearly",
}

CASE_BOOKS_HINT = {
    "Contract Breach": "📋 Contract + 📜 Constitution",
    "Landlord-Tenant Dispute": "📋 Contract + 📜 Constitution",
    "Employment Contract Dispute": "📋 Contract + 📜 Constitution",
    "Property Sale Agreement Dispute": "📋 Contract + 📜 Constitution",
    "Specific Performance of Contract": "📋 Contract + 📜 Constitution",
    "Coercion / Misrepresentation in Contract": "📋 Contract + 📜 Constitution",
    "Fundamental Rights Violation (Government Action)": "📜 Constitution + ⚔️ IPC",
    "Arbitrary State Action (Article 14)": "📜 Constitution + 📋 Contract",
    "Criminal / IPC": "⚔️ IPC + 📜 Constitution",
    "Assault / Hurt": "⚔️ IPC",
    "Theft / Robbery": "⚔️ IPC",
    "Cheating / Fraud (Criminal)": "⚔️ IPC + 🛒 Consumer",
    "Murder / Culpable Homicide": "⚔️ IPC",
    "Consumer Rights / Defective Product": "🛒 Consumer + 📜 Constitution",
    "E-commerce Fraud / Online Shopping": "🛒 Consumer + ⚔️ IPC",
    "Service Deficiency": "🛒 Consumer + 📜 Constitution",
    "Misleading Advertisement": "🛒 Consumer + ⚔️ IPC",
    "Medical Negligence (Consumer)": "🛒 Consumer + 📜 Constitution",
    "General Legal Dispute": "All books",
}


def extract_case_details(raw_input: str) -> Dict:
    """
    Takes ANY raw text and extracts structured case details.
    Returns accused, victim, location, incident, ai_suggested_case_type,
    suggestion_reason, confidence, missing_info.
    Does NOT finalize case_type — user must confirm manually.
    """
    prompt = f"""
You are an expert Indian legal clerk who structures legal complaints.
Analyze this raw case description and extract structured information.

RAW INPUT:
{raw_input[:2000]}

AVAILABLE CASE TYPES:
{chr(10).join(f'- {ct}: {desc}' 
  for ct, desc in CASE_TYPE_DESCRIPTIONS.items())}

Return ONLY valid JSON. No markdown, no backticks, no explanation:

{{
  "accused": "full name and role of accused, 
              or best guess like 'Employer (name unknown)' if unclear",
  "victim": "full name and role of complainant/victim,
             or best guess like 'Employee (name unknown)' if unclear",
  "location": "city and state if mentioned, else 'India'",
  "incident": "3-5 sentence FORMAL legal description in third person.
               Include: what happened, when approximately,
               what legal right was violated, what remedy is sought.
               Write formally even if input was casual or Hindi-English.",
  "ai_suggested_case_type": "single most matching case type from list above",
  "suggestion_reason": "one sentence explaining why you suggest this type",
  "confidence": "HIGH if all fields clear / MEDIUM if some guessed / LOW if vague",
  "missing_info": ["fields that were unclear or completely missing"]
}}
"""
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        raw_json = response["message"]["content"].strip()
        raw_json = re.sub(r"^```json\s*", "", raw_json)
        raw_json = re.sub(r"^```\s*", "", raw_json)
        raw_json = re.sub(r"\s*```$", "", raw_json)
        raw_json = raw_json.strip()

        parsed = json.loads(raw_json)

        required = [
            "accused",
            "victim",
            "location",
            "incident",
            "ai_suggested_case_type",
            "suggestion_reason",
            "confidence",
            "missing_info",
        ]
        for key in required:
            if key not in parsed:
                parsed[key] = (
                    []
                    if key == "missing_info"
                    else "General Legal Dispute"
                    if key == "ai_suggested_case_type"
                    else "Unknown"
                )
        return parsed

    except json.JSONDecodeError:
        return {
            "accused": "Unknown",
            "victim": "Unknown",
            "location": "India",
            "incident": raw_input[:500],
            "ai_suggested_case_type": "General Legal Dispute",
            "suggestion_reason": "Could not parse input clearly",
            "confidence": "LOW",
            "missing_info": ["Could not parse — all fields uncertain"],
        }
    except Exception as e:
        return {
            "accused": "Unknown",
            "victim": "Unknown",
            "location": "India",
            "incident": raw_input[:500],
            "ai_suggested_case_type": "General Legal Dispute",
            "suggestion_reason": f"Error: {str(e)}",
            "confidence": "LOW",
            "missing_info": [f"Error: {str(e)}"],
        }


def build_case_string(case_type: str, details: Dict) -> str:
    """Build final case string for agents after user confirms case type."""
    return f"""
Case Type: {case_type}
Accused: {details.get('accused', 'Unknown')}
Complainant/Victim: {details.get('victim', 'Unknown')}
Location: {details.get('location', 'India')}

Facts of the Case:
{details.get('incident', '')}
""".strip()


def extract_text_from_upload(uploaded_file) -> str:
    """Extract plain text from PDF, DOCX, or TXT upload."""
    import io

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    try:
        if file_name.endswith(".pdf"):
            import fitz

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text[:5000]

        if file_name.endswith(".docx"):
            from docx import Document as DocxDoc

            doc = DocxDoc(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text[:5000]

        if file_name.endswith(".txt"):
            return file_bytes.decode("utf-8", errors="ignore")[:5000]

        return f"Unsupported file type: {file_name}"

    except Exception as e:
        return f"Error reading file: {str(e)}"

