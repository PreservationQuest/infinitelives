from __future__ import annotations

import re


SECTION_RE = re.compile(r"^(abstract|introduction|methods?|results?|discussion|conclusion|references)\b", re.I)


def parse_sections(page_text: str) -> list[dict]:
    sections: list[dict] = []
    current = {"heading": "front_matter", "text": ""}
    for line in page_text.splitlines():
        if SECTION_RE.match(line.strip()):
            if current["text"].strip():
                sections.append(current)
            current = {"heading": line.strip(), "text": ""}
        else:
            current["text"] += line + "\n"
    if current["text"].strip():
        sections.append(current)
    return sections
