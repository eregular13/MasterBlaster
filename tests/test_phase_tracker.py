from masterblaster_control.phase_tracker import list_phase_progress, phases_dashboard_markdown


def test_phase_tracker_lists_p0_through_p7():
    phases = list_phase_progress()

    assert len(phases) == 10
    assert phases[0].phase_id == "P0"
    assert phases[-1].phase_id == "P9"
    assert phases[0].percent == 100
    assert phases[7].phase_id == "P7"
    assert phases[7].status == "complete"
    assert phases[8].phase_id == "P8"
    assert phases[8].status == "in_progress"
    assert phases[9].phase_id == "P9"
    assert phases[9].status == "not_started"


def test_phase_dashboard_markdown_renders_table():
    dashboard = phases_dashboard_markdown()

    assert dashboard.startswith("# MasterBlaster Phase Roadmap")
    assert "| P0 | Simulator perfection |" in dashboard
    assert "| P7 | Visionary extension |" in dashboard
    assert "| P8 | Enterprise horizon |" in dashboard
    assert "| P9 | Governed live adapters |" in dashboard