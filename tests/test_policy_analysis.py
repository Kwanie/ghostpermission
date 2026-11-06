import pytest
from core.policy_analysis import analyze_policy, split_sentences
from research_agent import verify_quote_in_policy, find_exact_policy_quotes

FILLER = " ".join(f"This is neutral filler sentence number {i} about how the service works." for i in range(12))


def report(sentence_block):
    return analyze_policy(sentence_block + "\n" + FILLER)


def topics(r, kind=None):
    return [(c["topic"], c["kind"], c["risk_flag"]) for c in r["clauses"] if kind in (None, c["kind"])]


def test_do_not_sell_is_reassuring_not_a_warning():
    r = report("We do not sell your personal data to anyone, ever.")
    assert ("Selling or renting your data", "reassuring", "Low") in topics(r)
    assert not [t for t in topics(r) if t[1] == "concern"]
    assert "No concerning clause" in r["headline"]


def test_word_forms_are_found():
    r = report("We are selling your personal data to advertising partners every month.")
    assert ("Selling or renting your data", "concern", "High") in topics(r)


def test_long_sentences_are_not_silently_dropped():
    long = ("We may collect, use, store and process information about you, including your device identifiers, usage patterns, "
            "and approximate and precise location, and we may sell that information to third parties for marketing, analytics, "
            "research, fraud prevention, product development and any other lawful business purposes that we consider appropriate from time to time.")
    assert len(long) > 350
    assert ("Selling or renting your data", "concern", "High") in topics(report(long))


def test_the_most_serious_clause_is_kept_even_when_it_comes_last():
    mild = " ".join(f"We may share data with partner {i} for marketing purposes." for i in range(8))
    r = analyze_policy(mild + "\nWe sell all your data to data brokers.\n" + FILLER)
    assert r["clauses"][0]["risk_flag"] == "High"


def test_background_location_is_higher_risk_than_plain_location():
    plain = topics(report("We collect your location when you use the app."))
    background = topics(report("We collect your precise location in the background."))
    assert ("Collecting your location", "concern", "Medium") in plain
    assert ("Collecting your location", "concern", "High") in background


def test_deleting_rights_and_their_negation():
    assert ("Deleting your data", "reassuring", "Low") in topics(report("You can delete your account and data at any time."))
    assert ("Deleting your data", "concern", "Medium") in topics(report("We cannot delete data that is already backed up."))


def test_every_shown_quote_really_appears_in_the_document():
    text = "Intro line.\nWe sell your data to partners.\nYou may opt out at any time in settings.\n" + FILLER
    r = analyze_policy(text)
    assert r["clauses"] and all(verify_quote_in_policy(c["original_text"], text) for c in r["clauses"])


def test_too_short_text_gives_no_verdict_at_all():
    r = analyze_policy("We sell your data.")
    assert r["status"] == "too_short" and r["clauses"] == [] and "not enough" in r["headline"]


def test_coverage_and_limits_are_always_reported():
    r = report("We collect your location.")
    c = r["coverage"]
    assert c["characters_read"] > 400 and c["sentences_read"] >= 13 and c["topics_checked"] >= 10 and c["truncated"] is False
    assert len(r["limitations"]) >= 2


def test_a_truncated_document_says_so():
    assert "Only the first part" in analyze_policy(FILLER + " We sell your data.", truncated=True)["headline"]


def test_the_report_never_calls_a_policy_safe_or_standard():
    for text in (FILLER, FILLER + "\nWe do not sell your data."):
        h = analyze_policy(text)["headline"].lower()
        assert "safe" not in h and "standard" not in h and "not a guarantee" in h


def test_each_topic_is_capped_so_one_topic_cannot_flood_the_list():
    many = "\n".join(f"We share your information with company number {i} for advertising." for i in range(10))
    r = analyze_policy(many + "\n" + FILLER)
    assert sum(1 for c in r["clauses"] if c["topic"] == "Sharing with other companies") <= 2


def test_sentence_splitting_keeps_line_breaks_as_boundaries():
    assert split_sentences("Heading One\nWe collect data about you. We keep it safe.\n- A bullet point that is long enough") == \
        ["We collect data about you.", "We keep it safe.", "A bullet point that is long enough"]


def test_the_old_helper_still_works_with_short_text_and_old_return_shape():
    quotes = find_exact_policy_quotes("We welcome you. We may sell your data to third party marketing affiliates. We also track location for ad targeting purposes.")
    assert len(quotes) >= 2 and {"topic", "original_text", "risk_flag"} <= set(quotes[0])
    assert "Sell" in [q["topic"] for q in quotes]


# ---- Phase 4 fixes found by stress-testing with tricky real-world sentences ----
_PAD = ("This policy explains how the company handles information about people who use its services across web and mobile. "
        "It applies to all of our products and to visitors of our websites in every country where we operate. ") * 2

def _about(sentence):
    report = analyze_policy(_PAD + sentence, min_chars=0)
    return [(c["topic"], c["kind"], c["risk_flag"]) for c in report["clauses"] if sentence[:20] in c["original_text"]]

def test_a_denial_that_names_third_parties_is_not_also_a_sharing_concern():
    assert _about("We do not sell your personal information to third parties.") == [
        ("Selling or renting your data", "reassuring", "Low")]

def test_a_harmless_sentence_with_share_and_you_is_not_flagged():
    assert _about("Share this page with your friends if you like it.") == []

def test_a_conditional_denial_is_not_reassuring():
    result = _about("We do not sell your data unless you give us permission or the law changes.")
    assert result == [("Selling or renting your data", "concern", "Medium")]
    report = analyze_policy(_PAD + "We do not sell your data unless you give us permission.", min_chars=0)
    assert any("conditions or exceptions" in c["summary"] for c in report["clauses"])

def test_not_hesitate_to_sell_is_a_high_concern_not_a_promise():
    assert _about("We will not hesitate to sell your information to partners.") == [
        ("Selling or renting your data", "concern", "High")]

def test_nothing_prevents_us_from_selling_is_a_high_concern():
    assert _about("Nothing in this policy prevents us from selling your personal information.") == [
        ("Selling or renting your data", "concern", "High")]

def test_a_denial_with_an_exception_stays_a_concern():
    assert ("Sharing with other companies", "concern", "Medium") in _about(
        "We never share your location with anyone except our advertising partners.")

def test_a_plain_denial_of_sharing_is_still_reassuring():
    assert _about("We do not share your information with advertisers.") == [
        ("Sharing with other companies", "reassuring", "Low")]

def test_wont_sell_is_understood_as_a_denial():
    assert _about("We won't sell your data.") == [("Selling or renting your data", "reassuring", "Low")]
