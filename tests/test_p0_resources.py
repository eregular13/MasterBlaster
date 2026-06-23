import pytest

from masterblaster_control.p0_resources import (
    UnknownResourceError,
    list_resources,
    read_resource,
    resource_summary_markdown,
)


def test_all_p0_resources_are_non_executing_and_versioned():
    resources = list_resources()

    assert len(resources) >= 5
    assert all(resource.non_executing is True for resource in resources)
    assert all(resource.version for resource in resources)
    assert all(resource.uri.startswith("p0://") for resource in resources)
    assert all("non-executing" in resource.body.lower() for resource in resources)


def test_resource_categories_filter_deterministically():
    planning = list_resources(category="planning")
    reporting = list_resources(category="reporting")
    governance = list_resources(category="governance")

    assert [resource.uri for resource in planning] == [
        "p0://planning/engagement-template",
        "p0://planning/rules-of-engagement-template",
        "p0://planning/workflow-template",
    ]
    assert [resource.uri for resource in reporting] == ["p0://reporting/report-draft-outline"]
    assert [resource.uri for resource in governance] == ["p0://governance/acceptance-checklist"]


def test_unknown_resource_uri_fails_closed():
    with pytest.raises(UnknownResourceError):
        read_resource("p0://planning/live-execution")


def test_report_resource_contains_required_draft_disclaimer():
    report = read_resource("p0://reporting/report-draft-outline")

    assert "not a compliance attestation" in report.body.lower()
    assert "certification" in report.body.lower()
    assert "proof of security" in report.body.lower()


def test_resource_summary_is_stable_markdown_catalog():
    summary = resource_summary_markdown()

    assert summary.startswith("# Non-Executing P0 Resources")
    assert "p0://planning/engagement-template" in summary
    assert "p0://governance/acceptance-checklist" in summary
    assert "Non-executing: `True`" in summary
