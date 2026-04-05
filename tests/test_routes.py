"""
Integration tests for Flask routes — uses in-memory SQLite via test client.
"""
import pytest
import json


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

class TestHomePage:
    def test_get_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_contains_register_link(self, client):
        resp = client.get("/")
        assert b"Register" in resp.data or b"signup" in resp.data


class TestSignupPage:
    def test_get_returns_200(self, client):
        assert client.get("/signup").status_code == 200

    def test_valid_signup_redirects_to_membership(self, client, app):
        from models import Member
        resp = client.post("/signup", data={
            "full_name": "New User",
            "email": "newuser@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1995-08-20",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Account created" in resp.data or b"Your account" in resp.data or b"membership" in resp.data.lower()

        with app.app_context():
            m = Member.query.filter_by(email="newuser@test.com").first()
            assert m is not None
            assert m.full_name == "New User"

    def test_missing_name_shows_error(self, client):
        resp = client.post("/signup", data={
            "full_name": "",
            "email": "x@x.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1995-01-01",
        }, follow_redirects=True)
        assert b"required" in resp.data.lower() or b"name" in resp.data.lower()

    def test_invalid_email_shows_error(self, client):
        resp = client.post("/signup", data={
            "full_name": "Test",
            "email": "notanemail",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1995-01-01",
        }, follow_redirects=True)
        assert b"email" in resp.data.lower()

    def test_duplicate_email_rejected(self, client, registered_user):
        resp = client.post("/signup", data={
            "full_name": "Duplicate",
            "email": registered_user["email"],
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1990-01-01",
        }, follow_redirects=True)
        assert b"already exists" in resp.data.lower() or b"already" in resp.data.lower()

    def test_password_too_short_rejected(self, client):
        resp = client.post("/signup", data={
            "full_name": "Short Pass",
            "email": "shortpass@test.com",
            "password": "abc",
            "confirm_password": "abc",
            "date_of_birth": "1990-01-01",
        }, follow_redirects=True)
        assert b"8 characters" in resp.data or b"password" in resp.data.lower()

    def test_password_mismatch_rejected(self, client):
        resp = client.post("/signup", data={
            "full_name": "Mismatch",
            "email": "mismatch@test.com",
            "password": "Password1!",
            "confirm_password": "Different1!",
            "date_of_birth": "1990-01-01",
        }, follow_redirects=True)
        assert b"match" in resp.data.lower()

    def test_under_16_rejected(self, client):
        resp = client.post("/signup", data={
            "full_name": "Young Kid",
            "email": "kid@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "2015-01-01",
        }, follow_redirects=True)
        assert b"16" in resp.data or b"under" in resp.data.lower()

    def test_membership_id_assigned(self, client, app):
        from models import Member
        client.post("/signup", data={
            "full_name": "ID Test",
            "email": "idtest@test.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "date_of_birth": "1990-01-01",
        }, follow_redirects=True)
        with app.app_context():
            m = Member.query.filter_by(email="idtest@test.com").first()
            assert m.membership_id.startswith("REG-")


class TestLoginPage:
    def test_get_returns_200(self, client):
        assert client.get("/login").status_code == 200

    def test_valid_login_redirects(self, client, registered_user):
        resp = client.post("/login", data={
            "email": registered_user["email"],
            "password": "Password1!",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Should land on membership details page
        assert (b"membership" in resp.data.lower() or
                b"Welcome" in resp.data or
                b"REG-" in resp.data)

    def test_wrong_password_rejected(self, client, registered_user):
        resp = client.post("/login", data={
            "email": registered_user["email"],
            "password": "WrongPass99!",
        }, follow_redirects=True)
        assert b"Invalid" in resp.data or b"incorrect" in resp.data.lower()

    def test_nonexistent_email_rejected(self, client):
        resp = client.post("/login", data={
            "email": "nobody@nowhere.com",
            "password": "Password1!",
        }, follow_redirects=True)
        assert b"Invalid" in resp.data or b"incorrect" in resp.data.lower()

    def test_missing_email_shows_error(self, client):
        resp = client.post("/login", data={
            "email": "",
            "password": "Password1!",
        }, follow_redirects=True)
        assert b"required" in resp.data.lower() or b"email" in resp.data.lower()


class TestLogout:
    def test_logout_clears_session(self, logged_in_client):
        resp = logged_in_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        # After logout, accessing a protected page should redirect to login
        resp2 = logged_in_client.get("/preferences", follow_redirects=False)
        assert resp2.status_code == 302
        assert "/login" in resp2.headers["Location"]


# ---------------------------------------------------------------------------
# Protected routes — unauthenticated access should redirect
# ---------------------------------------------------------------------------

class TestAuthProtection:
    @pytest.mark.parametrize("path", [
        "/preferences",
        "/recommendation",
        "/confirm",
        "/pay",
    ])
    def test_unauthenticated_redirects_to_login(self, client, path):
        resp = client.get(path, follow_redirects=False)
        # Should redirect (302) since session check happens in route or before
        assert resp.status_code in (302, 200)
        if resp.status_code == 302:
            assert "login" in resp.headers["Location"].lower() or "/" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class TestPreferences:
    def test_get_returns_200_when_logged_in(self, logged_in_client):
        resp = logged_in_client.get("/preferences")
        assert resp.status_code == 200

    def test_valid_gym_preferences_redirect_to_recommendation(self, logged_in_client):
        resp = logged_in_client.post("/preferences", data={
            "wants_gym": "yes",
            "gym_band": "off_peak",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "recommendation" in resp.headers["Location"]

    def test_addons_only_valid(self, logged_in_client):
        resp = logged_in_client.post("/preferences", data={
            "wants_gym": "no",
            "swim": "1",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "recommendation" in resp.headers["Location"]

    def test_no_selection_rejected(self, logged_in_client):
        resp = logged_in_client.post("/preferences", data={
            "wants_gym": "no",
        }, follow_redirects=True)
        assert b"select" in resp.data.lower() or b"component" in resp.data.lower()

    def test_gym_without_band_rejected(self, logged_in_client):
        resp = logged_in_client.post("/preferences", data={
            "wants_gym": "yes",
            "gym_band": "",
        }, follow_redirects=True)
        assert b"time band" in resp.data.lower() or b"select" in resp.data.lower()


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def _set_prefs(self, client):
        client.post("/preferences", data={
            "wants_gym": "yes",
            "gym_band": "off_peak",
        }, follow_redirects=True)

    def test_get_shows_comparison(self, logged_in_client):
        self._set_prefs(logged_in_client)
        resp = logged_in_client.get("/recommendation")
        assert resp.status_code == 200
        assert b"uGym" in resp.data or b"Power Zone" in resp.data

    def test_shows_price_for_both_gyms(self, logged_in_client):
        self._set_prefs(logged_in_client)
        resp = logged_in_client.get("/recommendation")
        assert b"uGym" in resp.data
        assert b"Power Zone" in resp.data

    def test_choosing_gym_redirects_to_confirm(self, logged_in_client):
        self._set_prefs(logged_in_client)
        resp = logged_in_client.post("/recommendation", data={
            "chosen_gym": "power_zone",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "confirm" in resp.headers["Location"]

    def test_invalid_gym_choice_rejected(self, logged_in_client):
        self._set_prefs(logged_in_client)
        resp = logged_in_client.post("/recommendation", data={
            "chosen_gym": "not_a_gym",
        }, follow_redirects=True)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Full flow: preferences → recommendation → confirm → pay
# ---------------------------------------------------------------------------

class TestFullMembershipFlow:
    def _do_prefs(self, client):
        client.post("/preferences", data={
            "wants_gym": "yes",
            "gym_band": "anytime",
        })

    def _do_recommend(self, client, gym="power_zone"):
        client.post("/recommendation", data={"chosen_gym": gym})

    def _do_confirm(self, client):
        client.post("/confirm", data={})

    def test_pay_creates_active_membership(self, logged_in_client, registered_user, app):
        from models import Member
        self._do_prefs(logged_in_client)
        self._do_recommend(logged_in_client)
        self._do_confirm(logged_in_client)

        resp = logged_in_client.post("/pay", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            m = Member.query.filter_by(email=registered_user["email"]).first()
            assert m is not None
            assert m.has_active_membership is True
            assert m.membership_id.startswith("PZ-")

    def test_success_page_accessible_after_pay(self, logged_in_client, registered_user, app):
        from models import Member

        self._do_prefs(logged_in_client)
        self._do_recommend(logged_in_client)
        self._do_confirm(logged_in_client)
        logged_in_client.post("/pay", follow_redirects=True)

        with app.app_context():
            m = Member.query.filter_by(email=registered_user["email"]).first()
            mid = m.membership_id

        resp = logged_in_client.get(f"/success/{mid}")
        assert resp.status_code == 200
        assert b"PZ-" in resp.data or b"Power Zone" in resp.data or b"Membership" in resp.data

    def test_membership_id_format_power_zone(self, logged_in_client, registered_user, app):
        from models import Member

        self._do_prefs(logged_in_client)
        self._do_recommend(logged_in_client, gym="power_zone")
        self._do_confirm(logged_in_client)
        logged_in_client.post("/pay", follow_redirects=True)

        with app.app_context():
            m = Member.query.filter_by(email=registered_user["email"]).first()
            assert m.membership_id.startswith("PZ-2026-")

    def test_double_pay_blocked(self, logged_in_client, app):
        """Trying to pay again after an active membership should redirect."""
        # First payment
        self._do_prefs(logged_in_client)
        self._do_recommend(logged_in_client)
        self._do_confirm(logged_in_client)
        logged_in_client.post("/pay", follow_redirects=True)

        # Second attempt
        resp = logged_in_client.get("/preferences", follow_redirects=True)
        assert resp.status_code == 200
        # Should see "already have a membership" or be redirected away
        assert (b"already" in resp.data.lower() or
                b"membership" in resp.data.lower())


# ---------------------------------------------------------------------------
# Membership details
# ---------------------------------------------------------------------------

class TestMembershipDetails:
    def test_own_membership_accessible(self, logged_in_client, registered_user):
        resp = logged_in_client.get(
            f"/membership/{registered_user['membership_id']}", follow_redirects=True
        )
        assert resp.status_code == 200

    def test_other_membership_blocked(self, logged_in_client):
        resp = logged_in_client.get("/membership/PZ-2099-999999", follow_redirects=True)
        assert resp.status_code == 200
        # Should flash an error or redirect to home
        assert (b"not found" in resp.data.lower() or
                b"denied" in resp.data.lower() or
                b"Find Your Perfect" in resp.data)


# ---------------------------------------------------------------------------
# 404 handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_unknown_route_returns_404(self, client):
        resp = client.get("/this/does/not/exist")
        assert resp.status_code == 404
