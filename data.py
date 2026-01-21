from decimal import Decimal
from typing import Dict, Any, Optional

"""
Static membership and pricing configuration for the gyms.

This module is intentionally simple and uses only in-memory data structures
so it is easy to swap out with a database-backed model (e.g. SQLAlchemy) later.
"""


GYMS = {
    "ugym": {
        "key": "ugym",
        "name": "uGym",
        "joining_fee": Decimal("10.00"),
        "gym_plans": {
            "super_off_peak": {
                "label": "Super off-peak (10-12 & 2-4)",
                "price": Decimal("16.00"),
            },
            "off_peak": {
                "label": "Off-peak (12-2 & 8-11)",
                "price": Decimal("21.00"),
            },
            "anytime": {
                "label": "Anytime",
                "price": Decimal("30.00"),
            },
        },
        "addons": {
            "swim": {
                "label": "Swimming pool",
                "with_gym": Decimal("15.00"),
                "without_gym": Decimal("25.00"),
            },
            "classes": {
                "label": "Classes",
                "with_gym": Decimal("10.00"),
                "without_gym": Decimal("20.00"),
            },
            "massage": {
                "label": "Massage therapy",
                "with_gym": Decimal("25.00"),
                "without_gym": Decimal("30.00"),
            },
            "physio": {
                "label": "Physiotherapy",
                "with_gym": Decimal("20.00"),
                "without_gym": Decimal("25.00"),
            },
        },
    },
    "power_zone": {
        "key": "power_zone",
        "name": "Power Zone",
        "joining_fee": Decimal("30.00"),
        "gym_plans": {
            "super_off_peak": {
                "label": "Super off-peak",
                "price": Decimal("13.00"),
            },
            "off_peak": {
                "label": "Off-peak",
                "price": Decimal("19.00"),
            },
            "anytime": {
                "label": "Anytime",
                "price": Decimal("24.00"),
            },
        },
        "addons": {
            "swim": {
                "label": "Swimming pool",
                "with_gym": Decimal("12.50"),
                "without_gym": Decimal("20.00"),
            },
            "classes": {
                "label": "Classes",
                "with_gym": Decimal("0.00"),
                "without_gym": Decimal("20.00"),
            },
            "massage": {
                "label": "Massage therapy",
                "with_gym": Decimal("25.00"),
                "without_gym": Decimal("30.00"),
            },
            "physio": {
                "label": "Physiotherapy",
                "with_gym": Decimal("25.00"),
                "without_gym": Decimal("30.00"),
            },
        },
    },
}


# Discount percentages (as Decimal fractions; e.g. 0.20 = 20% off)
DISCOUNTS = {
    "student_young": {
        "ugym": Decimal("0.20"),
        "power_zone": Decimal("0.15"),
    },
    "pensioner": {
        "ugym": Decimal("0.15"),
        "power_zone": Decimal("0.20"),
    },
}


NON_DISCOUNTED_ADDONS = {"massage", "physio"}


def get_gym(gym_key: str) -> Optional[Dict[str, Any]]:
    """
    Return gym configuration by key.

    Args:
        gym_key: The gym key identifier ("ugym" or "power_zone")

    Returns:
        The gym configuration dictionary, or None if not found
    """
    return GYMS.get(gym_key)


def list_gym_keys() -> list[str]:
    """
    Convenience helper for iterating all gyms.

    Returns:
        A list of all available gym keys
    """
    return list(GYMS.keys())

