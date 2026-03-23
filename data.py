from decimal import Decimal
from typing import Dict, Any, Optional

"""
Membership and pricing configuration for the gyms.

This module now loads data from the database but maintains backward compatibility
with the existing code by providing the same GYMS and DISCOUNTS structure.
"""

# Initialize as empty - will be populated from database
GYMS = {}
DISCOUNTS = {}
NON_DISCOUNTED_ADDONS = {"massage", "physio"}


def load_gyms_from_db():
    """
    Load gym data from the database and populate GYMS dictionary.
    Eager-loads membership_options to avoid N+1 queries.
    """
    from sqlalchemy.orm import joinedload
    from models import Gym

    global GYMS
    gyms = Gym.query.options(joinedload(Gym.membership_options)).all()

    GYMS = {}
    for gym in gyms:
        GYMS[gym.gym_key] = gym.to_dict()

    return GYMS


def load_discounts_from_db():
    """
    Load discount data from the database and populate DISCOUNTS dictionary.
    This function should be called after the app context is available.
    """
    from models import Discount

    global DISCOUNTS
    discounts = Discount.query.all()

    DISCOUNTS = {
        "student_young": {},
        "pensioner": {}
    }

    for discount in discounts:
        if discount.discount_type == 'student_Discount':
            DISCOUNTS["student_young"][discount.gym_key] = discount.rate
        elif discount.discount_type == 'pensioner_Discount':
            DISCOUNTS["pensioner"][discount.gym_key] = discount.rate

    return DISCOUNTS


def load_non_discounted_addons_from_db():
    """
    Load non-discounted addons from the database.
    This function should be called after the app context is available.
    """
    from models import MembershipOption

    global NON_DISCOUNTED_ADDONS

    # Query all addons that don't allow discounts
    non_discounted = MembershipOption.query.filter_by(
        option_type='addon',
        discount_allowed=False
    ).all()

    NON_DISCOUNTED_ADDONS = {option.option_key for option in non_discounted}

    return NON_DISCOUNTED_ADDONS


def invalidate_cache() -> None:
    """Clear cached data. Call when admin updates gyms, options, or discounts."""
    global GYMS, DISCOUNTS, NON_DISCOUNTED_ADDONS
    GYMS = {}
    DISCOUNTS = {}
    NON_DISCOUNTED_ADDONS = {"massage", "physio"}


def get_gym(gym_key: str) -> Optional[Dict[str, Any]]:
    """Return gym configuration by key."""
    if not GYMS:
        load_gyms_from_db()
    return GYMS.get(gym_key)


def list_gym_keys() -> list[str]:
    """Convenience helper for iterating all gyms."""
    if not GYMS:
        load_gyms_from_db()
    return list(GYMS.keys())

