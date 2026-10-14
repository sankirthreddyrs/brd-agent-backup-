import re
from app.schemas import Requirement, GapQuestion

# Whole-word regex matching with optional plural 's'
# Matches e.g. "log", "logs", "login" NOT matching "log", "oauth" matches "oauth2.0"
CATEGORIES = [
    (
        "authentication",
        [r"\blogin\b", r"\bsign[- ]in\b", r"\boauth(\d+(\.\d+)?)?\b", r"\bpasswords?\b", r"\bsso\b"],
        "How should users authenticate (passwords, Google sign-in, SSO)?",
    ),
    (
        "authorization",
        [r"\broles?\b", r"\bpermissions?\b", r"\badmins?\b", r"\baccess control\b"],
        "Which user roles exist and what can each role do?",
    ),
    (
        "data retention and privacy",
        [r"\bretentions?\b", r"\bprivacy\b", r"\bgdpr\b", r"\bpersonal data\b", r"\bdelet(e|ion|ing)\b"],
        "How long should user data be kept, and what privacy rules apply?",
    ),
    (
        "performance",
        [r"\bconcurrent\b", r"\bresponse times?\b", r"\blatenc(y|ies)\b", r"\bloads?\b", r"\bperformances?\b"],
        "What performance targets (users, response time) must the system meet?",
    ),
    (
        "availability",
        [r"\buptime\b", r"\bavailabilit(y|ies)\b", r"\bdowntimes?\b", r"\bbackups?\b"],
        "What availability or backup expectations exist?",
    ),
    (
        "audit and logging",
        [r"\baudits?\b", r"\blogs?\b", r"\blogging\b"],
        "What actions must be logged for audit?",
    ),
    (
        "security",
        [r"\bencrypt(ion|ed|s)?\b", r"\bsecurity\b", r"\bsessions?\b", r"\btimeouts?\b", r"\btls\b"],
        "What security requirements apply (encryption, session rules)?",
    ),
]


def check_word_match(pattern: str, text: str) -> bool:
    """Case-insensitive regex search ensuring whole-word match."""
    return bool(re.search(pattern, text, re.IGNORECASE))


def coverage_gaps(requirements: list[Requirement]) -> list[GapQuestion]:
    """
    Find categories missing from VERIFIED requirements.
    Only verified requirements count as covering a category.
    """
    verified_texts = [
        req.text for req in requirements if req.verification_status == "verified"
    ]
    combined_text = " ".join(verified_texts)

    gaps: list[GapQuestion] = []

    for cat_name, patterns, question in CATEGORIES:
        covered = any(check_word_match(pat, combined_text) for pat in patterns)
        if not covered:
            gaps.append(GapQuestion(category=cat_name, question=question))

    return gaps
