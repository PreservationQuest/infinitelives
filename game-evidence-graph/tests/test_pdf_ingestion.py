from game_evidence_graph.ingestion.text_cleaner import clean_page_text
from game_evidence_graph.ingestion.metadata_extractor import infer_title
from game_evidence_graph.schemas.paper import PageText


def test_text_cleaner_preserves_content():
    assert clean_page_text("Game-\nbased  review") == "Gamebased review"


def test_title_extractor_skips_journal_header():
    page = PageText(
        page=1,
        text=(
            "Neurología\n36\n(2021)\n618—624\nNEUROLOGÍA\nwww.elsevier.es/neurologia\n"
            "REVIEW\nARTICLE\nUse of commercial\nvideo games\nto improve postural\n"
            "balance\nin patients with multiple\nsclerosis:\nA\nsystematic\nreview\n"
            "and meta-analysis\nof randomised\ncontrolled\nclinical\ntrials\n"
            "M.\nParra-Moreno a, J.J.\n"
        ),
    )
    assert infer_title([page], "fallback").startswith("Use of commercial video games")


def test_title_extractor_skips_elsevier_homepage_and_report_marker():
    page = PageText(
        page=1,
        text=(
            "www.elsevier.com/locate/brainres\n"
            "Available online at www.sciencedirect.com\n"
            "Research Report\n"
            "The effects of an action video game on visual and affective\n"
            "information processing\n"
            "Kira Baileya,n, Robert Westb\n"
            "aDepartment of Psychological Sciences, University of Missouri\n"
            "a r t i c l e i n f o\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "The effects of an action video game on visual and affective information processing"
    )


def test_title_extractor_skips_journal_citation_line():
    page = PageText(
        page=1,
        text=(
            "Technological Forecasting & Social Change 174 (2022) 121210\n"
            "Available online 25 September 2021\n"
            "0040-1625/© 2021 Elsevier Inc. All rights reserved.\n"
            "Business model innovation in video-game consoles to face the threats of\n"
            "mobile gaming: Evidence from the case of Sony PlayStation\n"
            "Francesco Lantano *, Antonio Messeni Petruzzelli, Umberto Panniello\n"
            "Department of Mechanics, Mathematics, and Management\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "Business model innovation in video-game consoles to face the threats of "
        "mobile gaming: Evidence from the case of Sony PlayStation"
    )


def test_title_extractor_stops_before_credentialed_authors():
    page = PageText(
        page=1,
        text=(
            "ORIGINAL ARTICLE\n"
            "Activity and Energy Expenditure in Older People Playing\n"
            "Active Video Games\n"
            "Lynne M. Taylor, MSc, Ralph Maddison, PhD, Leila A. Pfaeffli, MA\n"
            "ABSTRACT. Taylor LM, Maddison R.\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "Activity and Energy Expenditure in Older People Playing Active Video Games"
    )


def test_title_extractor_uses_leading_uppercase_title_block():
    page = PageText(
        page=1,
        text=(
            "VIOLENT VIDEO GAMES: SPECIFIC\n"
            "EFFECTS OF VIOLENT CONTENT\n"
            "ON AGGRESSIVE THOUGHTS\n"
            "AND BEHAVIOR\n"
            "Craig A. Anderson\n"
            "Three experimental studies, one correlational study, and a meta-analysis\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "Violent Video Games: Specific Effects Of Violent Content On Aggressive Thoughts And Behavior"
    )


def test_title_extractor_stops_before_affiliation_marker_authors():
    page = PageText(
        page=1,
        text=(
            "Brands in virtual reality games: Affective processes within\n"
            "computer-mediated consumer experiences\n"
            "Zeph M.C. van Berlo a,*, Eva A. van Reijmersdal a, Edith G. Smit a\n"
            "a Amsterdam School of Communication Research\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "Brands in virtual reality games: Affective processes within "
        "computer-mediated consumer experiences"
    )


def test_title_extractor_handles_fragmented_review_title():
    page = PageText(
        page=1,
        text=(
            "Review\n"
            "article\n"
            "Counter\n"
            "striking\n"
            "psychosis:\n"
            "Commercial\n"
            "video\n"
            "games\n"
            "as\n"
            "potential\n"
            "treatment\n"
            "in\n"
            "schizophrenia?\n"
            "A\n"
            "systematic\n"
            "review\n"
            "of\n"
            "neuroimaging\n"
            "studies\n"
            "Claudia\n"
            "Suenderhauf ∗, Anna Walter\n"
        ),
    )
    assert infer_title([page], "fallback") == (
        "Counter striking psychosis: Commercial video games as potential treatment in "
        "schizophrenia? A systematic review of neuroimaging studies"
    )
