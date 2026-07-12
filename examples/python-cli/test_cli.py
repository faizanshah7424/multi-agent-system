from cli import run_cli


def test_cli_default_message():
    assert run_cli([]) == "Welcome to the CodeOrbit Python CLI!"


def test_cli_custom_message():
    assert run_cli(["--message", "Hello Orbit"]) == "Hello Orbit"
