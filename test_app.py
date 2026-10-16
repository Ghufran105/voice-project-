"""UI tests using Streamlit's headless AppTest. Claude and Google speech are mocked."""
import os

import pytest
from streamlit.testing.v1 import AppTest

import helpers as h

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def fake_result(code="print('hi')", expl="Prints hi."):
    return {"code": code, "explanation": expl, "raw": f"<code>{code}</code>", "user_message": "m"}


@pytest.fixture
def at(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "server-key")
    monkeypatch.delenv("MAX_REQUESTS_PER_SESSION", raising=False)
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    return app


def click_generate(app):
    next(b for b in app.button if "Generate" in b.label).click().run()


def test_app_loads_without_errors(at):
    assert not at.exception
    assert at.title[0].value.startswith("🎙️")
    assert at.session_state["history"] == []


def test_generate_python_flow(at, monkeypatch):
    calls = {}

    def fake(**kw):
        calls.update(kw)
        return fake_result()

    monkeypatch.setattr(h, "generate_code", fake)
    at.text_area(key="request_text").set_value("1 se 10 tak print karo").run()
    click_generate(at)
    assert not at.exception and not at.error
    assert at.code[0].value == "print('hi')"
    assert any("syntax check passed" in s.value for s in at.success)
    assert calls["target"] == "Python" and calls["api_key"] == "server-key"
    assert calls["request"] == "1 se 10 tak print karo"


def test_generate_cpp_with_bad_code_shows_error(at, monkeypatch):
    monkeypatch.setattr(h, "generate_code", lambda **kw: fake_result("int main(){ return 0 }"))
    at.radio[0].set_value("C++").run()
    at.text_area(key="request_text").set_value("empty program").run()
    click_generate(at)
    assert not at.exception
    assert at.code[0].language == "cpp"
    assert any("main.cpp" in e.value for e in at.error)


def test_codegen_error_is_shown_not_crashed(at, monkeypatch):
    def boom(**kw):
        raise h.CodeGenError("The API key was rejected.")

    monkeypatch.setattr(h, "generate_code", boom)
    at.text_area(key="request_text").set_value("something").run()
    click_generate(at)
    assert not at.exception
    assert any("rejected" in e.value for e in at.error)
    assert at.session_state["history"] == []


def test_empty_request_message(at):
    click_generate(at)  # real generate_code, empty text -> friendly error
    assert not at.exception
    assert any("say or type" in e.value for e in at.error)


def test_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    app.text_area(key="request_text").set_value("x").run()
    click_generate(app)
    assert any("No API key" in e.value for e in app.error)


def test_user_key_overrides_server_key(at, monkeypatch):
    seen = {}
    monkeypatch.setattr(h, "generate_code", lambda **kw: seen.update(kw) or fake_result())
    at.sidebar.text_input[-1].set_value("my-own-key").run()
    at.text_area(key="request_text").set_value("x").run()
    click_generate(at)
    assert seen["api_key"] == "my-own-key"


def test_session_limit_on_server_key(at, monkeypatch):
    monkeypatch.setattr(h, "generate_code", lambda **kw: fake_result())
    at.session_state["generation_count"] = 25
    at.text_area(key="request_text").set_value("x").run()
    click_generate(at)
    assert any("Session limit" in e.value for e in at.error)
    assert len(at.session_state["history"]) == 0


def test_followup_gets_history_and_earlier_results_listed(at, monkeypatch):
    seen = []
    monkeypatch.setattr(h, "generate_code", lambda **kw: seen.append(kw["history"][:]) or fake_result())
    for text in ("first", "second"):
        at.text_area(key="request_text").set_value(text).run()
        click_generate(at)
    assert len(seen[0]) == 0 and len(seen[1]) == 1
    assert len(at.session_state["history"]) == 2
    assert len(at.expander) == 1


def test_clear_history(at, monkeypatch):
    monkeypatch.setattr(h, "generate_code", lambda **kw: fake_result())
    at.text_area(key="request_text").set_value("x").run()
    click_generate(at)
    next(b for b in at.button if "Clear" in b.label).click().run()
    assert at.session_state["history"] == [] and not at.code
