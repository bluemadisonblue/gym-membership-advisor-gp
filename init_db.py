"""
Database initialization script. Drops all tables and reseeds.
"""

from app import app
from models import db, Gym, Member, MembershipOption, Discount
from db_seed import seed_gyms, seed_membership_options, seed_discounts


def init_database():
    """Initialize the database with tables and seed data."""
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        print("Seeding gyms...")
        seed_gyms(force=True)
        print("Seeding membership options...")
        seed_membership_options()
        print("Seeding discounts...")
        seed_discounts()
        print("Database initialization complete!")
        print(f"\n  Gyms: {Gym.query.count()}")
        print(f"  Membership Options: {MembershipOption.query.count()}")
        print(f"  Discounts: {Discount.query.count()}")
        print(f"  Members: {Member.query.count()}")
