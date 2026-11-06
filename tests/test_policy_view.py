from streamlit.testing.v1 import AppTest
import core.policy_view as view

FILLER = " ".join(f"This is neutral filler sentence number {i} about how the service works." for i in range(12))
POLICY = "We sell your personal data to advertising partners.\n" + FILLER


def harness():
    import streamlit as st
    from core.policy_view import render_policy_box
    if "payload" not in st.session_state:
        st.session_state.payload = {"app_name": "X", "privacy_policy_url": "https://example.com/privacy"}
    render_policy_box(st.session_state.payload)


def all_text(at):
    return " | ".join([m.value for m in at.markdown] + [c.value for c in at.caption] + [w.value for w in at.warning])


def test_a_link_without_text_offers_to_read_it_and_does_not_claim_there_is_no_policy():
    at = AppTest.from_function(harness).run()
    assert not at.exception
    assert any(b.label == "Read this policy" for b in at.button)
    assert "no privacy policy" not in all_text(at).lower()


def test_reading_the_policy_shows_real_quotes_and_an_honest_headline(monkeypatch):
    monkeypatch.setattr(view, "fetch_policy_text", lambda url: {"ok": True, "text": POLICY, "final_url": url, "truncated": False, "error": ""})
    monkeypatch.setattr(view, "get_llm", lambda: None)
    at = AppTest.from_function(harness).run()
    next(b for b in at.button if b.label == "Read this policy").click().run()
    assert not at.exception
    text = all_text(at)
    assert "points worth reading closely" in text and "Selling or renting your data" in text
    assert any(e.label == "Exact words from the document" for e in at.expander)
    assert "safe" not in text.lower().replace("not a guarantee", "")


def test_a_failed_fetch_explains_and_points_to_pasting(monkeypatch):
    monkeypatch.setattr(view, "fetch_policy_text", lambda url: {"ok": False, "text": "", "final_url": url, "truncated": False, "error": "The website took too long to answer."})
    at = AppTest.from_function(harness).run()
    next(b for b in at.button if b.label == "Read this policy").click().run()
    assert "took too long" in all_text(at) and "paste" in all_text(at).lower()


def test_no_link_means_an_honest_empty_state_and_the_paste_box():
    def no_link():
        import streamlit as st
        from core.policy_view import render_policy_box
        if "payload" not in st.session_state:
            st.session_state.payload = {"app_name": "X"}
        render_policy_box(st.session_state.payload)
    at = AppTest.from_function(no_link).run()
    assert "does not include a privacy policy link" in all_text(at)
    assert any(e.label == "Paste a privacy policy or terms text instead" for e in at.expander)


def test_pasted_text_is_analysed_and_can_be_cleared(monkeypatch):
    monkeypatch.setattr(view, "get_llm", lambda: None)
    at = AppTest.from_function(harness).run()
    at.text_area[0].set_value(POLICY).run()
    next(b for b in at.button if b.label == "Check this text").click().run()
    assert "Source: pasted by you" in all_text(at)
    next(b for b in at.button if b.label == "Use a different policy").click().run()
    assert any(b.label == "Read this policy" for b in at.button)
