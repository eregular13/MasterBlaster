from masterblaster_control.phase_tracker import list_phase_progress, phases_dashboard_markdown


def test_phase_tracker_lists_p0_through_p7():
    phases = list_phase_progress()

    assert len(phases) == 8
    assert phases[0].phase_id == "P0"
    assert phases[-1].phase_id == "P7"
    assert phases[0].percent == 100
    assert all(phase.percent == 100 for phase in phases)
    assert all(phase.status == "complete" for phase in phases)


def test_phase_dashboard_markdown_renders_table():
    dashboard = phases_dashboard_markdown()

    assert dashboard.startswith("# MasterBlaster Phase Roadmap")
    assert "| P0 | Simulator perfection |" in dashboard
    assert "| P7 | Visionary extension |" in dashboard