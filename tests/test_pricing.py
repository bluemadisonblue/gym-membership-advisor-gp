"""
Tests for pricing.py — pure business logic, no Flask context needed.
"""
import pytest
from decimal import Decimal

import data as data_module
from pricing import (
    _to_decimal,
    money,
    format_currency,
    get_discount_category,
    get_discount_rate,
    calculate_pricing_for_selection,
    hydrate_pricing_result,
)


# ---------------------------------------------------------------------------
# _to_decimal
# ---------------------------------------------------------------------------

class TestToDecimal:
    def test_decimal_passthrough(self):
        d = Decimal("12.50")
        assert _to_decimal(d) == d

    def test_int(self):
        assert _to_decimal(10) == Decimal("10")

    def test_float(self):
        assert _to_decimal(9.99) == Decimal("9.99")

    def test_string_plain(self):
        assert _to_decimal("5.25") == Decimal("5.25")

    def test_string_with_pound(self):
        assert _to_decimal("£15.00") == Decimal("15.00")

    def test_string_with_comma(self):
        assert _to_decimal("1,000.00") == Decimal("1000.00")

    def test_none_returns_zero(self):
        assert _to_decimal(None) == Decimal("0.00")

    def test_bool_returns_zero(self):
        assert _to_decimal(True) == Decimal("0.00")
        assert _to_decimal(False) == Decimal("0.00")

    def test_empty_string_returns_zero(self):
        assert _to_decimal("") == Decimal("0.00")

    def test_invalid_string_returns_zero(self):
        assert _to_decimal("not-a-number") == Decimal("0.00")


# ---------------------------------------------------------------------------
# money (rounding)
# ---------------------------------------------------------------------------

class TestMoney:
    def test_rounds_half_up(self):
        # 1.005 should round to 1.01 with ROUND_HALF_UP
        assert money(Decimal("1.005")) == Decimal("1.01")

    def test_two_decimal_places(self):
        assert money(Decimal("10")) == Decimal("10.00")

    def test_float_input(self):
        result = money(9.99)
        assert result == Decimal("9.99")

    def test_string_input(self):
        assert money("£5.50") == Decimal("5.50")


# ---------------------------------------------------------------------------
# format_currency
# ---------------------------------------------------------------------------

class TestFormatCurrency:
    def test_formats_with_pound(self):
        assert format_currency(Decimal("10.50")) == "£10.50"

    def test_formats_zero(self):
        assert format_currency(0) == "£0.00"

    def test_formats_large(self):
        assert format_currency(Decimal("1000.00")) == "£1000.00"


# ---------------------------------------------------------------------------
# get_discount_category
# ---------------------------------------------------------------------------

class TestGetDiscountCategory:
    def test_young_adult_under_25(self):
        assert get_discount_category(20, False, False) == "student_young"

    def test_student_regardless_of_age(self):
        assert get_discount_category(25, True, False) == "student_young"

    def test_pensioner_over_66(self):
        assert get_discount_category(70, False, True) == "pensioner"

    def test_pensioner_takes_precedence_over_student(self):
        # Unlikely in practice but the code checks pensioner first
        assert get_discount_category(70, True, True) == "pensioner"

    def test_no_discount_for_normal_adult(self):
        assert get_discount_category(35, False, False) is None

    def test_boundary_exactly_25_no_student(self):
        # age < 25 is false at 25; not a student → no discount
        assert get_discount_category(25, False, False) is None

    def test_boundary_exactly_24(self):
        assert get_discount_category(24, False, False) == "student_young"

    def test_boundary_exactly_67(self):
        # age > 66 is true at 67
        assert get_discount_category(67, False, True) == "pensioner"

    def test_boundary_exactly_66(self):
        # 66 is NOT a pensioner (> 66 required)
        assert get_discount_category(66, False, False) is None


# ---------------------------------------------------------------------------
# get_discount_rate  (requires loaded DISCOUNTS cache)
# ---------------------------------------------------------------------------

class TestGetDiscountRate:
    def setup_method(self):
        """Ensure discount cache is populated with known test values."""
        data_module.DISCOUNTS = {
            "student_young": {"ugym": Decimal("0.20"), "power_zone": Decimal("0.15")},
            "pensioner": {"ugym": Decimal("0.15"), "power_zone": Decimal("0.20")},
        }

    def test_student_ugym(self):
        assert get_discount_rate("ugym", "student_young") == Decimal("0.20")

    def test_student_power_zone(self):
        assert get_discount_rate("power_zone", "student_young") == Decimal("0.15")

    def test_pensioner_ugym(self):
        assert get_discount_rate("ugym", "pensioner") == Decimal("0.15")

    def test_pensioner_power_zone(self):
        assert get_discount_rate("power_zone", "pensioner") == Decimal("0.20")

    def test_no_discount_category(self):
        assert get_discount_rate("ugym", None) == Decimal("0.00")

    def test_unknown_gym(self):
        assert get_discount_rate("unknown_gym", "student_young") == Decimal("0.00")


# ---------------------------------------------------------------------------
# calculate_pricing_for_selection  (requires loaded GYMS + DISCOUNTS cache)
# ---------------------------------------------------------------------------

class TestCalculatePricingForSelection:
    """Integration tests for the full pricing calculation."""

    @pytest.fixture(autouse=True)
    def _load_data(self, app):
        """Ensure module-level cache is populated for every test in this class."""
        with app.app_context():
            data_module.load_gyms_from_db()
            data_module.load_discounts_from_db()
            data_module.load_non_discounted_addons_from_db()

    def _signup(self, age=30, is_student=False, is_pensioner=False):
        return {"age": age, "is_student": is_student, "is_pensioner": is_pensioner}

    def _prefs(self, wants_gym=True, gym_band="off_peak",
                add_swim=False, add_classes=False, add_massage=False, add_physio=False):
        return {
            "wants_gym": wants_gym,
            "gym_band": gym_band,
            "add_swim": add_swim,
            "add_classes": add_classes,
            "add_massage": add_massage,
            "add_physio": add_physio,
        }

    def test_returns_both_gyms(self):
        result = calculate_pricing_for_selection(self._signup(), self._prefs())
        assert "ugym" in result["gyms"]
        assert "power_zone" in result["gyms"]

    def test_recommended_gym_is_cheaper(self):
        result = calculate_pricing_for_selection(self._signup(), self._prefs())
        rec = result["recommended_gym"]
        other = result["recommended_vs"]
        assert (result["gyms"][rec]["monthly_total_after_discount"]
                <= result["gyms"][other]["monthly_total_after_discount"])

    def test_off_peak_gym_only_no_discount(self):
        """30-year-old, off-peak gym only: uGym £21, Power Zone £19."""
        result = calculate_pricing_for_selection(self._signup(age=30), self._prefs(gym_band="off_peak"))
        assert result["gyms"]["ugym"]["monthly_total_after_discount"] == Decimal("21.00")
        assert result["gyms"]["power_zone"]["monthly_total_after_discount"] == Decimal("19.00")
        assert result["recommended_gym"] == "power_zone"

    def test_student_discount_applied(self):
        """Student (age 22): uGym off-peak £21 × 0.80 = £16.80."""
        result = calculate_pricing_for_selection(
            self._signup(age=22, is_student=True),
            self._prefs(gym_band="off_peak"),
        )
        ugym = result["gyms"]["ugym"]
        assert ugym["base_discount"] == money(Decimal("21.00") * Decimal("0.20"))
        assert ugym["base_final"] == Decimal("16.80")

    def test_pensioner_discount_applied(self):
        """Pensioner (age 70): Power Zone off-peak £19 × 0.80 = £15.20."""
        result = calculate_pricing_for_selection(
            self._signup(age=70, is_pensioner=True),
            self._prefs(gym_band="off_peak"),
        )
        pz = result["gyms"]["power_zone"]
        assert pz["base_discount"] == money(Decimal("19.00") * Decimal("0.20"))
        assert pz["base_final"] == Decimal("15.20")

    def test_massage_not_discounted(self):
        """Massage is never discounted even for students."""
        result = calculate_pricing_for_selection(
            self._signup(age=20, is_student=True),
            self._prefs(gym_band="off_peak", add_massage=True),
        )
        ugym_addons = {a["key"]: a for a in result["gyms"]["ugym"]["addons"]}
        massage = ugym_addons.get("massage")
        assert massage is not None
        assert massage["discount"] == Decimal("0.00")
        assert massage["discount_applied"] is False

    def test_physio_not_discounted(self):
        result = calculate_pricing_for_selection(
            self._signup(age=20, is_student=True),
            self._prefs(gym_band="off_peak", add_physio=True),
        )
        pz_addons = {a["key"]: a for a in result["gyms"]["power_zone"]["addons"]}
        physio = pz_addons.get("physio")
        assert physio is not None
        assert physio["discount"] == Decimal("0.00")

    def test_swim_discounted_for_student(self):
        """Swimming pool IS discounted for students."""
        result = calculate_pricing_for_selection(
            self._signup(age=20, is_student=True),
            self._prefs(gym_band="off_peak", add_swim=True),
        )
        ugym_addons = {a["key"]: a for a in result["gyms"]["ugym"]["addons"]}
        swim = ugym_addons.get("swim")
        assert swim is not None
        assert swim["discount"] > Decimal("0.00")
        assert swim["discount_applied"] is True

    def test_addons_only_no_gym(self):
        """User with no gym access, just swim add-on."""
        result = calculate_pricing_for_selection(
            self._signup(age=30),
            self._prefs(wants_gym=False, gym_band=None, add_swim=True),
        )
        ugym = result["gyms"]["ugym"]
        assert ugym["base_gym_price"] == Decimal("0.00")
        assert len(ugym["addons"]) == 1
        # Should use 'without_gym' pricing (higher price)
        swim_addon = ugym["addons"][0]
        assert swim_addon["key"] == "swim"
        assert swim_addon["price"] == Decimal("25.00")  # price_for_addons_only

    def test_savings_calculated_correctly(self):
        result = calculate_pricing_for_selection(self._signup(age=30), self._prefs(gym_band="off_peak"))
        rec = result["recommended_gym"]
        other = result["recommended_vs"]
        expected_savings = money(
            result["gyms"][other]["monthly_total_after_discount"]
            - result["gyms"][rec]["monthly_total_after_discount"]
        )
        assert result["recommended_savings_per_month"] == expected_savings

    def test_anytime_plan(self):
        result = calculate_pricing_for_selection(self._signup(age=30), self._prefs(gym_band="anytime"))
        assert result["gyms"]["ugym"]["monthly_total_after_discount"] == Decimal("30.00")
        assert result["gyms"]["power_zone"]["monthly_total_after_discount"] == Decimal("24.00")

    def test_super_off_peak_plan(self):
        result = calculate_pricing_for_selection(self._signup(age=30), self._prefs(gym_band="super_off_peak"))
        assert result["gyms"]["ugym"]["monthly_total_after_discount"] == Decimal("16.00")
        assert result["gyms"]["power_zone"]["monthly_total_after_discount"] == Decimal("13.00")

    def test_discount_category_stored_in_result(self):
        result = calculate_pricing_for_selection(self._signup(age=22, is_student=True), self._prefs())
        assert result["discount_category"] == "student_young"

    def test_no_discount_category_for_regular_adult(self):
        result = calculate_pricing_for_selection(self._signup(age=35), self._prefs())
        assert result["discount_category"] is None


# ---------------------------------------------------------------------------
# hydrate_pricing_result
# ---------------------------------------------------------------------------

class TestHydratePricingResult:
    def test_converts_string_decimals(self):
        raw = {
            "recommended_savings_per_month": "4.50",
            "gyms": {
                "ugym": {
                    "joining_fee": "10.00",
                    "base_gym_price": "21.00",
                    "base_discount": "0.00",
                    "base_final": "21.00",
                    "addons_total_before_discount": "0.00",
                    "addons_discount_total": "0.00",
                    "addons_total_after_discount": "0.00",
                    "monthly_total_before_discount": "21.00",
                    "discount_total": "0.00",
                    "monthly_total_after_discount": "21.00",
                    "addons": [],
                }
            },
        }
        result = hydrate_pricing_result(raw)
        assert isinstance(result["recommended_savings_per_month"], Decimal)
        assert isinstance(result["gyms"]["ugym"]["joining_fee"], Decimal)

    def test_empty_dict_passthrough(self):
        assert hydrate_pricing_result({}) == {}

    def test_none_passthrough(self):
        assert hydrate_pricing_result(None) is None
