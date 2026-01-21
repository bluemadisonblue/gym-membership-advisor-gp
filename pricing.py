from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from data import GYMS, DISCOUNTS, NON_DISCOUNTED_ADDONS


def money(value: Decimal) -> Decimal:
    """
    Normalize a Decimal monetary value to 2 decimal places.

    Args:
        value: The decimal value to normalize

    Returns:
        The value rounded to 2 decimal places using half-up rounding
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_currency(value: Decimal) -> str:
    """
    Format a Decimal as a GBP currency string.

    Args:
        value: The decimal value to format

    Returns:
        A formatted currency string (e.g., "£10.50")
    """
    return f"£{money(value):.2f}"


def get_discount_category(age: int, is_student: bool, is_pensioner_flag: bool) -> Optional[str]:
    """
    Determine which discount category applies.

    Args:
        age: The user's age
        is_student: Whether the user is a student
        is_pensioner_flag: Whether the user is a pensioner (age > 66)

    Returns:
        The discount category string ("pensioner", "student_young", or None)
        Note: Pensioner takes precedence over student/young adult.
        Students and young adults (age < 25) use the same category.
    """
    if is_pensioner_flag:
        return "pensioner"

    if is_student or age < 25:
        return "student_young"

    return None


def get_discount_rate(gym_key: str, discount_category: Optional[str]) -> Decimal:
    """
    Return the discount rate (0-1) for the given gym and category.

    Args:
        gym_key: The gym key identifier ("ugym" or "power_zone")
        discount_category: The discount category string or None

    Returns:
        The discount rate as a Decimal (0.00 to 1.00)
    """
    if not discount_category:
        return Decimal("0.00")

    gym_rates = DISCOUNTS.get(discount_category, {})
    return gym_rates.get(gym_key, Decimal("0.00"))


def calculate_pricing_for_selection(signup: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate pricing breakdown for each gym based on the user's signup info and preferences.

    Args:
        signup: Dictionary containing user signup data (age, is_student, is_pensioner, etc.)
        preferences: Dictionary containing user preferences (wants_gym, gym_band, addons, etc.)

    Returns:
        A dictionary containing:
        - "gyms": Dictionary with pricing breakdown for each gym
        - "recommended_gym": The gym key with the lowest monthly total
        - "discount_category": The applied discount category
        - "recommended_vs": The other gym key for comparison
        - "recommended_savings_per_month": Monthly savings compared to the other gym

    Raises:
        ValueError: If gym_band is required but not provided, or if gym_band is invalid
    """
    age = signup.get("age") or 0
    is_student = bool(signup.get("is_student"))
    is_pensioner_flag = bool(signup.get("is_pensioner"))

    wants_gym = bool(preferences.get("wants_gym"))
    gym_band = preferences.get("gym_band")

    discount_category = get_discount_category(age, is_student, is_pensioner_flag)

    gyms_result: Dict[str, Any] = {}

    for gym_key, gym_cfg in GYMS.items():
        joining_fee = gym_cfg["joining_fee"]
        discount_rate = get_discount_rate(gym_key, discount_category)

        base_gym_price = Decimal("0.00")
        gym_plan_label = None
        if wants_gym:
            if not gym_band:
                # Defensive: should be validated earlier
                raise ValueError("Gym band is required when user wants a gym membership.")
            plan_cfg = gym_cfg["gym_plans"].get(gym_band)
            if not plan_cfg:
                raise ValueError(f"Invalid gym band '{gym_band}' for gym '{gym_key}'.")
            base_gym_price = plan_cfg["price"]
            gym_plan_label = plan_cfg["label"]

        addons = []

        def maybe_add_addon(addon_key: str, selected: bool):
            if not selected:
                return
            addon_cfg = gym_cfg["addons"][addon_key]
            label = addon_cfg["label"]
            context_key = "with_gym" if wants_gym else "without_gym"
            price = addon_cfg[context_key]

            # Massage and physio are never discounted
            discount_applicable = addon_key not in NON_DISCOUNTED_ADDONS
            discount_amount = Decimal("0.00")
            if discount_applicable and discount_rate > 0:
                discount_amount = money(price * discount_rate)

            final_price = money(price - discount_amount)

            addons.append(
                {
                    "key": addon_key,
                    "label": label,
                    "context": "with gym membership" if wants_gym else "without gym membership",
                    "price": price,
                    "discount": discount_amount,
                    "final_price": final_price,
                    "discount_applied": discount_applicable and discount_rate > 0,
                }
            )

        maybe_add_addon("swim", bool(preferences.get("add_swim")))
        maybe_add_addon("classes", bool(preferences.get("add_classes")))
        maybe_add_addon("massage", bool(preferences.get("add_massage")))
        maybe_add_addon("physio", bool(preferences.get("add_physio")))

        addons_total_before_discount = sum((a["price"] for a in addons), Decimal("0.00"))
        addons_discount_total = sum((a["discount"] for a in addons), Decimal("0.00"))
        addons_total_after_discount = sum((a["final_price"] for a in addons), Decimal("0.00"))

        # Gym base price discount (if applicable)
        base_discount = Decimal("0.00")
        if wants_gym and discount_rate > 0:
            base_discount = money(base_gym_price * discount_rate)

        base_final = money(base_gym_price - base_discount)

        monthly_before_discount = money(base_gym_price + addons_total_before_discount)
        total_discount = money(base_discount + addons_discount_total)
        monthly_after_discount = money(base_final + addons_total_after_discount)

        gyms_result[gym_key] = {
            "gym_key": gym_key,
            "gym_name": gym_cfg["name"],
            "joining_fee": joining_fee,
            "gym_band": gym_band if wants_gym else None,
            "gym_plan_label": gym_plan_label,
            "wants_gym": wants_gym,
            "base_gym_price": base_gym_price,
            "base_discount": base_discount,
            "base_final": base_final,
            "addons": addons,
            "addons_total_before_discount": addons_total_before_discount,
            "addons_discount_total": addons_discount_total,
            "addons_total_after_discount": addons_total_after_discount,
            "monthly_total_before_discount": monthly_before_discount,
            "discount_total": total_discount,
            "monthly_total_after_discount": monthly_after_discount,
        }

    # Recommendation: choose the gym with the cheapest monthly_total_after_discount
    recommended_key = min(
        gyms_result.keys(),
        key=lambda k: gyms_result[k]["monthly_total_after_discount"],
    )

    other_keys = [k for k in gyms_result.keys() if k != recommended_key]
    other_key = other_keys[0] if other_keys else recommended_key
    savings = money(gyms_result[other_key]["monthly_total_after_discount"] - gyms_result[recommended_key]["monthly_total_after_discount"])
    if savings < 0:
        savings = Decimal("0.00")

    return {
        "gyms": gyms_result,
        "recommended_gym": recommended_key,
        "discount_category": discount_category,
        "recommended_vs": other_key,
        "recommended_savings_per_month": savings,
    }

