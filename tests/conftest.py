"""
Pytest fixtures shared across the test suite.
"""
import pytest
from decimal import Decimal

import data as data_module


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing with an in-memory SQLite database."""
    import os
    os.environ["SECRET_KEY"] = "test-secret-key"

    from app import app as flask_app
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key",
    )

    from models import db
    from db_seed import seed_all_if_empty

    with flask_app.app_context():
        db.create_all()
        seed_all_if_empty()

        # Ensure the pending gym row exists
        from app import _ensure_pending_gym_row, PENDING_GYM_KEY
        from models import Gym
        if not db.session.get(Gym, PENDING_GYM_KEY):
            _ensure_pending_gym_row()

        # Load data into the module-level cache
        data_module.load_gyms_from_db()
        data_module.load_discounts_from_db()
        data_module.load_non_discounted_addons_from_db()

        yield flask_app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Database session for direct model manipulation in tests."""
    from models import db as _db
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture()
def registered_user(client, app):
    """Create and return a registered (but no active membership) test user via the signup route."""
    from models import db as _db, Member
    with app.app_context():
        # Clean up any leftover test user
        Member.query.filter_by(email="flow@test.com").delete()
        _db.session.commit()

    resp = client.post("/signup", data={
        "full_name": "Flow Tester",
        "email": "flow@test.com",
        "password": "Password1!",
        "confirm_password": "Password1!",
        "date_of_birth": "2000-06-15",
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        member = Member.query.filter_by(email="flow@test.com").first()
        assert member is not None
        return {"id": member.id, "email": member.email, "membership_id": member.membership_id}


@pytest.fixture()
def logged_in_client(client, registered_user):
    """A test client that is already logged in as the registered test user."""
    client.post("/login", data={
        "email": registered_user["email"],
        "password": "Password1!",
    }, follow_redirects=True)
    return client
