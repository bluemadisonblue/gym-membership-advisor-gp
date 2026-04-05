"""
Shared database seed logic for gyms, membership options, and discounts.
Used by app.py and init_db.py.
"""

from decimal import Decimal

from models import db, Gym, MembershipOption, Discount


def seed_gyms(force: bool = False) -> None:
    """Seed gym records. Skip if gyms exist unless force=True."""
    if not force and Gym.query.first():
        return
    db.session.add_all([
        Gym(gym_key="ugym", gym_name="uGym", joining_fee=Decimal("10.00")),
        Gym(gym_key="power_zone", gym_name="Power Zone", joining_fee=Decimal("30.00")),
        Gym(gym_key="pending", gym_name="Account only (no plan yet)", joining_fee=Decimal("0.00")),
    ])
    db.session.commit()


def seed_membership_options() -> None:
    """Seed membership options for all gyms."""
    ugym_opts = [
        MembershipOption(gym_key="ugym", option_type="gym_plan", option_key="super_off_peak",
                        label="Super off-peak (10-12 & 2-4)", price=Decimal("16.00"), discount_allowed=True),
        MembershipOption(gym_key="ugym", option_type="gym_plan", option_key="off_peak",
                        label="Off-peak (12-2 & 8-11)", price=Decimal("21.00"), discount_allowed=True),
        MembershipOption(gym_key="ugym", option_type="gym_plan", option_key="anytime",
                        label="Anytime", price=Decimal("30.00"), discount_allowed=True),
        MembershipOption(gym_key="ugym", option_type="addon", option_key="swim", label="Swimming pool",
                        price_with_full_gym_access=Decimal("15.00"), price_for_addons_only=Decimal("25.00"), discount_allowed=True),
        MembershipOption(gym_key="ugym", option_type="addon", option_key="classes", label="Classes",
                        price_with_full_gym_access=Decimal("10.00"), price_for_addons_only=Decimal("20.00"), discount_allowed=True),
        MembershipOption(gym_key="ugym", option_type="addon", option_key="massage", label="Massage therapy",
                        price_with_full_gym_access=Decimal("25.00"), price_for_addons_only=Decimal("30.00"), discount_allowed=False),
        MembershipOption(gym_key="ugym", option_type="addon", option_key="physio", label="Physiotherapy",
                        price_with_full_gym_access=Decimal("20.00"), price_for_addons_only=Decimal("25.00"), discount_allowed=False),
    ]
    power_opts = [
        MembershipOption(gym_key="power_zone", option_type="gym_plan", option_key="super_off_peak",
                        label="Super off-peak", price=Decimal("13.00"), discount_allowed=True),
        MembershipOption(gym_key="power_zone", option_type="gym_plan", option_key="off_peak",
                        label="Off-peak", price=Decimal("19.00"), discount_allowed=True),
        MembershipOption(gym_key="power_zone", option_type="gym_plan", option_key="anytime",
                        label="Anytime", price=Decimal("24.00"), discount_allowed=True),
        MembershipOption(gym_key="power_zone", option_type="addon", option_key="swim", label="Swimming pool",
                        price_with_full_gym_access=Decimal("12.50"), price_for_addons_only=Decimal("20.00"), discount_allowed=True),
        MembershipOption(gym_key="power_zone", option_type="addon", option_key="classes", label="Classes",
                        price_with_full_gym_access=Decimal("0.00"), price_for_addons_only=Decimal("20.00"), discount_allowed=True),
        MembershipOption(gym_key="power_zone", option_type="addon", option_key="massage", label="Massage therapy",
                        price_with_full_gym_access=Decimal("25.00"), price_for_addons_only=Decimal("30.00"), discount_allowed=False),
        MembershipOption(gym_key="power_zone", option_type="addon", option_key="physio", label="Physiotherapy",
                        price_with_full_gym_access=Decimal("25.00"), price_for_addons_only=Decimal("30.00"), discount_allowed=False),
    ]
    db.session.add_all(ugym_opts + power_opts)
    db.session.commit()


def seed_discounts() -> None:
    """Seed discount rates."""
    db.session.add_all([
        Discount(discount_type="student_Discount", gym_key="ugym", rate=Decimal("0.20")),
        Discount(discount_type="student_Discount", gym_key="power_zone", rate=Decimal("0.15")),
        Discount(discount_type="pensioner_Discount", gym_key="ugym", rate=Decimal("0.15")),
        Discount(discount_type="pensioner_Discount", gym_key="power_zone", rate=Decimal("0.20")),
    ])
    db.session.commit()


def seed_all_if_empty() -> None:
    """Seed all reference data if the database is empty."""
    if Gym.query.first():
        return
    seed_gyms()
    seed_membership_options()
    seed_discounts()
