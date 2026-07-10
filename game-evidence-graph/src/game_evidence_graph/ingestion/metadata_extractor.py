from __future__ import annotations

import re
from pathlib import Path

from game_evidence_graph.schemas.paper import PaperMetadata, PageText

ARTICLE_MARKERS = {
    "article",
    "research article",
    "research report",
    "brief report",
    "review",
    "review article",
    "original article",
    "original research",
    "full length article",
    "full article",
    "registered report",
    "regular article",
    "systematic review",
}

TITLE_STOP_WORDS = {
    "abstract",
    "keywords",
    "key words",
    "palabras clave",
    "resumen",
    "introduction",
    "received",
    "accepted",
    "corresponding author",
    "e mail",
    "email",
}

NON_AUTHOR_TITLE_TERMS = {
    "addiction",
    "anxiety",
    "business",
    "children",
    "climate",
    "conflict",
    "contact",
    "cooperative",
    "cognitive",
    "disorder",
    "effects",
    "governance",
    "game",
    "games",
    "gaming",
    "innovation",
    "learning",
    "model",
    "pain",
    "social",
    "test",
    "video",
    "videogame",
    "virtual",
}


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\x02", "")).strip()


def _line_key(line: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()


def _is_header_noise(line: str) -> bool:
    key = _line_key(line)
    if not key:
        return True
    if key in {"a", "as", "in", "of", "on", "to"}:
        return False
    tokens = key.split()
    if len(tokens) >= 5 and sum(len(token) == 1 for token in tokens) / len(tokens) > 0.6:
        return True
    if key.startswith("journal of "):
        return True
    if key.startswith("special issue"):
        return True
    if "xxx xxxx xxx" in key:
        return True
    if key.startswith("www ") or "elsevier" in key or "sciencedirect" in key:
        return True
    if key.startswith("available online") or key.startswith("contents lists available"):
        return True
    if "journal homepage" in key or "all rights reserved" in key or "see front matter" in key:
        return True
    if "doi org" in key or "dx doi org" in key:
        return True
    if re.search(r"\b\d{4}\s+elsevier\b", key) or "copyright" in key:
        return True
    if re.fullmatch(r"\d+", key) or re.fullmatch(r"\(?\d{4}\)?", key):
        return True
    if re.fullmatch(r"\d+\s+\d{4}\s+\d+", key):
        return True
    if re.fullmatch(r"\d+\s+\d+", key):
        return True
    if re.search(r"\b\d+\s*\(\d{4}\)\s*\d+", line):
        return True
    if re.search(r"\b\d{4}\s*;\s*\d+", line):
        return True
    if len(line) <= 2 and line.lower() not in {"a", "as", "in", "of", "on", "to"}:
        return True
    if line.isupper() and len(line.split()) <= 4 and key not in ARTICLE_MARKERS:
        return True
    return False


def _has_title_terms(line: str) -> bool:
    return bool(set(_line_key(line).split()) & NON_AUTHOR_TITLE_TERMS)


def _is_probable_person_line(line: str) -> bool:
    if ":" in line or "?" in line or _has_title_terms(line):
        return False
    words = line.split()
    if not 2 <= len(words) <= 10:
        return False
    capitalized_tokens = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]{2,}", line)
    return len(capitalized_tokens) >= 2


def _is_single_author_name_after_title(line: str, title_lines: list[str]) -> bool:
    if len(_join_title_lines(title_lines).split()) < 8:
        return False
    if len(line.split()) != 1:
        return False
    key = _line_key(line)
    if key in {"a", "an", "and", "as", "for", "in", "of", "on", "the", "to", "with"}:
        return False
    return bool(re.fullmatch(r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]{2,}", line))


def _is_author_continuation_after_title(line: str, title_lines: list[str]) -> bool:
    if len(_join_title_lines(title_lines).split()) < 8:
        return False
    return bool(re.search(r"\b[a-z]\s*,", line) and re.search(r"[A-Z]\.|[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]+", line))


def _is_probable_author_line(line: str) -> bool:
    if re.match(r"^[A-Z]\.$", line):
        return True
    if re.search(r"\b(PhD|MSc|BSc|MD|MA|MBChB|MPH|RN)\b", line):
        return True
    if re.search(r"\b(department|university|institute|school of|faculty of)\b", line, flags=re.I):
        return True
    if re.search(r"\b[A-Z]\.[A-Z]?\.\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]+", line):
        return True
    if re.search(r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]+,\s+[A-Z]\.", line):
        return True
    if re.search(r"\b[a-z]\s*,\s*[⁎*]?\s*,", line) or re.search(r"\b[a-z]\s*,\s*[⁎*]", line):
        capitalized_tokens = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]{2,}", line)
        if len(capitalized_tokens) >= 2:
            return True
    if "*" in line:
        capitalized_tokens = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]{2,}", line)
        if len(capitalized_tokens) >= 2 and len(line.split()) <= 18:
            return True
    if "," in line and ":" not in line and not _has_title_terms(line):
        capitalized_tokens = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ-]{2,}", line)
        if len(capitalized_tokens) >= 3 and len(line.split()) <= 18:
            return True
    if _is_probable_person_line(line):
        return True
    return False


def _is_title_stop(line: str) -> bool:
    key = _line_key(line)
    return any(key.startswith(stop) for stop in TITLE_STOP_WORDS) or _is_probable_author_line(line)


def _join_title_lines(lines: list[str]) -> str:
    title = " ".join(lines)
    title = re.sub(r"\s+([:;,.])", r"\1", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    return title


def _is_uppercase_title_line(line: str) -> bool:
    key = _line_key(line)
    if not key or key in ARTICLE_MARKERS:
        return False
    tokens = key.split()
    if len(tokens) >= 5 and sum(len(token) == 1 for token in tokens) / len(tokens) > 0.6:
        return False
    if any(term in key for term in ["copyright", "elsevier", "journal", "volume", "www", "doi"]):
        return False
    letters = [char for char in line if char.isalpha()]
    return bool(letters) and all(char.upper() == char for char in letters)


def _title_from_leading_uppercase_block(lines: list[str]) -> str | None:
    title_lines: list[str] = []
    for line in lines[:12]:
        key = _line_key(line)
        if key in ARTICLE_MARKERS:
            return None
        if _is_uppercase_title_line(line):
            title_lines.append(line)
            continue
        break
    title = _join_title_lines(title_lines)
    if len(title.split()) >= 5:
        return title.title()
    return None


def _title_from_article_marker(lines: list[str]) -> str | None:
    seen_abstract = False
    for idx, line in enumerate(lines):
        if idx > 30:
            break
        key = _line_key(line)
        if key == "abstract" or key == "a b s t r a c t":
            seen_abstract = True
        if seen_abstract:
            continue
        next_key = _line_key(lines[idx + 1]) if idx + 1 < len(lines) else ""
        marker = (
            key in ARTICLE_MARKERS
            or f"{key} {next_key}" in ARTICLE_MARKERS
            or "research report" in key
            or "full article" in key
        )
        if not marker:
            continue

        start = idx + 2 if f"{key} {next_key}" in ARTICLE_MARKERS and key in {"review", "research"} else idx + 1
        title_lines: list[str] = []
        for candidate in lines[start:]:
            if _is_header_noise(candidate):
                continue
            if _is_author_continuation_after_title(candidate, title_lines):
                break
            if _is_single_author_name_after_title(candidate, title_lines):
                break
            if _is_title_stop(candidate) and (title_lines or not _is_probable_person_line(candidate)):
                break
            title_lines.append(candidate)
            if len(_join_title_lines(title_lines)) > 220:
                break
        title = _join_title_lines(title_lines)
        if len(title.split()) >= 5:
            return title
    return None


def infer_title(pages: list[PageText], fallback: str) -> str:
    text = "\n".join(page.text for page in pages[:2])
    lines = [_clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    uppercase_title = _title_from_leading_uppercase_block(lines)
    if uppercase_title:
        return uppercase_title

    marker_title = _title_from_article_marker(lines)
    if marker_title:
        return marker_title

    candidates: list[str] = []
    for idx, line in enumerate(lines[:80]):
        key = _line_key(line)
        next_key = _line_key(lines[idx + 1]) if idx + 1 < len(lines) else ""
        if key in ARTICLE_MARKERS or "research report" in key or "full article" in key:
            continue
        if next_key.startswith("journal homepage"):
            continue
        if _is_header_noise(line):
            if candidates:
                break
            continue
        if _is_title_stop(line):
            if candidates:
                break
            continue
        if _is_author_continuation_after_title(line, candidates):
            break
        if _is_single_author_name_after_title(line, candidates):
            break
        candidates.append(line)
        title = _join_title_lines(candidates)
        if len(title.split()) > 35 or len(title) > 260:
            break
    title = _join_title_lines(candidates)
    if len(title.split()) >= 5:
        return title
    return fallback


def extract_metadata(paper_id: str, pdf_path: str | Path, pages: list[PageText]) -> PaperMetadata:
    first_text = pages[0].text if pages else ""
    all_text = "\n".join(page.text for page in pages[:2])
    title = infer_title(pages, Path(pdf_path).stem)
    year_match = re.search(r"\b(19|20)\d{2}\b", first_text)
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", all_text, flags=re.I)
    return PaperMetadata(
        paper_id=paper_id,
        title=title,
        year=int(year_match.group(0)) if year_match else None,
        doi=doi_match.group(0) if doi_match else None,
        source_pdf=Path(pdf_path).name,
    )
