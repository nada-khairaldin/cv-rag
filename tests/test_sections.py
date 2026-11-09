"""One small test per section-detection rule, using real cleaned CV text."""

from cvrag.parsing import PAGE_BREAK
from cvrag.parsing.sections import detect_sections, detect_sections_with_report

# The Fadi Salem CV as clean_text leaves it.
CLEANED_CV = "\n".join([
    "Fadi Salem",
    "CRM & Marketing Automation Specialist",
    "Dubai, UAE | fadi.salem@example.com | +971 52 555 0403 | linkedin.com/in/fadi-crm",
    "PROFESSIONAL SUMMARY",
    "CRM and Marketing Automation Specialist with experience designing lifecycle "
    "journeys, segmentation, and email automation. Skilled in HubSpot, customer data, "
    "campaign logic, and reporting.",
    "CORE SKILLS",
    "HubSpot • Mailchimp • CRM • Email Automation • Customer Segmentation "
    "• Lead Scoring • Zapier • GA4 • Excel",
    "EXPERIENCE",
    "CRM Specialist | LoopCommerce",
    "2024 - Present",
    "- Built onboarding, re-engagement, and lead-nurturing email journeys.",
    "- Created customer segments using behavior and lifecycle stage data.",
    "- Connected forms, CRM, and notification workflows using automation tools.",
    "Marketing Operations Coordinator | MarketNest",
    "2022 - 2024",
    "- Maintained CRM data quality and supported campaign list preparation.",
    "- Produced campaign reports for open, click, and conversion rates.",
    "EDUCATION",
    "B.B.A. Digital Business, University of Dubai, 2022",
    "SELECTED PROJECTS",
    "- Automated Lead Nurturing Flow - HubSpot",
    "- CRM Data Cleanup and Segmentation Project",
    "CERTIFICATIONS",
    "HubSpot Marketing Software Certification",
])


def section_names(text: str) -> list[str]:
    """Detect sections and return only their canonical names."""
    return [section.name for section in detect_sections(text)]


def sections_by_name(text: str) -> dict:
    """Detect sections and index them by name (last one wins)."""
    return {section.name: section for section in detect_sections(text)}


# --- The whole CV -------------------------------------------------------------


def test_sections_are_detected_in_document_order():
    assert section_names(CLEANED_CV) == [
        "header",
        "summary",
        "skills",
        "experience",
        "education",
        "projects",
        "certifications",
    ]


def test_header_holds_the_name():
    assert "Fadi Salem" in sections_by_name(CLEANED_CV)["header"].text


def test_experience_holds_both_job_lines():
    experience = sections_by_name(CLEANED_CV)["experience"].text
    assert "CRM Specialist | LoopCommerce" in experience
    assert "Marketing Operations Coordinator | MarketNest" in experience


def test_a_heading_is_not_part_of_its_own_content():
    summary = sections_by_name(CLEANED_CV)["summary"]
    assert summary.heading == "PROFESSIONAL SUMMARY"
    assert "PROFESSIONAL SUMMARY" not in summary.text


# --- Known headings -----------------------------------------------------------


def test_heading_variants_are_recognized():
    for heading, expected in [
        ("Skills:", "skills"),
        ("## Experience", "experience"),
        ("Work Experience", "experience"),
        ("core skills", "skills"),
    ]:
        sections = detect_sections(f"{heading}\nPython and SQL")
        assert [section.name for section in sections] == [expected]
        assert sections[0].heading == heading


def test_repeated_headings_produce_two_sections():
    sections = detect_sections("PROJECTS\n- One.\nPROJECTS\n- Two.")
    assert [section.name for section in sections] == ["projects", "projects"]
    assert sections[0].text == "- One."
    assert sections[1].text == "- Two."


def test_volunteering_starts_its_own_section_after_certifications():
    text = f"{CLEANED_CV}\nVOLUNTEERING\n- Mentored students at a coding club."
    sections = sections_by_name(text)
    assert "volunteering" in sections
    assert "Mentored students" in sections["volunteering"].text
    assert "Mentored students" not in sections["certifications"].text


# --- Unknown headings ---------------------------------------------------------


def test_unknown_heading_starts_an_other_section():
    text = f"{CLEANED_CV}\nCOMMUNITY WORK\n- Organized a local meetup."
    sections, report = detect_sections_with_report(text)

    unknown = [section for section in sections if section.name == "other"]
    assert len(unknown) == 1
    assert unknown[0].heading == "COMMUNITY WORK"
    assert unknown[0].text == "- Organized a local meetup."
    assert "COMMUNITY WORK" in report["unknown_heading_candidates"]

    certifications = sections_by_name(text)["certifications"]
    assert "Organized a local meetup." not in certifications.text


def test_a_job_line_inside_experience_does_not_start_a_section():
    text = "EXPERIENCE\nSENIOR DATA ENGINEER | TABADUL\n- Built ingestion pipelines."
    sections = detect_sections(text)
    assert [section.name for section in sections] == ["experience"]
    assert "SENIOR DATA ENGINEER | TABADUL" in sections[0].text


def test_a_date_line_inside_experience_does_not_start_a_section():
    text = "EXPERIENCE\n2022 - PRESENT\n- Built ingestion pipelines."
    sections = detect_sections(text)
    assert [section.name for section in sections] == ["experience"]
    assert "2022 - PRESENT" in sections[0].text


def test_an_uppercase_line_followed_by_a_known_heading_does_not_start_a_section():
    text = "SUMMARY\nA short summary line.\nCOMMUNITY WORK\nEDUCATION\nBSc Marketing"
    sections, report = detect_sections_with_report(text)
    assert [section.name for section in sections] == ["summary", "education"]
    assert "COMMUNITY WORK" in sections[0].text
    assert report["unknown_heading_candidates"] == []


def test_an_uppercase_name_in_the_header_does_not_start_a_section():
    text = "FADI SALEM\nCRM Specialist\nSUMMARY\nA short summary line."
    sections = detect_sections(text)
    assert [section.name for section in sections] == ["header", "summary"]
    assert "FADI SALEM" in sections[0].text


def test_an_unknown_heading_on_the_last_line_does_not_start_a_section():
    text = "SUMMARY\nA short summary line.\nCOMMUNITY WORK"
    sections = detect_sections(text)
    assert [section.name for section in sections] == ["summary"]
    assert "COMMUNITY WORK" in sections[0].text


# --- Markdown lines -----------------------------------------------------------


def test_a_markdown_job_line_does_not_start_a_section():
    text = "EXPERIENCE\n### Machine Learning Engineer | Nova Analytics\n- Built models."
    sections, report = detect_sections_with_report(text)
    assert [section.name for section in sections] == ["experience"]
    assert report["unknown_heading_candidates"] == []


def test_markdown_name_and_job_lines_are_not_reported():
    text = (
        "# Fadi Salem\n"
        "CRM Specialist\n"
        "EXPERIENCE\n"
        "### CRM Specialist | LoopCommerce\n"
        "- Built onboarding journeys."
    )
    sections, report = detect_sections_with_report(text)
    assert [section.name for section in sections] == ["header", "experience"]
    assert report["unknown_heading_candidates"] == []


def test_a_markdown_heading_below_a_known_heading_is_reported():
    text = "EXPERIENCE\n- Built journeys.\n## Volunteer Highlights\n- Mentored students."
    sections, report = detect_sections_with_report(text)
    assert [section.name for section in sections] == ["experience"]
    assert report["unknown_heading_candidates"] == ["## Volunteer Highlights"]


# --- No known headings --------------------------------------------------------


def test_text_without_a_known_heading_is_one_body_section():
    text = "Fadi Salem\nCRM Specialist\n- Built onboarding journeys."
    sections, report = detect_sections_with_report(text)
    assert [section.name for section in sections] == ["body"]
    assert sections[0].text == text
    assert sections[0].heading == ""
    assert report["unknown_heading_candidates"] == []


def test_an_unknown_heading_without_a_known_one_stays_in_the_body():
    text = "FADI SALEM\nCOMMUNITY WORK\n- Organized a local meetup."
    assert section_names(text) == ["body"]


# --- Offsets and pages --------------------------------------------------------


def test_offsets_reproduce_the_input():
    for text in (
        CLEANED_CV,
        f"{CLEANED_CV}\nCOMMUNITY WORK\n- Organized a local meetup.",
        "no known headings here",
        f"EXPERIENCE\n- Built journeys.{PAGE_BREAK}EDUCATION\nBSc Marketing",
    ):
        sections = detect_sections(text)
        assert "".join(text[section.start : section.end] for section in sections) == text


def test_content_start_points_at_the_first_content_character():
    text = "SUMMARY\nA short summary line."
    section = detect_sections(text)[0]
    assert text[section.start : section.content_start] == "SUMMARY\n"
    assert text[section.content_start : section.end] == "A short summary line."


def test_a_section_spanning_a_page_break_lists_both_pages():
    text = f"EXPERIENCE\n- Built journeys.{PAGE_BREAK}- Created segments."
    section = detect_sections(text)[0]
    assert section.pages == [1, 2]
    assert section.text == "- Built journeys.\n- Created segments."


def test_a_section_after_a_page_break_lists_only_its_own_page():
    text = f"EXPERIENCE\n- Built journeys.{PAGE_BREAK}EDUCATION\nBSc Marketing"
    sections = sections_by_name(text)
    assert sections["experience"].pages == [1]
    assert sections["education"].pages == [2]


def test_a_single_page_cv_stays_on_page_one():
    assert all(section.pages == [1] for section in detect_sections(CLEANED_CV))


# --- Report -------------------------------------------------------------------


def test_a_complete_cv_misses_nothing_expected():
    _, report = detect_sections_with_report(CLEANED_CV)
    assert report["missing_expected"] == []
    assert report["empty_sections"] == []


def test_missing_expected_lists_the_sections_not_found():
    _, report = detect_sections_with_report("EXPERIENCE\n- Built journeys.")
    assert report["missing_expected"] == ["summary", "skills", "education"]


def test_empty_sections_are_reported():
    sections, report = detect_sections_with_report("SUMMARY\nEXPERIENCE\n- Built journeys.")
    assert [section.name for section in sections] == ["summary", "experience"]
    assert sections[0].text == ""
    assert report["empty_sections"] == ["summary"]


def test_report_has_the_expected_keys():
    _, report = detect_sections_with_report(CLEANED_CV)
    assert set(report) == {
        "unknown_heading_candidates",
        "missing_expected",
        "empty_sections",
    }
