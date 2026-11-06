import zipfile

import check_before_sharing as guard
import make_clean_zip as mz


def fake_groq_key():
    return "gsk_" + "A1b2C3d4E5" * 3            # built at run time, so this file itself holds no key-shaped text


def fake_openai_key():
    return "sk-proj-" + "Zy9x8W7v6U" * 3


def make_project(tmp_path, code="print('hello')\n"):
    root = tmp_path / "proj"
    (root / ".venv" / "lib").mkdir(parents=True)
    (root / "core").mkdir()
    (root / "app.py").write_text(code, encoding="utf-8")
    (root / "core" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    (root / ".env").write_text(f"GROQ_API_KEY={fake_groq_key()}\n", encoding="utf-8")
    (root / ".env.example").write_text("GROQ_API_KEY=\n", encoding="utf-8")
    (root / ".venv" / "lib" / "big.py").write_text("y = 2\n", encoding="utf-8")
    return root


def test_env_files_are_found_but_the_example_is_not(tmp_path):
    root = make_project(tmp_path)
    assert guard.find_env_files(root) == [".env"]

def test_keys_inside_code_are_found(tmp_path):
    root = make_project(tmp_path, code=f"KEY = '{fake_groq_key()}'\nOTHER = '{fake_openai_key()}'\n")
    kinds = {kind for _, kind in guard.find_keys_in_code(root)}
    assert kinds == {"a Groq key", "an OpenAI key"}

def test_the_env_file_itself_is_not_reported_as_a_code_problem(tmp_path):
    assert guard.find_keys_in_code(make_project(tmp_path)) == []

def test_ordinary_hyphenated_words_are_not_mistaken_for_keys(tmp_path):
    code = "name = 'risk-based-analysis-of-privacy-policies-and-terms'\ntask = 'task-management-dashboard-version-two'\n"
    assert guard.find_keys_in_code(make_project(tmp_path, code=code)) == []

def test_main_reports_success_and_failure(tmp_path):
    assert guard.main(make_project(tmp_path)) == 0
    assert guard.main(make_project(tmp_path / "other", code=f"K='{fake_groq_key()}'")) == 1

def test_the_clean_zip_leaves_out_env_and_venv(tmp_path):
    root = make_project(tmp_path)
    out = mz.build_zip(root, tmp_path / "out" / "share.zip")
    names = zipfile.ZipFile(out).namelist()
    assert "proj/app.py" in names and "proj/core/thing.py" in names and "proj/.env.example" in names
    assert not any(name.endswith("/.env") for name in names)
    assert not any("/.venv/" in name for name in names)

def test_the_zip_is_refused_when_a_key_is_inside_the_code(tmp_path):
    root = make_project(tmp_path, code=f"KEY = '{fake_groq_key()}'\n")
    try:
        mz.build_zip(root, tmp_path / "out" / "share.zip")
    except RuntimeError as problem:
        assert "app.py" in str(problem) and fake_groq_key() not in str(problem)
    else:
        raise AssertionError("the zip should have been refused")
    assert not (tmp_path / "out" / "share.zip").exists()
