from __future__ import annotations

import json
import os
import re
from typing import Any

from pydantic import ValidationError

from game_evidence_graph.llm.base import LLMClient
from game_evidence_graph.llm.prompts import STUDY_ONTOLOGY_PROMPT
from game_evidence_graph.schemas.paper import PaperDocument
from game_evidence_graph.schemas.study import Condition, Intervention, Outcome, Population, StudyOntology, StudyRecord

EVIDENCE_STRENGTHS = {
    "randomized_controlled_trial",
    "quasi_experimental",
    "case_control",
    "within_subject_experimental",
    "within_subject_observational",
    "between_subject_observational",
    "correlational",
    "pre_post_no_control",
    "qualitative",
    "mixed_methods",
    "not_reported",
    "unclear",
}

EFFECT_DIRECTIONS = {"positive", "negative", "null", "mixed", "not_reported", "unclear"}

GAME_MENTION_PATTERNS = [
    "Minecraft",
    "Nintendo Wii",
    "Wii Fit Plus",
    "Wii Fit",
    "Xbox Kinect",
    "Xbox 360",
    "Kinect Sports",
    "Kinect Joy Ride",
    "Kinect Adventures",
    "World of Warcraft",
    "Counter-Strike",
    "League of Legends",
    "Angry Birds",
    "Cut the Rope",
]

RESEARCH_CATEGORIES = {
    "Addiction",
    "Behavioral",
    "Economics",
    "Education",
    "Environmental",
    "Ethical",
    "Governance",
    "Learning",
    "Neuro/Cognitive",
    "Physiological",
    "Policy-making",
    "Psychological",
    "Sexualization",
    "Social",
    "Technological",
}

RESEARCH_CATEGORY_ALIASES = {
    "addiction": "Addiction",
    "addictive": "Addiction",
    "behavior": "Behavioral",
    "behaviour": "Behavioral",
    "behavioral": "Behavioral",
    "behavioural": "Behavioral",
    "economics": "Economics",
    "economic": "Economics",
    "education": "Education",
    "educational": "Education",
    "environment": "Environmental",
    "environmental": "Environmental",
    "ethics": "Ethical",
    "ethical": "Ethical",
    "governance": "Governance",
    "learning": "Learning",
    "neuro": "Neuro/Cognitive",
    "neurocognitive": "Neuro/Cognitive",
    "neuro_cognitive": "Neuro/Cognitive",
    "cognitive": "Neuro/Cognitive",
    "physiology": "Physiological",
    "physiological": "Physiological",
    "policy": "Policy-making",
    "policy_making": "Policy-making",
    "policy-making": "Policy-making",
    "psychology": "Psychological",
    "psychological": "Psychological",
    "sexualization": "Sexualization",
    "sexualisation": "Sexualization",
    "social": "Social",
    "technology": "Technological",
    "technological": "Technological",
}


def _slug(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text or fallback


def _controlled(value: Any, allowed: set[str], default: str = "unclear") -> str:
    if value is None:
        return default
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    aliases = {
        "case_control_design": "case_control",
        "case_control_study": "case_control",
        "randomized_control_trial": "randomized_controlled_trial",
        "randomised_controlled_trial": "randomized_controlled_trial",
        "rct": "randomized_controlled_trial",
        "pre_post": "pre_post_no_control",
        "pre_post_study": "pre_post_no_control",
        "not_specified": "not_reported",
        "none": "not_reported",
        "no_effect": "null",
        "no_difference": "null",
    }
    text = aliases.get(text, text)
    return text if text in allowed else default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_list(value: Any) -> list[str]:
    items: list[str] = []
    for item in _as_list(value):
        text = _string_or_none(item)
        if text:
            items.append(text)
    return items


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", []):
            return value
    return None


def _string_or_none(value: Any) -> str | None:
    if value in (None, "", []):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item not in (None, ""))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _int_or_none(value: Any) -> int | None:
    if value in (None, "", []):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    if value in (None, "", []):
        return None


def _normalize_research_categories(value: Any) -> list[str]:
    categories: list[str] = []
    for item in _as_list(value):
        text = _string_or_none(item)
        if not text:
            continue
        if text in RESEARCH_CATEGORIES:
            canonical = text
        else:
            key = re.sub(r"[^a-z0-9/-]+", "_", text.lower()).strip("_")
            key = key.replace("/", "_")
            canonical = RESEARCH_CATEGORY_ALIASES.get(key)
        if canonical and canonical not in categories:
            categories.append(canonical)
    return categories


def _study_text_blob(study: dict[str, Any], paper: PaperDocument | None = None) -> str:
    parts = [paper.metadata.title if paper else ""]
    try:
        parts.append(json.dumps(study, ensure_ascii=False))
    except TypeError:
        parts.append(str(study))
    return " ".join(part for part in parts if part)


def _infer_game_mentions(text: str) -> list[str]:
    mentions: list[str] = []
    lowered = text.lower()
    for pattern in GAME_MENTION_PATTERNS:
        if pattern.lower() in lowered and pattern not in mentions:
            mentions.append(pattern)
    return mentions


def _infer_research_categories(study: dict[str, Any], paper: PaperDocument) -> list[str]:
    explicit = _normalize_research_categories(
        _first_present(study, "research_categories", "research_category", "paper_categories", "domain", "domains")
    )
    if explicit:
        return explicit

    text = " ".join(
        _string_or_none(value) or ""
        for value in [
            paper.metadata.title,
            study.get("population"),
            study.get("outcome"),
            study.get("outcomes"),
            study.get("condition"),
            study.get("studied_condition"),
            study.get("studied_conditions"),
        ]
    ).lower()
    inferred: list[str] = []
    keyword_map = {
        "Addiction": ["addiction", "problematic gaming", "internet gaming disorder"],
        "Behavioral": ["behavior", "behaviour", "choice", "habit"],
        "Economics": ["economic", "economics", "market", "pricing"],
        "Education": ["school", "classroom", "student", "education"],
        "Environmental": ["environmental", "climate", "sustainability"],
        "Ethical": ["ethics", "ethical", "fairness"],
        "Governance": ["governance", "regulation", "compliance"],
        "Learning": ["learning", "knowledge", "concept map", "performance"],
        "Neuro/Cognitive": ["cognitive", "neural", "brain", "attention", "memory"],
        "Physiological": ["postural", "balance", "heart rate", "physiological", "fmri", "fnirs"],
        "Policy-making": ["policy", "policymaking", "policy-making"],
        "Psychological": ["motivation", "emotion", "empathy", "anxiety", "depression"],
        "Sexualization": ["sexualization", "sexualisation"],
        "Social": ["social", "cooperation", "team", "communication"],
        "Technological": ["technology", "platform", "virtual reality", "ai"],
    }
    for category, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            inferred.append(category)
    return inferred


def _normalize_studied_conditions(study: dict[str, Any]) -> list[str]:
    raw = _first_present(
        study,
        "studied_conditions",
        "studied_condition",
        "topic_conditions",
        "topic_condition",
        "health_condition",
        "clinical_condition",
        "condition_of_interest",
        "phenomenon",
    )
    conditions = _string_list(raw)
    if not conditions:
        population = study.get("population")
        if isinstance(population, dict):
            conditions = _string_list(
                _first_present(population, "studied_conditions", "health_condition", "clinical_condition", "diagnosis")
            )
    return conditions


def _normalize_population(study: dict[str, Any], index: int) -> Population:
    population = study.get("population")
    if isinstance(population, dict):
        data = dict(population)
        data.setdefault("population_id", f"pop_{index:03d}")
        data.setdefault("population_raw", _first_present(data, "population_raw", "description", "participants"))
        for key in [
            "population_id",
            "population_raw",
            "age_range",
            "gender",
            "country",
            "prior_gaming_experience",
        ]:
            data[key] = _string_or_none(data.get(key))
        data["population_id"] = data["population_id"] or f"pop_{index:03d}"
        data["studied_conditions"] = _string_list(
            _first_present(data, "studied_conditions", "health_condition", "clinical_condition", "diagnosis")
        )
        data["sample_size"] = _int_or_none(data.get("sample_size"))
        data["mean_age"] = _float_or_none(data.get("mean_age"))
        return Population.model_validate(data)
    return Population(
        population_id=f"pop_{index:03d}",
        population_raw=_string_or_none(_first_present(study, "population", "participants", "sample", "population_raw")),
        studied_conditions=_normalize_studied_conditions(study),
        sample_size=_int_or_none(_first_present(study, "sample_size", "n")),
        country=_string_or_none(study.get("country")),
        age_range=_string_or_none(study.get("age_range")),
        mean_age=_float_or_none(study.get("mean_age")),
        gender=_string_or_none(study.get("gender")),
    )


def _normalize_conditions(
    study_id: str, intervention_id: str, intervention: dict[str, Any], study: dict[str, Any], game_mentions_hint: list[str] | None = None
) -> list[Condition]:
    conditions = []
    for idx, condition in enumerate(_as_list(intervention.get("conditions")), start=1):
        if not isinstance(condition, dict):
            continue
        condition_type = str(condition.get("condition_type") or condition.get("type") or f"condition_{idx}")
        conditions.append(
            Condition(
                condition_id=condition.get("condition_id") or f"{study_id}_cond_{_slug(condition_type, str(idx)).lower()}",
                condition_type=condition_type.lower(),
                description=_string_or_none(condition.get("description") or condition.get("condition")),
                game_mentions=[str(x) for x in _as_list(condition.get("game_mentions") or condition.get("games"))] or (game_mentions_hint or []),
                game_ids=[str(x) for x in _as_list(condition.get("game_ids"))],
            )
        )
    if conditions:
        return conditions

    treatment = _first_present(intervention, "treatment_raw", "treatment", "intervention", "intervention_name") or _first_present(
        study, "treatment_raw", "treatment", "intervention"
    )
    control = _first_present(intervention, "control_raw", "control") or _first_present(study, "control_raw", "control")
    game_mentions = _as_list(
        _first_present(intervention, "game_mentions", "games", "game")
        or _first_present(study, "game_mentions", "games", "game")
    ) or (game_mentions_hint or [])
    if treatment:
        conditions.append(
            Condition(
                condition_id=f"{study_id}_cond_treatment",
                condition_type="treatment",
                description=_string_or_none(treatment),
                game_mentions=[str(x) for x in game_mentions],
            )
        )
    if control:
        conditions.append(
            Condition(
                condition_id=f"{study_id}_cond_control",
                condition_type="control",
                description=_string_or_none(control),
                game_mentions=[],
            )
        )
    if not conditions:
        conditions.append(
            Condition(
                condition_id=f"{study_id}_cond_unclear",
                condition_type="unclear",
                description=None,
                game_mentions=[str(x) for x in game_mentions],
            )
        )
    return conditions


def _normalize_interventions(study_id: str, study: dict[str, Any], game_mentions_hint: list[str] | None = None) -> list[Intervention]:
    raw_interventions = _as_list(study.get("interventions"))
    if not raw_interventions:
        raw_interventions = [study]

    interventions: list[Intervention] = []
    for idx, raw in enumerate(raw_interventions, start=1):
        intervention = raw if isinstance(raw, dict) else {"intervention_name": str(raw)}
        intervention_id = intervention.get("intervention_id") or f"{study_id}_int_{idx:02d}"
        interventions.append(
            Intervention(
                intervention_id=intervention_id,
                intervention_name=_string_or_none(_first_present(intervention, "intervention_name", "name", "intervention", "treatment")),
                treatment_raw=_string_or_none(
                    _first_present(intervention, "treatment_raw", "treatment")
                    or _first_present(study, "treatment_raw", "treatment")
                ),
                control_raw=_string_or_none(
                    _first_present(intervention, "control_raw", "control") or _first_present(study, "control_raw", "control")
                ),
                conditions=_normalize_conditions(study_id, intervention_id, intervention, study, game_mentions_hint),
            )
        )
    return interventions


def _dict_values_as_outcomes(raw: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for key in [
        "outcome_measures",
        "outcome_measure",
        "measured_outcomes",
        "measured_outcome",
        "dependent_variables",
        "dependent_variable",
        "measures",
        "measurements",
        "effects",
        "effect_evidence",
        "results",
        "findings",
    ]:
        values.extend(_as_list(raw.get(key)))
    return [value for value in values if value not in (None, "", [])]


def _normalize_outcome(raw: Any, study_id: str, index: int, study: dict[str, Any]) -> Outcome:
    if isinstance(raw, str):
        raw = {"outcome_raw": raw}
    outcome = dict(raw or {})
    outcome_raw = _string_or_none(_first_present(outcome, "outcome_raw", "outcome", "name", "construct", "label")) or "unclear"
    measurement = _first_present(outcome, "measurement_raw", "measurement", "measure", "instrument") or _first_present(
        study, "measurement", "measurements"
    )
    source_page = _first_present(outcome, "source_page", "page")
    return Outcome(
        outcome_id=_string_or_none(outcome.get("outcome_id")) or f"{study_id}_out_{index:03d}",
        outcome_raw=outcome_raw,
        outcome_canonical=_string_or_none(_first_present(outcome, "outcome_canonical", "canonical_outcome")) or "unclear",
        outcome_category=_string_or_none(_first_present(outcome, "outcome_category", "category")) or "unclear",
        measurement_id=_string_or_none(outcome.get("measurement_id")) or f"{study_id}_meas_{index:03d}",
        measurement_raw=_string_or_none(measurement),
        measurement_type=_string_or_none(_first_present(outcome, "measurement_type", "measure_type")),
        effect_direction=_controlled(_first_present(outcome, "effect_direction", "direction"), EFFECT_DIRECTIONS, "not_reported"),
        effect_size_raw=_string_or_none(_first_present(outcome, "effect_size_raw", "effect_size", "effect", "reported_effect")),
        effect_size_numeric=_float_or_none(outcome.get("effect_size_numeric")),
        effect_metric=_string_or_none(outcome.get("effect_metric")),
        p_value=_string_or_none(_first_present(outcome, "p_value", "p")),
        confidence_interval=_string_or_none(_first_present(outcome, "confidence_interval", "ci")),
        effect_target_measure=_string_or_none(outcome.get("effect_target_measure")),
        evidence_statement=_string_or_none(_first_present(outcome, "evidence_statement", "effect_statement", "summary")),
        source_quote=_string_or_none(_first_present(outcome, "source_quote", "evidence_quote", "quote")),
        source_page=_int_or_none(source_page),
        page_trace_status="found" if source_page is not None else "not_found",
    )


def _normalize_outcomes(study_id: str, study: dict[str, Any]) -> list[Outcome]:
    raw_outcomes = _as_list(study.get("outcomes"))
    raw_outcomes.extend(_dict_values_as_outcomes(study))
    if not raw_outcomes and _first_present(study, "outcome", "outcome_raw"):
        raw_outcomes = [_first_present(study, "outcome", "outcome_raw")]
    outcomes = [_normalize_outcome(raw, study_id, idx, study) for idx, raw in enumerate(raw_outcomes, start=1)]
    if outcomes:
        return outcomes

    fallback_conditions = _normalize_studied_conditions(study)
    if not fallback_conditions:
        return []
    return [
        Outcome(
            outcome_id=f"{study_id}_out_{idx:03d}",
            outcome_raw=condition,
            outcome_canonical="unclear",
            outcome_category="unclear",
            measurement_id=f"{study_id}_meas_{idx:03d}",
            measurement_raw=None,
            effect_direction="not_reported",
            page_trace_status="not_found",
        )
        for idx, condition in enumerate(fallback_conditions, start=1)
    ]


def normalize_study_record(study: dict[str, Any], paper: PaperDocument, index: int) -> StudyRecord:
    study_id = str(study.get("study_id") or f"{paper.metadata.paper_id}_study_{index:02d}")
    game_mentions_hint = _infer_game_mentions(_study_text_blob(study, paper))
    normalized = {
        "paper_id": _string_or_none(study.get("paper_id")) or paper.metadata.paper_id,
        "paper_title": _string_or_none(study.get("paper_title")) or paper.metadata.title,
        "doi": _string_or_none(study.get("doi")) or paper.metadata.doi,
        "year": study.get("year") or paper.metadata.year,
        "venue": _string_or_none(study.get("venue")) or paper.metadata.venue,
        "study_id": study_id,
        "study_label": _string_or_none(study.get("study_label") or study.get("label") or study.get("name")),
        "research_categories": _infer_research_categories(study, paper),
        "studied_conditions": _normalize_studied_conditions(study),
        "population": _normalize_population(study, index),
        "study_design": _controlled(study.get("study_design"), EVIDENCE_STRENGTHS),
        "evidence_strength": _controlled(study.get("evidence_strength") or study.get("study_design"), EVIDENCE_STRENGTHS),
        "context": _string_or_none(study.get("context") or study.get("setting")),
        "intervention_duration": _string_or_none(study.get("intervention_duration") or study.get("duration")),
        "interventions": _normalize_interventions(study_id, study, game_mentions_hint),
        "outcomes": _normalize_outcomes(study_id, study),
        "source_pdf": paper.metadata.source_pdf,
        "extraction_confidence": _float_or_none(study.get("extraction_confidence") or study.get("confidence")) or 0.5,
        "review_status": study.get("review_status") or "needs_review",
    }
    return StudyRecord.model_validate(normalized)


def page_numbered_text(paper: PaperDocument, max_chars: int = 30_000) -> str:
    parts: list[str] = []
    remaining = max_chars
    for page in paper.pages:
        if remaining <= 0:
            break
        text = f"[Page {page.page}]\n{page.text}\n"
        parts.append(text[:remaining])
        remaining -= len(parts[-1])
    return "\n".join(parts)


async def extract_studies_from_paper(client: LLMClient, paper: PaperDocument) -> list[StudyRecord]:
    max_chars = int(os.getenv("GAME_EVIDENCE_TEXT_MAX_CHARS", "30000"))
    payload = await client.complete_json(
        f"{STUDY_ONTOLOGY_PROMPT}\n"
        f"Paper metadata: {paper.metadata.model_dump_json()}\n"
        f"Text excerpt with page markers:\n{page_numbered_text(paper, max_chars=max_chars)}"
    )
    studies = payload.get("studies", [])
    records: list[StudyRecord] = []
    for index, study in enumerate(studies, start=1):
        if not isinstance(study, dict):
            continue
        try:
            records.append(normalize_study_record(study, paper, index))
        except ValidationError as exc:
            fallback = {
                "study_id": f"{paper.metadata.paper_id}_study_{index:02d}",
                "study_label": "Unvalidated LLM study extraction",
                "research_categories": [],
                "studied_conditions": [],
                "population": {"population_id": f"pop_{index:03d}", "population_raw": None},
                "study_design": "unclear",
                "evidence_strength": "unclear",
                "interventions": [],
                "outcomes": [],
                "paper_id": paper.metadata.paper_id,
                "paper_title": paper.metadata.title,
                "doi": paper.metadata.doi,
                "year": paper.metadata.year,
                "venue": paper.metadata.venue,
                "source_pdf": paper.metadata.source_pdf,
                "extraction_confidence": 0.0,
                "review_status": "needs_review",
            }
            record = StudyRecord.model_validate(fallback)
            record.study_label = f"{record.study_label}: {exc.errors()[0]['msg']}"
            records.append(record)
    return records


async def extract_study_ontology(client: LLMClient, papers: list[PaperDocument]) -> StudyOntology:
    all_studies: list[StudyRecord] = []
    paper_records: list[dict] = []
    total = len(papers)
    for index, paper in enumerate(papers, start=1):
        print(f"[extract-studies] {index}/{total} {paper.metadata.paper_id}: {paper.metadata.title}", flush=True)
        paper_records.append(paper.metadata.model_dump(mode="json"))
        all_studies.extend(await extract_studies_from_paper(client, paper))
    return StudyOntology(papers=paper_records, studies=all_studies)
