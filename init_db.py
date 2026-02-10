"""
Database initialization script for the Gym Membership Advisor.

This script creates all tables and populates them with initial data
based on the existing data.py configuration.
"""

from decimal import Decimal
from app import app
from models import db, Gym, MembershipOption, Discount


def init_database():
    """Initialize the database with tables and seed data."""
    with app.app_context():
        # Drop all existing tables and recreate them
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating tables...")
        db.create_all()
        
        # Seed gyms
        print("Seeding gyms...")
        ugym = Gym(
            gym_key='ugym',
            gym_name='uGym',
            joining_fee=Decimal('10.00')
        )
        power_zone = Gym(
            gym_key='power_zone',
            gym_name='Power Zone',
            joining_fee=Decimal('30.00')
        )
        
        db.session.add(ugym)
        db.session.add(power_zone)
        db.session.commit()
        
        # Seed membership options for uGym
        print("Seeding membership options for uGym...")
        ugym_options = [
            # Gym plans
            MembershipOption(
                gym_key='ugym',
                option_type='gym_plan',
                option_key='super_off_peak',
                label='Super off-peak (10-12 & 2-4)',
                price=Decimal('16.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='ugym',
                option_type='gym_plan',
                option_key='off_peak',
                label='Off-peak (12-2 & 8-11)',
                price=Decimal('21.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='ugym',
                option_type='gym_plan',
                option_key='anytime',
                label='Anytime',
                price=Decimal('30.00'),
                discount_allowed=True
            ),
            # Add-ons
            MembershipOption(
                gym_key='ugym',
                option_type='addon',
                option_key='swim',
                label='Swimming pool',
                price_with_full_gym_access=Decimal('15.00'),
                price_for_addons_only=Decimal('25.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='ugym',
                option_type='addon',
                option_key='classes',
                label='Classes',
                price_with_full_gym_access=Decimal('10.00'),
                price_for_addons_only=Decimal('20.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='ugym',
                option_type='addon',
                option_key='massage',
                label='Massage therapy',
                price_with_full_gym_access=Decimal('25.00'),
                price_for_addons_only=Decimal('30.00'),
                discount_allowed=False
            ),
            MembershipOption(
                gym_key='ugym',
                option_type='addon',
                option_key='physio',
                label='Physiotherapy',
                price_with_full_gym_access=Decimal('20.00'),
                price_for_addons_only=Decimal('25.00'),
                discount_allowed=False
            ),
        ]
        
        # Seed membership options for Power Zone
        print("Seeding membership options for Power Zone...")
        power_zone_options = [
            # Gym plans
            MembershipOption(
                gym_key='power_zone',
                option_type='gym_plan',
                option_key='super_off_peak',
                label='Super off-peak',
                price=Decimal('13.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='power_zone',
                option_type='gym_plan',
                option_key='off_peak',
                label='Off-peak',
                price=Decimal('19.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='power_zone',
                option_type='gym_plan',
                option_key='anytime',
                label='Anytime',
                price=Decimal('24.00'),
                discount_allowed=True
            ),
            # Add-ons
            MembershipOption(
                gym_key='power_zone',
                option_type='addon',
                option_key='swim',
                label='Swimming pool',
                price_with_full_gym_access=Decimal('12.50'),
                price_for_addons_only=Decimal('20.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='power_zone',
                option_type='addon',
                option_key='classes',
                label='Classes',
                price_with_full_gym_access=Decimal('0.00'),
                price_for_addons_only=Decimal('20.00'),
                discount_allowed=True
            ),
            MembershipOption(
                gym_key='power_zone',
                option_type='addon',
                option_key='massage',
                label='Massage therapy',
                price_with_full_gym_access=Decimal('25.00'),
                price_for_addons_only=Decimal('30.00'),
                discount_allowed=False
            ),
            MembershipOption(
                gym_key='power_zone',
                option_type='addon',
                option_key='physio',
                label='Physiotherapy',
                price_with_full_gym_access=Decimal('25.00'),
                price_for_addons_only=Decimal('30.00'),
                discount_allowed=False
            ),
        ]
        
        for option in ugym_options + power_zone_options:
            db.session.add(option)
        db.session.commit()
        
        # Seed discounts
        print("Seeding discounts...")
        discounts = [
            # Student/Young adult discounts
            Discount(
                discount_type='student_Discount',
                gym_key='ugym',
                rate=Decimal('0.20')  # 20% off
            ),
            Discount(
                discount_type='student_Discount',
                gym_key='power_zone',
                rate=Decimal('0.15')  # 15% off
            ),
            # Pensioner discounts
            Discount(
                discount_type='pensioner_Discount',
                gym_key='ugym',
                rate=Decimal('0.15')  # 15% off
            ),
            Discount(
                discount_type='pensioner_Discount',
                gym_key='power_zone',
                rate=Decimal('0.20')  # 20% off
            ),
        ]
        
        for discount in discounts:
            db.session.add(discount)
        db.session.commit()
        
        print("Database initialization complete!")
        
        # Display summary
        print("\nDatabase summary:")
        print(f"  Gyms: {Gym.query.count()}")
        print(f"  Membership Options: {MembershipOption.query.count()}")
        print(f"  Discounts: {Discount.query.count()}")
        print(f"  Members: {0}")  # No members initially


if __name__ == '__main__':
    init_database()
