from masterblaster_control.p8_acceptance_gate import evaluate_p8_gate, p8_gate_markdown


def test_p8_gate_passed_at_100_percent():
    gate = evaluate_p8_gate()
    assert gate.percent == 100
    assert gate.passed is True
    assert "PASSED" in p8_gate_markdown()