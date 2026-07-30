import math

import pytest

from knobe.parsing import expected_rating_from_logprobs, parse_rating, parse_with_fallback


class TestParseRating:
    @pytest.mark.parametrize(
        "raw,expected_value",
        [
            ("7", 7),
            (" 7.", 7),
            ("10", 10),
            ("rating: 3 out of 10", 3),
            ("0", 0),
            ("The answer is 9.", 9),
        ],
    )
    def test_parses_first_valid_integer(self, raw, expected_value):
        value, ok, raw_out = parse_rating(raw)
        assert value == expected_value
        assert ok is True
        assert raw_out == raw

    def test_unparseable_word_returns_none(self):
        value, ok, raw_out = parse_rating("ten")
        assert value is None
        assert ok is False
        assert raw_out == "ten"

    def test_empty_string_returns_none(self):
        value, ok, raw_out = parse_rating("")
        assert value is None
        assert ok is False
        assert raw_out == ""

    def test_never_coerces_unparseable_to_a_number(self):
        """An empty/unparseable response must never silently become 0 or
        any other numeric default."""
        value, ok, _ = parse_rating("I cannot answer this.")
        assert value is None
        assert ok is False

    def test_out_of_range_number_not_matched_as_whole(self):
        # "11" itself isn't a valid single-digit-or-10 token at a word
        # boundary, so this should not parse as 1 or 11.
        value, ok, _ = parse_rating("11")
        assert ok is False
        assert value is None


class TestExpectedRatingFromLogprobs:
    def test_uniform_distribution_ev_is_midpoint(self):
        logprobs = [math.log(1 / 11)] * 11
        ev = expected_rating_from_logprobs(logprobs)
        assert ev == pytest.approx(5.0, abs=1e-6)

    def test_point_mass_on_ten(self):
        # overwhelming probability on "10" relative to the rest
        logprobs = [-50.0] * 10 + [0.0]
        ev = expected_rating_from_logprobs(logprobs)
        assert ev == pytest.approx(10.0, abs=1e-4)

    def test_hand_computed_fixture(self):
        # Unnormalized weights proportional to [1, 3] on tokens "0" and "1",
        # zero elsewhere (as -inf log prob) -- hand-computed EV = 3/4 = 0.75
        neg_inf = float("-inf")
        logprobs = [math.log(1.0), math.log(3.0)] + [neg_inf] * 9
        ev = expected_rating_from_logprobs(logprobs)
        assert ev == pytest.approx(0.75, abs=1e-6)

    def test_requires_length_11(self):
        with pytest.raises(ValueError):
            expected_rating_from_logprobs([0.0] * 10)


class TestParseWithFallback:
    def test_regex_success_does_not_use_logprobs(self):
        result = parse_with_fallback("7", logprobs_0_10=None, threshold_ok=True)
        assert result.parsed_rating == 7
        assert result.parse_ok is True
        assert result.parse_method == "regex"

    def test_falls_back_to_logits_when_regex_fails_and_fallback_enabled(self):
        logprobs = [math.log(1 / 11)] * 11
        result = parse_with_fallback("no idea", logprobs_0_10=logprobs, threshold_ok=False)
        assert result.parse_method == "logit_fallback"
        assert result.parsed_rating == pytest.approx(5.0, abs=1e-6)
        assert result.parse_ok is True

    def test_no_fallback_when_threshold_ok_true(self):
        """threshold_ok=True means the checkpoint's regex parse rate is
        healthy (>=95% per spec §4.4) -- logit fallback should not kick in
        even if logprobs are available and this particular raw failed."""
        logprobs = [math.log(1 / 11)] * 11
        result = parse_with_fallback("no idea", logprobs_0_10=logprobs, threshold_ok=True)
        assert result.parse_method == "regex"
        assert result.parsed_rating is None
        assert result.parse_ok is False

    def test_no_fallback_without_logprobs(self):
        result = parse_with_fallback("no idea", logprobs_0_10=None, threshold_ok=False)
        assert result.parse_method == "regex"
        assert result.parsed_rating is None
        assert result.parse_ok is False
