from google_auth_pc.ui.settings_screen import scale_label, stepper_state


def test_scale_labels():
    assert scale_label(0.9) == "%90"
    assert scale_label(1.0) == "Normal (100%)"
    assert scale_label(1.15) == "%115"
    assert scale_label(1.3) == "%130"


def test_stepper_state_bounds():
    assert stepper_state(0.9) == (False, True)
    assert stepper_state(1.0) == (True, True)
    assert stepper_state(1.15) == (True, True)
    assert stepper_state(1.3) == (True, False)
