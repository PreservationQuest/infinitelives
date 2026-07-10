import asyncio

from game_evidence_graph.extraction.study_extractor import normalize_study_record, page_numbered_text
from game_evidence_graph.extraction.study_extractor import extract_study_ontology
from game_evidence_graph.llm.mock_client import MockLLMClient
from game_evidence_graph.schemas.paper import PageText, PaperDocument, PaperMetadata


def test_mock_extraction_empty_without_paid_calls():
    ontology = asyncio.run(extract_study_ontology(MockLLMClient(), []))
    assert ontology.studies == []


def test_flat_llm_study_shape_is_normalized():
    paper = PaperDocument(
        metadata=PaperMetadata(
            paper_id="paper_001",
            title="Game Study",
            year=2024,
            doi="10.123/example",
            source_pdf="paper.pdf",
        ),
        pages=[PageText(page=1, text="Participants played a game.")],
    )
    record = normalize_study_record(
        {
            "study_id": "Nilsagard_Study1",
            "population": "Adults with Parkinson disease.",
            "treatment": "Balance training with a game.",
            "control": "Conventional balance training.",
            "outcomes": ["balance"],
            "measurement": ["Timed Up and Go"],
            "study_design": "randomized controlled trial",
            "studied_conditions": ["multiple sclerosis"],
            "research_categories": ["Physiological"],
            "confidence": 0.72,
        },
        paper,
        1,
    )
    assert record.paper_id == "paper_001"
    assert record.population.population_raw == "Adults with Parkinson disease."
    assert record.interventions[0].conditions[0].condition_type == "treatment"
    assert record.outcomes[0].measurement_raw == "Timed Up and Go"
    assert record.evidence_strength == "randomized_controlled_trial"
    assert record.research_categories == ["Physiological"]
    assert record.studied_conditions == ["multiple sclerosis"]
    assert record.population.studied_conditions == ["multiple sclerosis"]


def test_page_numbered_text_is_bounded():
    paper = PaperDocument(
        metadata=PaperMetadata(paper_id="paper_001"),
        pages=[PageText(page=1, text="a" * 100), PageText(page=2, text="b" * 100)],
    )
    text = page_numbered_text(paper, max_chars=50)
    assert "[Page 1]" in text
    assert len(text) <= 51


def test_llm_list_and_dict_string_fields_are_coerced():
    paper = PaperDocument(
        metadata=PaperMetadata(paper_id="paper_001", title="Game Study"),
        pages=[PageText(page=1, text="Participants played a game.")],
    )
    record = normalize_study_record(
        {
            "study_id": "paper_001_study_01",
            "population": {"participants": ["adults", "patients"], "sample_size": "12"},
            "interventions": [
                {
                    "intervention_name": ["game", "training"],
                    "treatment": {"description": "exergame training"},
                    "control": ["usual care"],
                }
            ],
            "outcomes": [
                {
                    "outcome": ["balance", "mobility"],
                    "measurement": {"instrument": "Timed Up and Go"},
                    "source_quote": ["Participants improved on balance measures."],
                }
            ],
        },
        paper,
        1,
    )
    assert record.population.population_raw
    assert record.interventions[0].intervention_name == "game; training"
    assert "exergame training" in record.interventions[0].treatment_raw
    assert record.outcomes[0].outcome_raw == "balance; mobility"
    assert "Timed Up and Go" in record.outcomes[0].measurement_raw


def test_research_categories_can_be_inferred_from_title_and_outcome():
    paper = PaperDocument(
        metadata=PaperMetadata(
            paper_id="paper_001",
            title="Use of commercial video games to improve postural balance in patients with multiple sclerosis",
        ),
        pages=[PageText(page=1, text="Participants played a game.")],
    )
    record = normalize_study_record(
        {
            "study_id": "paper_001_study_01",
            "population": {"population_raw": "Patients with multiple sclerosis", "diagnosis": "multiple sclerosis"},
            "treatment": "Commercial exergame therapy",
            "control": "Conventional physical therapy",
            "outcomes": ["postural balance"],
        },
        paper,
        1,
    )
    assert "Physiological" in record.research_categories
    assert record.studied_conditions == ["multiple sclerosis"]
    assert {condition.condition_type for condition in record.interventions[0].conditions} == {"treatment", "control"}


def test_game_mentions_and_outcomes_fallbacks_are_derived():
    paper = PaperDocument(
        metadata=PaperMetadata(
            paper_id="paper_001",
            title="Gaming for peace: Virtual contact through cooperative video gaming",
        ),
        pages=[PageText(page=1, text="Participants played Minecraft in cooperative teams.")],
    )
    record = normalize_study_record(
        {
            "study_id": "paper_001_study_01",
            "population": "School-aged children",
            "intervention": "Virtual cooperative multiplayer Minecraft intervention",
            "studied_conditions": ["intergroup tolerance"],
        },
        paper,
        1,
    )
    assert record.interventions[0].conditions[0].game_mentions == ["Minecraft"]
    assert record.outcomes[0].outcome_raw == "intergroup tolerance"
    assert record.outcomes[0].effect_direction == "not_reported"
