"""
Content Classifier — Pre-LLM content analysis.

Classifies walkthrough text as narrative, tabular, meta, or insufficient
BEFORE sending to the LLM. This saves tokens and reduces hallucination
by filtering out non-narrative content that produces bad extractions.

Edge cases handled:
- Item lists disguised as walkthroughs
- Stat tables and crafting recipes
- Author notes, spoiler warnings, version history
- Very short sections (< 30 words)
- Mixed content with narrative + tables
"""
import re
from models.schemas import ContentType


# Meta-text patterns (author notes, spoiler warnings, etc.)
META_PATTERNS = [
    r"(?i)^(version|revision|changelog|update)\s*(history|log|notes)?",
    r"(?i)^(written|authored|created)\s+by\b",
    r"(?i)^(copyright|©|\(c\))\s",
    r"(?i)\b(spoiler\s+warning|spoiler\s+alert|warning:?\s+spoilers)\b",
    r"(?i)^(table\s+of\s+contents|contents:)",
    r"(?i)\b(donate|paypal|patreon|buy\s+me\s+a\s+coffee)\b",
    r"(?i)^(contact|email|discord):?\s",
    r"(?i)^(faq|frequently\s+asked\s+questions)\s*$",
    r"(?i)\b(this\s+guide\s+is\s+protected|all\s+rights\s+reserved)\b",
    r"(?i)^(special\s+thanks|acknowledgements|credits)\s*$",
]

# Tabular content indicators
TABULAR_INDICATORS = [
    r"\|.*\|.*\|",                    # Markdown/wiki table rows
    r"^\s*[-=]{3,}\s*$",             # Table separators
    r"^\s*\w+\s*:\s*\d+",            # Name: Value pairs (stats)
    r"^\s*-\s+\w+\s*[-–]\s*\d+",     # - Item - 50 (item lists with values)
]

# Narrative indicators (gameplay descriptions)
NARRATIVE_INDICATORS = [
    r"\b(you|player|character)\b.*\b(can|should|must|need|will)\b",
    r"\b(head|go|walk|run|move|travel|proceed)\b.*\b(to|toward|north|south|east|west|left|right)\b",
    r"\b(fight|attack|defeat|kill|dodge|block|parry)\b",
    r"\b(pick\s+up|grab|collect|loot|open|chest|treasure)\b",
    r"\b(puzzle|solve|activate|switch|lever|button|pressure\s+plate)\b",
    r"\b(boss|enemy|monster|creature|NPC)\b",
    r"\b(health|mana|stamina|HP|MP)\b.*\b(restore|deplete|manage)\b",
    r"\b(save|checkpoint|respawn|die|death|game\s+over)\b",
]


def classify_content(text: str) -> ContentType:
    """
    Classify walkthrough text content type.

    Returns:
        ContentType enum indicating the dominant content type.
    """
    if not text or not text.strip():
        return ContentType.INSUFFICIENT

    words = text.split()
    word_count = len(words)

    # Edge case: too short
    if word_count < 30:
        return ContentType.INSUFFICIENT

    lines = text.strip().split("\n")
    non_empty_lines = [l for l in lines if l.strip()]
    total_lines = max(len(non_empty_lines), 1)

    # Count meta-text matches
    meta_matches = sum(1 for pattern in META_PATTERNS
                       for line in non_empty_lines
                       if re.search(pattern, line))

    # Count tabular indicators
    tabular_matches = sum(1 for pattern in TABULAR_INDICATORS
                         for line in non_empty_lines
                         if re.search(pattern, line))

    # Count narrative indicators
    narrative_matches = sum(1 for pattern in NARRATIVE_INDICATORS
                           if re.search(pattern, text, re.IGNORECASE))

    # Numeric content ratio (high = tabular data)
    numeric_tokens = sum(1 for w in words if re.match(r"^\d+[\d,./%]*$", w))
    numeric_ratio = numeric_tokens / max(word_count, 1)

    # Bullet point ratio (high = list content)
    bullet_lines = sum(1 for l in non_empty_lines if re.match(r"^\s*[-*•]\s", l))
    bullet_ratio = bullet_lines / total_lines

    # Decision logic
    meta_ratio = meta_matches / total_lines
    tabular_ratio = tabular_matches / total_lines

    # Meta only if it dominates AND no narrative content
    if meta_ratio > 0.3 and narrative_matches < 2:
        return ContentType.META

    # Tabular requires BOTH structural indicators AND low narrative
    if (tabular_ratio > 0.3 or numeric_ratio > 0.3) and narrative_matches < 2:
        return ContentType.TABULAR

    if bullet_ratio > 0.6 and numeric_ratio > 0.15 and narrative_matches < 2:
        return ContentType.TABULAR

    if narrative_matches >= 2:
        return ContentType.NARRATIVE

    # Mixed if has some narrative but also tabular/meta elements
    if narrative_matches >= 1 and (tabular_ratio > 0.1 or meta_ratio > 0.1):
        return ContentType.MIXED

    if word_count >= 50:
        return ContentType.MIXED

    return ContentType.INSUFFICIENT


def compute_source_quality(text: str, content_type: ContentType) -> float:
    """
    Score the quality of source text for MDA extraction (0-1).
    Higher = more likely to produce good extractions.
    """
    if content_type == ContentType.INSUFFICIENT:
        return 0.0
    if content_type == ContentType.META:
        return 0.1
    if content_type == ContentType.TABULAR:
        return 0.2

    word_count = len(text.split())
    narrative_matches = sum(1 for pattern in NARRATIVE_INDICATORS
                           if re.search(pattern, text, re.IGNORECASE))

    # Base score from content type
    base = 0.5 if content_type == ContentType.MIXED else 0.7

    # Bonus for length (more text = more extractable events)
    length_bonus = min(word_count / 500, 0.15)

    # Bonus for narrative density
    density_bonus = min(narrative_matches / 8, 0.15)

    return min(base + length_bonus + density_bonus, 1.0)


def strip_meta_content(text: str) -> str:
    """Remove meta-text sections from walkthrough content."""
    lines = text.split("\n")
    cleaned = []
    skip_section = False

    for line in lines:
        # Check if this line starts a meta section
        is_meta = any(re.search(p, line) for p in META_PATTERNS)

        if is_meta:
            skip_section = True
            continue

        # Reset skip on new section header
        if line.strip().startswith("## "):
            skip_section = False

        if not skip_section:
            cleaned.append(line)

    return "\n".join(cleaned)
