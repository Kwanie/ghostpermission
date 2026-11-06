import check_setup

SECRET = "gsk_THISISAFAKEKEYFORTESTING123456"

def test_setup_check_never_prints_the_key(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", SECRET)
    check_setup.PROBLEMS.clear()
    check_setup.check_env_file()
    printed = capsys.readouterr().out
    assert SECRET not in printed and "GROQ_API_KEY is set" in printed

def test_setup_check_reports_a_badly_pasted_key(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", '"' + SECRET + '"')
    check_setup.PROBLEMS.clear()
    check_setup.check_env_file()
    assert "quote marks" in capsys.readouterr().out

def test_online_check_explains_a_rejected_key(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", SECRET)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(check_setup, "ask_provider", lambda url, headers: 401)
    check_setup.PROBLEMS.clear()
    check_setup.check_online()
    assert "REJECTED" in capsys.readouterr().out

def test_online_check_handles_no_internet(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", SECRET)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(check_setup, "ask_provider", lambda url, headers: None)
    check_setup.PROBLEMS.clear()
    check_setup.check_online()
    assert "could not reach the internet" in capsys.readouterr().out

def test_ai_test_reports_success_with_a_fake_model(monkeypatch, capsys, fake_llm):
    monkeypatch.setattr("agents.shared_llm.get_llm", lambda: fake_llm(['{"ok": true}']))
    check_setup.PROBLEMS.clear()
    check_setup.check_ai_answer()
    assert "The model answered" in capsys.readouterr().out and check_setup.PROBLEMS == []

def test_ai_test_explains_a_bad_model_answer(monkeypatch, capsys, fake_llm):
    monkeypatch.setattr("agents.shared_llm.get_llm", lambda: fake_llm([RuntimeError("model not found")] * 2))
    check_setup.PROBLEMS.clear()
    check_setup.check_ai_answer()
    assert "GHOST_LLM_MODEL" in capsys.readouterr().out
