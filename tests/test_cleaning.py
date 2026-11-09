"""One small test per cleaning rule, using real CV text."""

from cvrag.parsing import PAGE_BREAK
from cvrag.parsing.cleaning import clean_text, clean_text_with_report

RAW_PAGE = (
    "Synthetic CV for training/demo purposes \n"
    "Fadi Salem \n"
    "CRM & Marketing Automation Specialist \n"
    "PROFESSIONAL SUMMARY \n"
    "CRM and Marketing Automation Specialist with experience designing lifecycle "
    "journeys, segmentation, and email automation. Skilled in \n"
    "HubSpot, customer data, campaign logic, and reporting. \n"
    "CORE SKILLS \n"
    "HubSpot  •  Mailchimp  •  CRM  •  Email Automation \n"
    "EXPERIENCE \n"
    "CRM Specialist | LoopCommerce \n"
    "2024 - Present \n"
    "• Built onboarding, re-engagement, and lead-nurturing email journeys. \n"
    "• Created customer segments using behavior and lifecycle stage data. \n"
)


def clean_lines(raw: str) -> list[str]:
    """Clean raw text and return it as a list of lines."""
    return clean_text(raw).split("\n")


# --- Step 1: characters -------------------------------------------------------


def test_invisible_characters_are_removed():
    assert clean_text("Fadi​ Salem﻿") == "Fadi Salem"


def test_non_breaking_space_becomes_a_normal_space():
    assert clean_text("Fadi Salem") == "Fadi Salem"


def test_carriage_returns_become_newlines_without_merging_lines():
    assert clean_text("EXPERIENCE\r\nEDUCATION\rPROJECTS") == "EXPERIENCE\nEDUCATION\nPROJECTS"


# --- Step 2: noise lines ------------------------------------------------------


def test_synthetic_banner_is_removed():
    cleaned, report = clean_text_with_report(RAW_PAGE)
    assert "Synthetic CV for training/demo purposes" not in cleaned
    assert "Synthetic CV for training/demo purposes" in report["removed_lines"]


def test_page_number_line_is_removed():
    cleaned, report = clean_text_with_report("PROJECTS \nPage 1 of 2 \n")
    assert cleaned == "PROJECTS"
    assert report["removed_lines"] == ["Page 1 of 2"]


def test_repeated_header_is_kept_once_across_two_pages():
    raw = (
        "Fadi Salem - CV \nEXPERIENCE \n- Built onboarding journeys. \n"
        f"{PAGE_BREAK}"
        "Fadi Salem - CV \nEDUCATION \n- BSc Marketing. \n"
    )
    cleaned, report = clean_text_with_report(raw)
    assert cleaned.count("Fadi Salem - CV") == 1
    assert cleaned.startswith("Fadi Salem - CV")
    assert "Fadi Salem - CV" in report["removed_lines"]


def test_repeated_header_is_kept_on_a_single_page_document():
    cleaned = clean_text("Fadi Salem - CV \nEXPERIENCE \n- Built journeys. \n")
    assert cleaned.startswith("Fadi Salem - CV")


# --- Step 3: whitespace -------------------------------------------------------


def test_no_line_ends_with_a_space():
    cleaned = clean_text(RAW_PAGE)
    for page in cleaned.split(PAGE_BREAK):
        for line in page.split("\n"):
            assert line == line.rstrip()


def test_inline_bullet_separators_keep_their_characters():
    assert "HubSpot • Mailchimp • CRM • Email Automation" in clean_text(RAW_PAGE)


# --- Step 4: bullets ----------------------------------------------------------


def test_bullet_lines_are_normalized():
    cleaned, report = clean_text_with_report(RAW_PAGE)
    assert "- Built onboarding, re-engagement, and lead-nurturing email journeys." in cleaned
    assert "- Created customer segments using behavior and lifecycle stage data." in cleaned
    assert report["bullets_normalized"] == 2


def test_dash_bullet_is_not_counted_as_a_change():
    _, report = clean_text_with_report("- Built onboarding journeys. \n")
    assert report["bullets_normalized"] == 0


# --- Step 5: wrapped lines ----------------------------------------------------


def test_continuation_word_joins_the_wrapped_paragraph():
    cleaned, report = clean_text_with_report(RAW_PAGE)
    assert (
        "CRM and Marketing Automation Specialist with experience designing lifecycle "
        "journeys, segmentation, and email automation. Skilled in HubSpot, customer "
        "data, campaign logic, and reporting." in cleaned
    )
    assert any(a.endswith("Skilled in") for a, _ in report["joined_lines"])


def test_trailing_comma_joins_the_next_line():
    assert clean_text("Python, SQL, \nDocker \n") == "Python, SQL, Docker"


def test_lowercase_start_joins_a_wrapped_bullet():
    raw = (
        "- Connected forms, CRM, and notification workflows using \n"
        "automation tools. \n"
    )
    assert clean_text(raw) == (
        "- Connected forms, CRM, and notification workflows using automation tools."
    )


def test_a_joined_chain_stops_at_the_next_job_title():
    raw = (
        "- Connected forms, CRM, and notification workflows using \n"
        "automation tools \n"
        "Marketing Operations Coordinator | MarketNest \n"
    )
    assert clean_lines(raw) == [
        "- Connected forms, CRM, and notification workflows using automation tools",
        "Marketing Operations Coordinator | MarketNest",
    ]


def test_a_finished_bullet_does_not_swallow_the_next_job_title():
    raw = (
        "- Produced campaign reports for open, click, and conversion rates across 4 markets \n"
        "Marketing Operations Coordinator | MarketNest \n"
    )
    assert clean_lines(raw) == [
        "- Produced campaign reports for open, click, and conversion rates across 4 markets",
        "Marketing Operations Coordinator | MarketNest",
    ]


def test_job_title_and_date_stay_on_separate_lines():
    lines = clean_lines(RAW_PAGE)
    assert "CRM Specialist | LoopCommerce" in lines
    assert "2024 - Present" in lines


def test_numeric_date_range_stays_on_its_own_line():
    assert clean_lines("CRM Specialist | LoopCommerce \n03/2021 - 05/2023 \n") == [
        "CRM Specialist | LoopCommerce",
        "03/2021 - 05/2023",
    ]


def test_headings_stay_on_their_own_lines():
    lines = clean_lines(RAW_PAGE)
    for heading in ("PROFESSIONAL SUMMARY", "CORE SKILLS", "EXPERIENCE"):
        assert heading in lines


def test_a_sentence_end_blocks_a_join():
    assert clean_lines("Built journeys. \nand measured them \n") == [
        "Built journeys.",
        "and measured them",
    ]


def test_a_hyphen_break_joins_without_a_space():
    assert clean_text("Designed multi- \nchannel campaigns \n") == (
        "Designed multi-channel campaigns"
    )


def test_a_bullet_never_joins_onto_the_previous_line():
    assert clean_lines("Achievements, \n- Built journeys \n") == [
        "Achievements,",
        "- Built journeys",
    ]


def test_lines_are_never_joined_across_a_page_break():
    raw = f"Skilled in \n{PAGE_BREAK}HubSpot and CRM \n"
    assert clean_text(raw) == f"Skilled in{PAGE_BREAK}HubSpot and CRM"


# --- Step 6: final tidy -------------------------------------------------------


def test_repeated_empty_lines_are_collapsed():
    assert clean_text("EXPERIENCE \n\n\n\nEDUCATION \n") == "EXPERIENCE\n\nEDUCATION"


def test_blank_lines_around_a_page_are_trimmed():
    assert clean_text("\n\nFadi Salem \n\n\n") == "Fadi Salem"


# --- Whole pipeline -----------------------------------------------------------


def test_page_breaks_are_preserved():
    raw = f"Fadi Salem \n{PAGE_BREAK}EDUCATION \n"
    cleaned = clean_text(raw)
    assert cleaned.count(PAGE_BREAK) == 1
    assert cleaned == f"Fadi Salem{PAGE_BREAK}EDUCATION"


def test_full_page_matches_the_expected_result():
    assert clean_lines(RAW_PAGE) == [
        "Fadi Salem",
        "CRM & Marketing Automation Specialist",
        "PROFESSIONAL SUMMARY",
        "CRM and Marketing Automation Specialist with experience designing lifecycle "
        "journeys, segmentation, and email automation. Skilled in HubSpot, customer "
        "data, campaign logic, and reporting.",
        "CORE SKILLS",
        "HubSpot • Mailchimp • CRM • Email Automation",
        "EXPERIENCE",
        "CRM Specialist | LoopCommerce",
        "2024 - Present",
        "- Built onboarding, re-engagement, and lead-nurturing email journeys.",
        "- Created customer segments using behavior and lifecycle stage data.",
    ]


def test_cleaning_already_clean_text_changes_nothing():
    cleaned = clean_text(RAW_PAGE)
    again, report = clean_text_with_report(cleaned)
    assert again == cleaned
    assert report == {"removed_lines": [], "joined_lines": [], "bullets_normalized": 0}


def test_report_has_the_expected_keys():
    _, report = clean_text_with_report(RAW_PAGE)
    assert set(report) == {"removed_lines", "joined_lines", "bullets_normalized"}
    assert all(len(pair) == 2 for pair in report["joined_lines"])
