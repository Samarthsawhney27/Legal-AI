# courtroom/case_templates.py
# Pre-built cases optimized for Constitution + Contract + IPC + Consumer Protection books

PRESET_CASES = {
    "Landlord Eviction Without Notice": {
        "type": "Contract Breach + Fundamental Rights",
        "accused": "Mr. Ramesh Gupta (Landlord)",
        "victim": "Mr. Anil Kumar (Tenant)",
        "location": "Mumbai, Maharashtra",
        "incident": (
            "Tenant Anil Kumar has been residing in the rented flat at Andheri West for "
            "3 years, paying rent of Rs. 25,000/month consistently. A valid registered lease "
            "agreement existed between both parties valid until December 2024. In October "
            "2024, without any prior written notice, the landlord Ramesh Gupta physically "
            "changed the locks of the flat while the tenant was at work, leaving all his "
            "belongings inside. No court order was obtained. Landlord claims the verbal "
            "agreement had ended. Tenant demands re-entry and Rs. 2,00,000 in damages."
        ),
    },
    "Wrongful Termination of Employment Contract": {
        "type": "Contract Breach + Article 19",
        "accused": "TechCorp Pvt. Ltd. (Employer)",
        "victim": "Ms. Priya Sharma (Employee)",
        "location": "Bangalore, Karnataka",
        "incident": (
            "Ms. Priya Sharma was employed as Senior Software Engineer at TechCorp Pvt. Ltd. "
            "under a 2-year fixed-term contract signed in January 2023, with a 3-month notice "
            "period clause for termination by either party. In August 2024, with no prior "
            "notice and no written reason provided, TechCorp terminated her employment via "
            "a single email effective the same day, citing vague 'restructuring'. No "
            "severance was paid. No notice period was honored. Ms. Sharma claims breach of "
            "contract and violation of her right to livelihood under Article 21."
        ),
    },
    "Builder Delays Flat Possession": {
        "type": "Specific Relief + Contract Breach",
        "accused": "Sunshine Developers Pvt. Ltd. (Builder)",
        "victim": "Mr. Suresh & Mrs. Meena Patel (Buyers)",
        "location": "Pune, Maharashtra",
        "incident": (
            "Mr. and Mrs. Patel entered into a registered Sale Agreement with Sunshine "
            "Developers in 2021 for a 2BHK flat, paying Rs. 45 lakhs (full amount) with "
            "possession promised by December 2023. As of 2025, construction is incomplete "
            "and possession has not been given. Builder claims force majeure due to COVID "
            "delays. Buyers argue COVID exemption expired in 2022 and 2 more years of delay "
            "is unjustifiable. Buyers seek specific performance of the contract (actual flat "
            "handover) plus compensation of Rs. 5 lakhs for rent paid elsewhere during the delay."
        ),
    },
    "Government Cancels Valid Contract Arbitrarily": {
        "type": "Article 14 + Contract Breach",
        "accused": "State Government of Rajasthan",
        "victim": "M/s. ABC Infrastructure Ltd. (Contractor)",
        "location": "Jaipur, Rajasthan",
        "incident": (
            "M/s. ABC Infrastructure Ltd. won a government tender for road construction worth "
            "Rs. 12 crores through a fair bidding process in 2022. A formal contract was signed "
            "and work commenced. After 40% of work was completed and Rs. 4.8 crores spent, the "
            "State Government cancelled the contract in 2024 without any written reason, "
            "without any show-cause notice, and without paying for completed work. A new "
            "contractor (politically connected) was appointed for the same work. ABC "
            "Infrastructure claims arbitrary cancellation violates Article 14 (equality "
            "before law) and amounts to breach of contract."
        ),
    },
    "Contract Signed Under Coercion": {
        "type": "Section 15 Contract Act + Article 21",
        "accused": "Mr. Vijay Malhotra (Moneylender)",
        "victim": "Mr. Deepak Yadav (Borrower)",
        "location": "Lucknow, Uttar Pradesh",
        "incident": (
            "Deepak Yadav borrowed Rs. 5 lakhs from Vijay Malhotra in 2022 during a family "
            "medical emergency. Under severe pressure, with Malhotra threatening to harm "
            "his family if he refused, Deepak signed a document that transferred ownership "
            "of his ancestral home worth Rs. 40 lakhs as security. The document was signed "
            "without legal counsel and without Deepak reading it. When Deepak repaid Rs. 3 "
            "lakhs and sought return of his property, Malhotra claimed full ownership via "
            "the signed document. Deepak claims the agreement is void due to coercion "
            "under Section 15 of the Indian Contract Act."
        ),
    },
    "🛒 E-commerce Fraud (Consumer)": {
        "type": "E-commerce Fraud / Online Shopping",
        "accused": "ShopFast India Pvt. Ltd. (E-commerce Platform)",
        "victim": "Ms. Kavya Reddy (Consumer)",
        "location": "Hyderabad, Telangana",
        "incident": (
            "Ms. Kavya Reddy ordered a branded laptop worth ₹65,000 from ShopFast India "
            "during a sale. The product delivered was a fake/counterfeit item with no "
            "warranty card, different serial number, and significantly inferior specs. "
            "She raised a return request within 24 hours but ShopFast rejected it citing "
            "'electronics return policy'. She has emails and photos as evidence. The seller "
            "account has since been removed from the platform but ShopFast refuses liability "
            "claiming they are only a marketplace. She seeks full refund plus ₹10,000 "
            "compensation for harassment under Consumer Protection Act 2019."
        ),
    },
    "⚔️ Assault and Grievous Hurt (IPC)": {
        "type": "Assault / Hurt",
        "accused": "Mr. Rohit Verma",
        "victim": "Mr. Sanjay Mishra",
        "location": "Delhi",
        "incident": (
            "On the night of 15th March 2024, Mr. Rohit Verma attacked Mr. Sanjay Mishra "
            "with an iron rod during a property boundary dispute in their neighbourhood "
            "in Dwarka, Delhi. Sanjay suffered a fractured arm and head injuries requiring "
            "14 days hospitalisation. Three witnesses were present. Medical report confirms "
            "grievous hurt. Rohit claims it was self-defence as Sanjay had verbally "
            "threatened him first. FIR has been filed under IPC. Prosecution seeks "
            "conviction; defense argues right of private defence under IPC."
        ),
    },
}

SUPPORTED_CASE_TYPES = [
    # ── Contract / Civil (existing) ───────────────────────
    "Contract Breach",
    "Landlord-Tenant Dispute",
    "Employment Contract Dispute",
    "Property Sale Agreement Dispute",
    "Specific Performance of Contract",
    "Coercion / Misrepresentation in Contract",

    # ── Constitutional (existing) ─────────────────────────
    "Fundamental Rights Violation (Government Action)",
    "Arbitrary State Action (Article 14)",

    # ── Criminal / IPC (NEW) ──────────────────────────────
    "Criminal / IPC",
    "Assault / Hurt",
    "Theft / Robbery",
    "Cheating / Fraud (Criminal)",
    "Murder / Culpable Homicide",

    # ── Consumer (NEW) ────────────────────────────────────
    "Consumer Rights / Defective Product",
    "E-commerce Fraud / Online Shopping",
    "Service Deficiency",
    "Misleading Advertisement",
    "Medical Negligence (Consumer)",
]

UNSUPPORTED_CASE_TYPES = [
    "Divorce / Family Law (need Hindu Marriage Act)",
    "GST / Tax Disputes (need Finance Acts)",
    "POCSO / Child Protection (need POCSO Act)",
    "Motor Accident Claims (need Motor Vehicles Act)",
    "Cheque Bounce (need Negotiable Instruments Act)",
]
