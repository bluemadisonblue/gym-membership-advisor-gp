"""
Tests for models.py — ORM model methods.
"""
import pytest
from decimal import Decimal
from datetime import date


class TestMemberPassword:
    """Test password hashing directly via werkzeug — no DB needed."""

    def test_set_and_check_correct_password(self, app):
        from werkzeug.security import generate_password_hash, check_password_hash
        h = generate_password_hash("secret123", method="pbkdf2:sha256")
        assert check_password_hash(h, "secret123") is True

    def test_wrong_password_returns_false(self, app):
        from werkzeug.security import generate_password_hash, check_password_hash
        h = generate_password_hash("correct_pass", method="pbkdf2:sha256")
        assert check_password_hash(h, "wrong_pass") is False

    def test_hash_is_not_plaintext(self, app):
        from werkzeug.security import generate_password_hash
        h = generate_password_hash("mysecret", method="pbkdf2:sha256")
        assert "mysecret" not in h

    def test_uses_pbkdf2(self, app):
        from werkzeug.security import generate_password_hash
        h = generate_password_hash("anypass", method="pbkdf2:sha256")
        assert h.startswith("pbkdf2:sha256")

    def test_member_set_and_check_via_signup(self, client, app):
        """End-to-end: password set at signup, verified at login."""
        from models import Member
        client.post("/signup", data={
            "full_name": "Hash Test",
            "email": "hashtest@test.com",
            "password": "MyPass123!",
            "confirm_password": "MyPass123!",
            "date_of_birth": "1990-01-01",
        }, follow_redirects=True)
        with app.app_context():
            m = Member.query.filter_by(email="hashtest@test.com").first()
            assert m is not None
            assert m.check_password("MyPass123!") is True
            assert m.check_password("WrongPass") is False
            assert m.password_hash.startswith("pbkdf2:sha256")


class TestMemberToDict:
    def test_to_dict_contains_expected_keys_inactive(self, app):
        """to_dict() for a member without an active plan returns nested signup/pricing."""
        from models import db, Member
        with app.app_context():
            member = Member(
                membership_id="TEST-2026-000099",
                full_name="Dict Tester",
                email="dicttest@example.com",
                email_verified=True,
                date_of_birth=date(1990, 1, 1),
                age=35,
                is_student=False,
                is_young_adult=False,
                is_pensioner=False,
                chosen_gym="pending",
                wants_gym=False,
                gym_band=None,
                add_swim=False,
                add_classes=False,
                add_massage=False,
                add_physio=False,
                monthly_total=Decimal("0.00"),
                joining_fee=Decimal("0.00"),
                first_payment_total=Decimal("0.00"),
                has_active_membership=False,
            )
            member.set_password("pass1234")
            db.session.add(member)
            db.session.commit()

            d = member.to_dict()
            assert d["membership_id"] == "TEST-2026-000099"
            assert d["has_active_membership"] is False
            assert d["signup"]["full_name"] == "Dict Tester"
            assert "pricing" in d
            assert "gym_name" in d["pricing"]

            db.session.delete(member)
            db.session.commit()


class TestMemberAgeFlags:
    """Verify the age-derived boolean flags stored on signup."""

    def test_young_adult_flag(self, client, app):
        from models import Member
        client.post("/signup", data={
            "full_name": "Young Adult",
            "email": "young@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "2005-01-01",  # age ~21
        }, follow_redirects=True)
        with app.app_context():
            m = Member.query.filter_by(email="young@test.com").first()
            assert m is not None
            assert m.is_young_adult is True
            assert m.is_pensioner is False

    def test_pensioner_flag(self, client, app):
        from models import Member
        client.post("/signup", data={
            "full_name": "Pensioner Pete",
            "email": "pensioner@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1950-06-01",  # age ~75
        }, follow_redirects=True)
        with app.app_context():
            m = Member.query.filter_by(email="pensioner@test.com").first()
            assert m is not None
            assert m.is_pensioner is True
            assert m.is_young_adult is False

    def test_regular_adult_no_flags(self, client, app):
        from models import Member
        client.post("/signup", data={
            "full_name": "Regular Rita",
            "email": "regular@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1985-03-15",  # age ~40
        }, follow_redirects=True)
        with app.app_context():
            m = Member.query.filter_by(email="regular@test.com").first()
            assert m is not None
            assert m.is_young_adult is False
            assert m.is_pensioner is False
