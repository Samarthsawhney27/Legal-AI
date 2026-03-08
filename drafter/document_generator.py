# drafter/document_generator.py
# Generates strictly formal Indian legal documents
# Zero emoji, zero casual language, court-grade formatting

import json
import re
from datetime import datetime

import ollama

from drafter.document_types import DOCUMENT_TYPES

OLLAMA_MODEL = "llama3.2"

TODAY = datetime.today().strftime("%d %B %Y")

# ─────────────────────────────────────────────────────────────────────────
# STRICT FORMALITY INSTRUCTION — prepended to ALL document prompts
# ─────────────────────────────────────────────────────────────────────────
STRICT_FORMALITY_INSTRUCTION = """
ABSOLUTE FORMATTING RULES — VIOLATION OF ANY RULE IS UNACCEPTABLE:

1. ZERO EMOJI anywhere in the document. Not a single one.
2. ZERO bullet points. ZERO dashes as list markers.
3. ALL facts in numbered paragraphs only: 1., 2., 3. etc.
4. ZERO casual phrases. Use only formal legal English.
5. ZERO markdown formatting — no asterisks, no hashes, no underscores.
6. ALL section headings in BLOCK CAPITALS only.
7. Monetary amounts: "Rs.X,XX,XXX/- (Rupees X Lakhs X Thousand Only)"
8. Dates: "the Xth day of Month, Year" or DD.MM.YYYY format.
9. Refer to parties as: Complainant/Informant, Accused/Noticee/Opposite
   Party, Applicant — NEVER by first name alone after introduction.
10. Document must read exactly like a real Indian court submission.
11. NO filler phrases like "I want to", "Please note", "Kindly be aware".
    Use: "It is submitted that", "It is pertinent to state that",
    "The Complainant states as under:", "It is most respectfully submitted"
12. Every document must end with a formal VERIFICATION/DECLARATION clause.
13. Language must be precise, concise, and unambiguous.
    Every sentence must serve a legal purpose.
14. No repetition. State each fact exactly once.
15. Total document length: 600-900 words. Concise but complete.
"""


# ─────────────────────────────────────────────────────────────────────────
# FIR PROMPT
# ─────────────────────────────────────────────────────────────────────────
FIR_GENERATION_PROMPT = """
{formality_rules}

You are a senior Indian Police legal officer drafting an official
First Information Report (FIR) under Section 154 of the Code of
Criminal Procedure, 1973.

Draft a complete, strictly formatted FIR using the fields below.
The document must be identical in structure to an actual FIR filed
at an Indian police station.

EXTRACTED FIELDS:
{fields_json}

APPLICABLE SECTIONS: {applicable_sections}

OUTPUT THE DOCUMENT IN EXACTLY THIS FORMAT:
(Replace bracketed instructions with actual content from fields)

FIRST INFORMATION REPORT
(Under Section 154 of the Code of Criminal Procedure, 1973)

FIR No.        : __________ / {year}
Date of FIR    : {date}
Time of FIR    : __________ Hours
Police Station : {police_station}
District       : {city}
State          : {state}
Act(s)         : {applicable_sections}

------------------------------------------------------------------------

PART I — DETAILS OF THE INFORMANT / COMPLAINANT

Name              : {complainant_name}
Father's Name     : {complainant_father_name}
Age               : {complainant_age} Years
Permanent Address : {complainant_address}
Contact Number    : {complainant_phone}
Occupation        : [extract from fields or write Not Stated]

------------------------------------------------------------------------

PART II — DETAILS OF ACCUSED / SUSPECT

Name              : {accused_name}
Address           : {accused_address}
Physical Description : {accused_description}
Relationship to Informant : [extract or write Not Known]

------------------------------------------------------------------------

PART III — NATURE OF OFFENCE

[List each applicable IPC / Act section on a separate line as:]
Section [X] of [Act] — [Brief description of offence]
Section [X] of [Act] — [Brief description of offence]

------------------------------------------------------------------------

PART IV — DATE, TIME AND PLACE OF OCCURRENCE

Date of Occurrence  : {incident_date}
Time of Occurrence  : {incident_time}
Place of Occurrence : {incident_location}

------------------------------------------------------------------------

PART V — STATEMENT OF THE INFORMANT

The Informant states as under:

1. [State the background — who the parties are, their relationship,
   and the context leading up to the offence. Formal third person
   or first person is acceptable. Be specific and factual.]

2. [State exactly what happened — actions of the accused, sequence
   of events, date and time, location, method used. Be precise.
   Include specific amounts, descriptions, identifications.]

3. [State the immediate consequence — injury, loss, damage, harm
   suffered by the Informant as a direct result of the accused's
   actions. Include medical treatment if applicable.]

4. [State the evidence available — documents, photographs, videos,
   witness names, CCTV, medical reports, bank statements etc.]

5. [State any prior communication or complaint made before this FIR —
   whether police was approached earlier, bank informed, etc.]

------------------------------------------------------------------------

PART VI — WITNESSES

[List witness names and addresses, one per line, numbered.
If none: Write "No witnesses have been identified at this stage."]

------------------------------------------------------------------------

PART VII — PROPERTY INVOLVED

[Describe any property stolen, damaged, or involved.
Include: description, estimated value in Rs.X,XX,XXX/- format.
If none: Write "No property involved."]

------------------------------------------------------------------------

PART VIII — ACTION REQUESTED

The Informant respectfully requests that the following action be taken:

1. That an FIR be registered against the accused under the
   applicable sections stated above.

2. That the accused be apprehended and appropriate legal action
   be initiated forthwith.

3. That the evidence be preserved and an investigation be conducted
   as per law.

4. That such other and further orders be passed as this Hon'ble
   Station may deem fit and proper in the circumstances of the case.

------------------------------------------------------------------------

DECLARATION

I, {complainant_name}, do hereby solemnly declare that the
information given above is true and correct to the best of my
knowledge and belief. Nothing material has been concealed
therefrom. I am aware that giving false information to police
is a punishable offence under Section 182 of the Indian Penal
Code, 1860.

Signature / Left Thumb Impression of Informant : ____________________
Name (in full)    : {complainant_name}
Date              : {date}
Place             : {city}, {state}

------------------------------------------------------------------------

FOR OFFICE USE ONLY

Received by       : _________________________________ (Designation)
GD Entry No.      : ______________
FIR Registered at : __________ Hours on ______________
Investigating Officer Assigned : _________________________
Designation       : _________________________

------------------------------------------------------------------------
"""


# ─────────────────────────────────────────────────────────────────────────
# LEGAL NOTICE PROMPT
# ─────────────────────────────────────────────────────────────────────────
LEGAL_NOTICE_GENERATION_PROMPT = """
{formality_rules}

You are a senior Indian advocate drafting a formal Legal Notice
on behalf of your client. This notice is to be sent via
Registered Post Acknowledgement Due (RPAD) and Speed Post.

Draft a complete, strictly formatted Legal Notice using the
fields below. The document must conform to standard Indian
legal notice format as used by practising advocates.

EXTRACTED FIELDS:
{fields_json}

APPLICABLE SECTIONS: {applicable_sections}

OUTPUT THE DOCUMENT IN EXACTLY THIS FORMAT:

WITHOUT PREJUDICE

LEGAL NOTICE

Notice No. : LN / {year} / 001
Date       : {date}
Mode       : Registered Post A.D. + Speed Post

FROM
{sender_name}
{sender_address}
Contact : {sender_phone}
Email   : {sender_email}

TO
{recipient_name}
{recipient_designation}
{recipient_address}

------------------------------------------------------------------------

Subject : Legal Notice under [primary applicable Act and Section]
          for [brief subject — e.g., "Refund of Security Deposit"
          or "Payment of Outstanding Dues" or "Breach of Contract"]

------------------------------------------------------------------------

Sir / Madam,

Under instructions from and on behalf of my client /
myself, {sender_name}, I hereby serve upon you the
following Legal Notice:

1. THAT [Introduce the parties — who the sender is, who the
   recipient is, and the nature of the legal relationship
   between them. e.g., landlord-tenant, employer-employee,
   contractor-client. Be specific about dates and facts.]

2. THAT [State the core grievance — what the Noticee did
   or failed to do. Specific dates, specific actions,
   specific violations. Reference the agreement, contract,
   or legal obligation that was breached. State amounts
   in full formal format: Rs.X,XX,XXX/- (Rupees X Only).]

3. THAT [State the legal violation — which specific sections
   of which Acts have been violated by the Noticee's conduct.
   Cite: {applicable_sections}. Explain briefly how each
   section applies to the facts.]

4. THAT [State any prior attempts at resolution — written
   communications sent, meetings held, requests made,
   and the Noticee's response or lack thereof. This
   establishes that the sender has exhausted informal
   remedies before issuing this notice.]

5. THAT the Noticee is hereby called upon to:
   [State the specific demand clearly and precisely.
   Include exact amount in Rs.X,XX,XXX/- format if
   monetary demand. State the exact deadline:
   "within {deadline_days} days from the date of
   receipt of this notice."]

6. THAT in the event of failure on the part of the Noticee
   to comply with the above demands within the stipulated
   period, the Sender shall be left with no option but to
   initiate appropriate legal proceedings before the
   competent court or forum, both civil and criminal,
   as may be advised, entirely at the risk, cost, and
   consequences of the Noticee, without any further
   notice in this regard.

This notice is issued without prejudice to all other rights
and remedies available to the Sender in law and equity,
all of which are expressly reserved.

A copy of this notice is being retained for record purposes.

Yours faithfully,

____________________________
{sender_name}
Date  : {date}
Place : {city}, {state}

------------------------------------------------------------------------

ENCLOSURES (as applicable):
1. Copy of [relevant agreement / contract / receipt]
2. Copy of [supporting documentary evidence]
3. Proof of postal dispatch (to be attached upon posting)

------------------------------------------------------------------------
"""


# ─────────────────────────────────────────────────────────────────────────
# RTI APPLICATION PROMPT
# ─────────────────────────────────────────────────────────────────────────
RTI_GENERATION_PROMPT = """
{formality_rules}

You are an expert in the Right to Information Act, 2005,
drafting a formal RTI Application on behalf of a citizen.

Draft a complete, strictly formatted RTI Application using
the fields below. The document must conform exactly to
the format prescribed under Section 6(1) of the RTI Act, 2005,
as used before all Indian public authorities.

EXTRACTED FIELDS:
{fields_json}

APPLICABLE SECTIONS: {applicable_sections}

OUTPUT THE DOCUMENT IN EXACTLY THIS FORMAT:

APPLICATION UNDER THE RIGHT TO INFORMATION ACT, 2005
(Section 6(1) — Right to Seek Information from Public Authorities)

Application No. : [To be assigned by receiving office]
Date            : {date}

TO

The Public Information Officer (PIO)
{department_name}
{department_address}

------------------------------------------------------------------------

Subject : Application for Information under Section 6(1) of the
          Right to Information Act, 2005

------------------------------------------------------------------------

Sir / Madam,

I, {applicant_name}, son / daughter of ________________,
aged _______ years, residing at {applicant_address},
Contact : {applicant_phone}, Email : {applicant_email},
a citizen of India, do hereby request the following
information under the provisions of the Right to
Information Act, 2005:

------------------------------------------------------------------------

PART I — INFORMATION SOUGHT

[Write each piece of information as a separate numbered
point. Each question must be specific, precise, and
answerable. Vague questions will be rejected by the PIO.
Time period: {time_period_for_info}]

1. [First specific piece of information sought — state
   precisely what document, record, data, or fact is
   requested. Include file numbers, dates, reference
   numbers if known.]

2. [Second specific piece of information sought.]

3. [Third specific piece of information sought.]

4. [Additional points as needed — maximum 6-8 points.
   More points reduce chance of full compliance.]

5. Certified copies of the following documents:
   a. [Document 1 — specific name and date]
   b. [Document 2 — specific name and date]

------------------------------------------------------------------------

PART II — PERIOD FOR WHICH INFORMATION IS SOUGHT

{time_period_for_info}

------------------------------------------------------------------------

PART III — FORMAT IN WHICH INFORMATION IS DESIRED

{format_desired}

If the information is available in electronic form, the
Applicant requests that the same be provided in soft copy
via email at {applicant_email} in addition to physical copy.

------------------------------------------------------------------------

PART IV — FEE PAYMENT DETAILS

Application Fee of Rs.10/- (Rupees Ten Only) is enclosed
herewith in the form of : [Cash / Indian Postal Order /
Demand Draft / Court Fee Stamp / Online Payment Reference]

Note : Citizens below the Poverty Line (BPL) are exempted
from payment of fee under Section 6(1) of the RTI Act, 2005.
BPL Certificate No. ___________ (if applicable).

------------------------------------------------------------------------

PART V — STATUTORY REMINDERS TO THE PIO

1. The Public Information Officer is reminded that under
   Section 7(1) of the RTI Act, 2005, the requested
   information is to be provided within 30 (thirty) days
   from the date of receipt of this application.

2. In case the requested information concerns the life
   or liberty of a person, the same is required to be
   provided within 48 hours under Section 7(1) proviso.

3. Failure to provide information within the prescribed
   period shall be deemed a refusal under Section 7(2)
   and the Applicant shall be entitled to file a First
   Appeal under Section 19(1) of the RTI Act, 2005.

4. The PIO is further reminded that under Section 20 of
   the RTI Act, 2005, the Information Commission may
   impose a penalty of Rs.250/- per day up to a maximum
   of Rs.25,000/- for delay or denial without reasonable
   cause.

------------------------------------------------------------------------

DECLARATION

I, {applicant_name}, do hereby solemnly declare that I am
a citizen of India and that the information sought above
is not covered under any of the exemptions specified in
Section 8 of the Right to Information Act, 2005, to the
best of my knowledge and belief.

Signature of Applicant : ____________________________
Name (in full)         : {applicant_name}
Address                : {applicant_address}
Date                   : {date}
Place                  : {city}, {state}

------------------------------------------------------------------------

ENCLOSURES:
1. Proof of fee payment
2. [Identity proof of applicant, if required]
3. BPL certificate (if claiming fee exemption)

------------------------------------------------------------------------
"""


# ─────────────────────────────────────────────────────────────────────────
# CONSUMER COMPLAINT AND BAIL APPLICATION — existing prompts with
# formality rules prepended
# ─────────────────────────────────────────────────────────────────────────
CONSUMER_COMPLAINT_PROMPT = """
{formality_rules}

You are an expert consumer law advocate drafting a Consumer Complaint.
Draft a complete Consumer Complaint for the District Consumer
Disputes Redressal Commission.

EXTRACTED FIELDS:
{fields_json}

DOCUMENT REQUIREMENTS:
1. Header: Complaint No.: ___/[Year] (to be filled by registry)
2. "BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION, [CITY]"
3. Parties: Complainant vs Opposite Party (formatted like court pleading)
4. Body sections:
   a. FACTS OF THE CASE (numbered paragraphs — what happened, when, how)
   b. CAUSE OF ACTION (what legal right was violated)
   c. DEFICIENCY IN SERVICE / DEFECT IN GOODS (cite specific section)
   d. RELIEF SOUGHT (specific demands — refund, compensation, costs)
5. Cite: {applicable_sections}
6. Include: Consumer Protection Act 2019 Section 35 reference
7. List all documentary evidence as annexures
8. Prayer clause: "It is therefore most respectfully prayed..."
9. Verification clause at end
10. Affidavit note

Draft the complete Consumer Complaint now:
"""

BAIL_APPLICATION_PROMPT = """
{formality_rules}

You are a senior criminal advocate drafting a Bail Application.
Draft a complete Bail Application for the Sessions/High Court.

EXTRACTED FIELDS:
{fields_json}

DOCUMENT REQUIREMENTS:
1. Header: "IN THE COURT OF [COURT NAME]"
2. Case reference: Criminal Misc. Petition No. ___/[Year]
3. Parties: "IN THE MATTER OF: [Applicant] ...APPLICANT"
           "VERSUS: State of [State] ...RESPONDENT"
4. "APPLICATION UNDER SECTION [437/438/439] CrPC FOR GRANT OF BAIL"
5. Body sections:
   a. BRIEF FACTS OF THE CASE
   b. GROUNDS FOR BAIL (minimum 6 strong legal grounds):
      1. No criminal antecedents
      2. Deep roots in society
      3. Offence is bailable / compoundable
      4. Custodial interrogation complete
      5. Investigation complete / charge sheet filed
      6. Will not tamper evidence / flee justice
   c. LEGAL SUBMISSIONS (cite bail jurisprudence)
   d. PRAYER: "It is therefore most respectfully prayed..."
6. Cite: {applicable_sections} + landmark bail judgments
   (Arnesh Kumar v State of Bihar, Sanjay Chandra v CBI)
7. End: Advocate signature, date, place
8. Verification by applicant

Draft the complete Bail Application now:
"""


# ─────────────────────────────────────────────────────────────────────────
# PROMPT MAP
# ─────────────────────────────────────────────────────────────────────────
PROMPT_MAP = {
    "FIR":                FIR_GENERATION_PROMPT,
    "Legal Notice":       LEGAL_NOTICE_GENERATION_PROMPT,
    "RTI Application":    RTI_GENERATION_PROMPT,
    "Consumer Complaint": CONSUMER_COMPLAINT_PROMPT,
    "Bail Application":   BAIL_APPLICATION_PROMPT,
}


# ─────────────────────────────────────────────────────────────────────────
# MAIN GENERATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────
def generate_document_text(document_type: str, extracted_fields: dict) -> str:
    """
    Generates a strictly formal legal document.
    Returns plain text — no emoji, no markdown, no casual language.
    """
    template = PROMPT_MAP[document_type]

    applicable = extracted_fields.get('applicable_sections', [])
    applicable_str = (
        ", ".join(applicable)
        if isinstance(applicable, list)
        else str(applicable)
    )

    # Fill placeholders directly
    prompt = template.format(
        formality_rules     = STRICT_FORMALITY_INSTRUCTION,
        fields_json         = json.dumps(extracted_fields, indent=2),
        applicable_sections = applicable_str,
        date                = extracted_fields.get('_generated_date', TODAY),
        year                = TODAY.split()[-1],
        deadline_days       = extracted_fields.get('deadline_days', '15'),
        # FIR fields
        police_station      = extracted_fields.get('police_station_name', '________'),
        city                = extracted_fields.get('city', '________'),
        state               = extracted_fields.get('state', '________'),
        complainant_name    = extracted_fields.get('complainant_name', '________'),
        complainant_father_name = extracted_fields.get('complainant_father_name', '________'),
        complainant_age     = extracted_fields.get('complainant_age', '________'),
        complainant_address = extracted_fields.get('complainant_address', '________'),
        complainant_phone   = extracted_fields.get('complainant_phone', '________'),
        accused_name        = extracted_fields.get('accused_name', '________'),
        accused_address     = extracted_fields.get('accused_address', '________'),
        accused_description = extracted_fields.get('accused_description', '________'),
        incident_date       = extracted_fields.get('incident_date', '________'),
        incident_time       = extracted_fields.get('incident_time', '________'),
        incident_location   = extracted_fields.get('incident_location', '________'),
        # Legal Notice fields
        sender_name         = extracted_fields.get('sender_name', '________'),
        sender_address      = extracted_fields.get('sender_address', '________'),
        sender_phone        = extracted_fields.get('sender_phone', '________'),
        sender_email        = extracted_fields.get('sender_email', '________'),
        recipient_name      = extracted_fields.get('recipient_name', '________'),
        recipient_designation = extracted_fields.get('recipient_designation', '________'),
        recipient_address   = extracted_fields.get('recipient_address', '________'),
        # RTI fields
        applicant_name      = extracted_fields.get('applicant_name', '________'),
        applicant_address   = extracted_fields.get('applicant_address', '________'),
        applicant_phone     = extracted_fields.get('applicant_phone', '________'),
        applicant_email     = extracted_fields.get('applicant_email', '________'),
        department_name     = extracted_fields.get('department_name', '________'),
        department_address  = extracted_fields.get('department_address', '________'),
        time_period_for_info = extracted_fields.get('time_period_for_info', 'As applicable'),
        format_desired      = extracted_fields.get('format_desired', 'Printed copies and soft copy via email'),
    )

    # Final instruction appended to prompt
    final_prompt = prompt + """

FINAL INSTRUCTION:
Using ALL the extracted fields above, complete this document now.
Replace every [bracketed instruction] with actual formal content
generated from the fields provided.
Replace every ________ with the appropriate value from fields.
Where a field says "NOT PROVIDED", write ________________
  (blank line for manual completion).
Output ONLY the completed document.
No preamble, no explanation, no commentary before or after.
The very first word of your output must be the first word
of the document itself.
Strictly follow ALL 15 formatting rules stated at the top.
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": final_prompt}],
        stream=False
    )

    raw = response['message']['content'].strip()

    # Post-processing: strip any accidental markdown and emoji
    raw = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', raw)      # remove bold/italic
    raw = re.sub(r'#{1,6}\s', '', raw)                        # remove markdown headers
    raw = re.sub(r'^\s*[-\u2022]\s', '', raw, flags=re.MULTILINE)  # remove bullets
    # Remove any emoji characters
    raw = re.sub(
        u'[\U00010000-\U0010ffff]'
        u'|[\u2600-\u26FF]'
        u'|[\u2700-\u27BF]'
        u'|[\U0001F300-\U0001F9FF]',
        '', raw
    )

    return raw.strip()


def generate_whatsapp_version(document_text: str, document_type: str) -> str:
    """
    Creates a concise WhatsApp-ready version of the document.
    Plain text, no formatting symbols, copy-paste ready.
    """
    prompt = f"""
Summarize this {document_type} into a WhatsApp message format.
Keep it under 500 words.
Include: key facts, what is being demanded, deadline, and contact info.
Use plain text only — no markdown, no asterisks for bold, no tables.
Start with: "LEGAL NOTICE / FIR / COMPLAINT (as applicable)"

DOCUMENT:
{document_text[:3000]}

WhatsApp version:
"""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    return response["message"]["content"].strip()
