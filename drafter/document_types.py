# drafter/document_types.py
# All document type definitions, templates, required fields, IPC sections

DOCUMENT_TYPES = {
    "FIR": {
        "full_name": "First Information Report",
        "icon": "🚨",
        "authority": "Police Station",
        "act": "Section 154 CrPC — Police must register FIR",
        "description": "Official complaint to police for cognizable offences",
        "color": "#e74c3c",
        "use_cases": [
            "Theft / Robbery / Burglary",
            "Assault / Physical attack",
            "Fraud / Cheating (Section 420 IPC)",
            "Kidnapping / Missing person",
            "Cybercrime / Online fraud",
            "Domestic violence",
            "Murder / Culpable homicide attempt",
        ],
        "required_fields": [
            "complainant_name",
            "complainant_address",
            "complainant_phone",
            "accused_name",
            "accused_address",
            "incident_date",
            "incident_time",
            "incident_location",
            "incident_description",
            "witnesses",
            "evidence",
            "police_station",
            "city",
            "state",
        ],
        "ipc_sections": {
            "Theft": "IPC Section 378-379",
            "Robbery": "IPC Section 390-392",
            "Assault": "IPC Section 351-354",
            "Grievous Hurt": "IPC Section 320-325",
            "Fraud/Cheating": "IPC Section 415-420",
            "Criminal Breach": "IPC Section 405-406",
            "Domestic Violence": "IPC Section 498A + DV Act 2005",
            "Cybercrime": "IT Act Section 66, 66C, 66D",
            "Murder Attempt": "IPC Section 307",
            "Kidnapping": "IPC Section 359-363",
        },
    },
    "Legal Notice": {
        "full_name": "Legal Notice",
        "icon": "⚖️",
        "authority": "Opposite Party (via Registered Post)",
        "act": "Section 80 CPC — Mandatory notice before suit",
        "description": "Formal demand notice before filing civil/criminal case",
        "color": "#2980b9",
        "use_cases": [
            "Landlord refusing to return security deposit",
            "Employer non-payment of salary/dues",
            "Builder not delivering flat",
            "Breach of contract",
            "Defamation / libel",
            "Recovery of money",
            "Property disputes",
        ],
        "required_fields": [
            "sender_name",
            "sender_address",
            "sender_phone",
            "sender_email",
            "recipient_name",
            "recipient_address",
            "recipient_designation",
            "grievance_description",
            "demand",
            "amount_if_any",
            "deadline_days",
            "city",
            "date",
        ],
        "ipc_sections": {
            "Contract Breach": "Indian Contract Act Section 73-74",
            "Non-payment": "Contract Act Section 73 + NI Act Section 138",
            "Property Dispute": "Transfer of Property Act + Specific Relief Act",
            "Builder Delay": "RERA 2016 Section 18 + Consumer Protection Act",
            "Defamation": "IPC Section 499-500",
            "Employment Dues": "Payment of Wages Act + Contract Act",
        },
    },
    "RTI Application": {
        "full_name": "Right to Information Application",
        "icon": "📋",
        "authority": "Public Information Officer (PIO)",
        "act": "RTI Act 2005 Section 6 — Right to seek information",
        "description": "Formal application to government for information",
        "color": "#27ae60",
        "use_cases": [
            "Government job selection process",
            "File status / pending application",
            "Government spending / contracts",
            "Policy documents / circulars",
            "Property records",
            "Court case status",
            "Scheme beneficiary list",
        ],
        "required_fields": [
            "applicant_name",
            "applicant_address",
            "applicant_phone",
            "applicant_email",
            "department_name",
            "department_address",
            "pio_name_if_known",
            "information_sought",
            "reason_if_any",
            "city",
            "date",
        ],
        "ipc_sections": {
            "Primary Act": "RTI Act 2005 Section 6(1)",
            "Response Time": "RTI Act Section 7 — 30 days response mandatory",
            "Appeal": "RTI Act Section 19 — First Appellate Authority",
            "Fee": "RTI Act Section 6(1) — ₹10 application fee",
            "Exemptions": "RTI Act Section 8 — info that cannot be disclosed",
        },
    },
    "Consumer Complaint": {
        "full_name": "Consumer Complaint",
        "icon": "🛒",
        "authority": "District Consumer Disputes Redressal Commission",
        "act": "Consumer Protection Act 2019 Section 35",
        "description": "Complaint against defective goods or deficient services",
        "color": "#f39c12",
        "use_cases": [
            "Defective product delivered",
            "E-commerce fake/wrong product",
            "Insurance claim rejection",
            "Bank unauthorized charges",
            "Medical negligence",
            "Builder possession delay",
            "Electricity/telecom overcharging",
        ],
        "required_fields": [
            "complainant_name",
            "complainant_address",
            "complainant_phone",
            "complainant_email",
            "opposite_party_name",
            "opposite_party_address",
            "opposite_party_type",
            "transaction_date",
            "transaction_amount",
            "product_service",
            "defect_description",
            "communication_attempts",
            "relief_sought",
            "documents_attached",
            "city",
            "state",
            "date",
        ],
        "ipc_sections": {
            "Defect": "Consumer Protection Act 2019 Section 2(10)",
            "Deficiency": "Consumer Protection Act 2019 Section 2(11)",
            "Filing Complaint": "Consumer Protection Act 2019 Section 35",
            "Jurisdiction": "Consumer Protection Act 2019 Section 34",
            "Compensation": "Consumer Protection Act 2019 Section 39(1)(d)",
            "E-commerce": "Consumer Protection (E-Commerce) Rules 2020",
        },
    },
    "Bail Application": {
        "full_name": "Bail Application",
        "icon": "🔓",
        "authority": "Sessions Court / High Court",
        "act": "CrPC Section 437/438/439 — Bail provisions",
        "description": "Petition for bail in criminal matter",
        "color": "#8e44ad",
        "use_cases": [
            "Regular bail after arrest",
            "Anticipatory bail before arrest",
            "Bail in non-bailable offence",
            "Bail pending trial",
            "Bail modification / enhancement",
        ],
        "required_fields": [
            "applicant_name",
            "applicant_age",
            "applicant_address",
            "applicant_occupation",
            "fir_number",
            "fir_date",
            "police_station",
            "sections_charged",
            "arrest_date",
            "custody_duration",
            "bail_grounds",
            "surety_name",
            "surety_address",
            "surety_relationship",
            "case_facts",
            "court_name",
            "city",
            "state",
            "date",
        ],
        "ipc_sections": {
            "Regular Bail": "CrPC Section 437",
            "Anticipatory Bail": "CrPC Section 438",
            "High Court Bail": "CrPC Section 439",
            "Bail Conditions": "CrPC Section 437(3)",
            "Bail Bond": "CrPC Section 441",
        },
    },
}

# Fields that are always present (pre-filled or standard)
COMMON_FIELDS = {
    "date": "Auto-filled with today's date",
    "city": "Required from user",
    "state": "Required from user",
}

# Document type auto-detection keywords
DETECTION_KEYWORDS = {
    "FIR": [
        "fir",
        "police",
        "theft",
        "stolen",
        "attack",
        "assault",
        "fraud",
        "cheating",
        "420",
        "robbery",
        "kidnap",
        "murder",
        "crime",
        "criminal",
        "complaint police",
        "file case",
        "arrested",
        "cybercrime",
        "hack",
        "domestic violence",
        "missing",
    ],
    "Legal Notice": [
        "notice",
        "demand",
        "deposit",
        "salary",
        "dues",
        "builder",
        "flat",
        "contract",
        "breach",
        "recovery",
        "money",
        "defamation",
        "landlord",
        "employer",
        "send notice",
        "legal notice",
        "property",
    ],
    "RTI Application": [
        "rti",
        "right to information",
        "government",
        "file status",
        "pending",
        "public information",
        "department",
        "official",
        "spending",
        "records",
        "circular",
        "policy",
        "scheme",
    ],
    "Consumer Complaint": [
        "consumer",
        "product",
        "defective",
        "fake",
        "amazon",
        "flipkart",
        "refund",
        "insurance",
        "bank",
        "overcharge",
        "electricity",
        "telecom",
        "medical negligence",
        "hospital",
        "ecommerce",
    ],
    "Bail Application": [
        "bail",
        "arrested",
        "custody",
        "jail",
        "anticipatory",
        "sessions",
        "high court bail",
        "fir registered",
        "charged",
        "detained",
    ],
}


def detect_document_type(user_description: str) -> tuple[str, int]:
    """
    Returns (detected_type, confidence_score) based on keyword matching.
    confidence_score: 0-100
    """
    description_lower = user_description.lower()
    scores: dict[str, int] = {}

    for doc_type, keywords in DETECTION_KEYWORDS.items():
        score = sum(
            2
            if f" {kw} " in f" {description_lower} "
            else 1
            if kw in description_lower
            else 0
            for kw in keywords
        )
        scores[doc_type] = score

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    total = sum(scores.values())

    confidence = int((best_score / max(total, 1)) * 100)
    confidence = min(confidence, 95)  # never claim 100%

    return best_type, confidence

