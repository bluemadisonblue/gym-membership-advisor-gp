from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
import logging
import os
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("gym_advisor")

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    Response,
)
from sqlalchemy import inspect, func, case, text

from models import db, Gym, Member, MembershipOption, Discount

PENDING_GYM_KEY = "pending"
import data
from pricing import calculate_pricing_for_selection, format_currency, hydrate_pricing_result, money
from db_seed import seed_all_if_empty
# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(basedir, 'templates'),
    static_folder=os.path.join(basedir, 'static')
)
# Use environment variable for production, fallback to dev key for local development
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Database configuration - local SQLite only (stored in instance folder)
os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
db_path = os.path.join(basedir, "instance", "gym_membership.db")
database_url = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"check_same_thread": False}  # Allow multi-threading for SQLite
}

# Initialize database
db.init_app(app)

_db_initialized = False


def _migrate_members_schema() -> None:
    """Add has_active_membership for existing SQLite DBs (defaults existing rows to active)."""
    if db.engine.dialect.name != "sqlite":
        return
    rows = db.session.execute(text("PRAGMA table_info(members)")).fetchall()
    cols = {r[1] for r in rows}
    if "has_active_membership" in cols:
        return
    db.session.execute(
        text("ALTER TABLE members ADD COLUMN has_active_membership BOOLEAN NOT NULL DEFAULT 1")
    )
    db.session.commit()


def _ensure_pending_gym_row() -> None:
    """Placeholder gym for accounts that have not purchased a plan yet."""
    if db.session.get(Gym, PENDING_GYM_KEY):
        return
    db.session.add(
        Gym(
            gym_key=PENDING_GYM_KEY,
            gym_name="Account only (no plan yet)",
            joining_fee=Decimal("0.00"),
        )
    )
    db.session.commit()
    data.invalidate_cache()


def _ensure_db_ready() -> None:
    """Create tables and seed data once on first request."""
    global _db_initialized
    if _db_initialized:
        return
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if "gyms" not in tables or "membership_option" not in tables or "discounts" not in tables:
        db.create_all()
    if "members" in tables:
        _migrate_members_schema()
    seed_all_if_empty()
    _ensure_pending_gym_row()
    _db_initialized = True


@app.before_request
def load_data():
    """Load gym data when needed. Skip for static assets."""
    if request.endpoint == "static":
        return
    _ensure_db_ready()
    if not data.GYMS:
        data.load_gyms_from_db()
        data.load_discounts_from_db()
        data.load_non_discounted_addons_from_db()


# ---------------------------------------------------------------------------
# Simple in-memory login rate limiter (resets on server restart)
# ---------------------------------------------------------------------------
from collections import defaultdict
from datetime import timedelta

_login_failures: Dict[str, list] = defaultdict(list)
_RATE_LIMIT_WINDOW = timedelta(minutes=15)
_RATE_LIMIT_MAX = 5


def _record_login_failure(ip: str) -> None:
    now = datetime.utcnow()
    _login_failures[ip].append(now)
    # Prune old entries
    _login_failures[ip] = [t for t in _login_failures[ip] if now - t < _RATE_LIMIT_WINDOW]


def _is_rate_limited(ip: str) -> bool:
    now = datetime.utcnow()
    recent = [t for t in _login_failures.get(ip, []) if now - t < _RATE_LIMIT_WINDOW]
    _login_failures[ip] = recent
    return len(recent) >= _RATE_LIMIT_MAX


def _clear_login_failures(ip: str) -> None:
    _login_failures.pop(ip, None)


def generate_membership_id(gym_key: str) -> str:
    """Generate a unique membership ID for an active (paid) membership."""
    year = datetime.now().year
    prefix = "UG" if gym_key == "ugym" else "PZ"
    seq = Member.query.filter_by(has_active_membership=True).count() + 1
    return f"{prefix}-{year}-{seq:06d}"


def login_required(f):
    """Decorator to require login for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def _signup_data_from_member(member: Member) -> Dict[str, Any]:
    """Build pricing/signup dict from stored account (no session password)."""
    return {
        "full_name": member.full_name,
        "email": member.email,
        "age": member.age,
        "is_student": member.is_student,
        "is_young_adult": member.is_young_adult,
        "is_pensioner": member.is_pensioner,
    }


def _get_plan_selection_flow() -> Tuple[
    Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]
]:
    """
    Return (signup_data, preferences, error_code).
    error_code is None on success, or one of: "login", "prefs", "already".
    """
    if "user_id" not in session:
        flash("Please log in to continue. Create an account first if you are new.", "error")
        return None, None, "login"
    member = db.session.get(Member, session["user_id"])
    if not member:
        flash("Please log in again.", "error")
        return None, None, "login"
    if member.has_active_membership:
        flash("You already have an active membership.", "info")
        return None, None, "already"
    preferences = session.get("preferences")
    if not preferences:
        flash("Choose your membership preferences first.", "error")
        return None, None, "prefs"
    return _signup_data_from_member(member), preferences, None


def _redirect_for_plan_flow_error(code: Optional[str]) -> Optional[Response]:
    """If error code from _get_plan_selection_flow, return Flask redirect; else None."""
    if code is None:
        return None
    if code == "login":
        return redirect(url_for("login"))
    if code == "already":
        m = db.session.get(Member, session["user_id"])
        if m:
            return redirect(url_for("membership_details", membership_id=m.membership_id))
        return redirect(url_for("home"))
    if code == "prefs":
        return redirect(url_for("preferences"))
    return None


def _get_member_for_user(membership_id: str):
    """Return member if found and owned by current user, else None."""
    member = Member.query.filter_by(membership_id=membership_id).first()
    if not member or member.id != session.get("user_id"):
        return None
    return member


@app.context_processor
def inject_globals():
    """Inject commonly used helpers into all templates."""
    return {
        "gyms": data.GYMS,
        "format_currency": format_currency,
        "user_csrf_token": generate_user_csrf_token(),
    }


@app.context_processor
def inject_account_state():
    """True when logged in but user has not purchased a plan yet."""
    if request.endpoint == "static":
        return {"account_needs_plan": False}
    uid = session.get("user_id")
    if not uid:
        return {"account_needs_plan": False}
    m = db.session.get(Member, uid)
    if not m:
        return {"account_needs_plan": False}
    return {"account_needs_plan": not m.has_active_membership}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup form submission and display."""
    if session.get("user_id"):
        existing = db.session.get(Member, session["user_id"])
        if existing:
            flash("You are already logged in.", "info")
            return redirect(url_for("membership_details", membership_id=existing.membership_id))

    # Calculate max date (today - 16 years) for the date picker
    today = date.today()
    max_date = date(today.year - 16, today.month, today.day)

    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("signup"))

        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        date_of_birth_raw = (request.form.get("date_of_birth") or "").strip()
        password = (request.form.get("password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()
        is_student = bool(request.form.get("is_student"))

        errors = []

        if not full_name:
            errors.append("Full name is required.")

        if not email:
            errors.append("Email address is required.")
        elif "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        else:
            # Check if email already exists
            existing_member = Member.query.filter_by(email=email).first()
            if existing_member:
                errors.append("An account with this email already exists. Please log in instead.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        age = None
        date_of_birth = None
        if not date_of_birth_raw:
            errors.append("Date of birth is required.")
        else:
            try:
                date_of_birth = datetime.strptime(date_of_birth_raw, "%Y-%m-%d").date()
                # Calculate age
                today = date.today()
                age = today.year - date_of_birth.year
                # Adjust if birthday hasn't occurred yet this year
                if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
                    age -= 1

                if age < 0:
                    errors.append("Invalid date of birth.")
            except ValueError:
                errors.append("Invalid date format.")

        if age is not None and age < 16:
            errors.append("We are sorry, but users under 16 cannot sign up for a membership.")

        if errors:
            for msg in errors:
                flash(msg, "error")
            # Keep entered values so user does not have to retype
            return render_template(
                "signup.html",
                full_name=full_name,
                email=email,
                date_of_birth=date_of_birth_raw,
                is_student=is_student,
                max_date=max_date.isoformat(),
            )

        # Derive flags (only if age was successfully calculated)
        is_young_adult = age is not None and age < 25
        is_pensioner = age is not None and age > 66

        member = Member(
            membership_id="TEMP",
            full_name=full_name,
            email=email,
            email_verified=True,
            date_of_birth=date_of_birth,
            age=age,
            is_student=is_student,
            is_young_adult=is_young_adult,
            is_pensioner=is_pensioner,
            chosen_gym=PENDING_GYM_KEY,
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
        member.set_password(password)
        db.session.add(member)
        db.session.flush()
        year = datetime.now().year
        member.membership_id = f"REG-{year}-{member.id:06d}"
        db.session.commit()

        session["user_id"] = member.id
        session["user_email"] = member.email
        session["user_name"] = member.full_name
        session.pop("preferences", None)
        session.pop("chosen_gym", None)
        session.pop("pricing_result", None)

        flash(
            "Account created. You can choose a membership plan whenever you are ready from your account or the menu.",
            "success",
        )
        return redirect(url_for("membership_details", membership_id=member.membership_id))

    return render_template(
        "signup.html",
        max_date=max_date.isoformat(),
        full_name="",
        date_of_birth="",
        is_student=False,
    )


@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    """Handle membership preferences form submission and display."""
    if "user_id" not in session:
        flash("Log in or register first, then choose your plan when you are ready.", "error")
        return redirect(url_for("login"))

    member = db.session.get(Member, session["user_id"])
    if not member:
        flash("Please log in again.", "error")
        return redirect(url_for("login"))

    if member.has_active_membership:
        flash("You already have an active membership.", "info")
        return redirect(url_for("membership_details", membership_id=member.membership_id))

    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("preferences"))

        wants_gym = request.form.get("wants_gym") == "yes"
        gym_band = request.form.get("gym_band") if wants_gym else None

        add_swim = bool(request.form.get("swim"))
        add_classes = bool(request.form.get("classes"))
        add_massage = bool(request.form.get("massage"))
        add_physio = bool(request.form.get("physio"))

        errors = []

        if wants_gym and not gym_band:
            errors.append("Please choose a gym time band.")

        if not wants_gym and not any([add_swim, add_classes, add_massage, add_physio]):
            errors.append("Please select at least one membership component (gym or add-ons).")

        if errors:
            for msg in errors:
                flash(msg, "error")
            return render_template(
                "preferences.html",
                wants_gym="yes" if wants_gym else "no",
                gym_band=gym_band,
                add_swim=add_swim,
                add_classes=add_classes,
                add_massage=add_massage,
                add_physio=add_physio,
            )

        session["preferences"] = {
            "wants_gym": wants_gym,
            "gym_band": gym_band,
            "add_swim": add_swim,
            "add_classes": add_classes,
            "add_massage": add_massage,
            "add_physio": add_physio,
        }

        return redirect(url_for("recommendation"))

    # GET
    saved_pref = session.get("preferences", {})
    return render_template(
        "preferences.html",
        wants_gym="yes" if saved_pref.get("wants_gym") else "no",
        gym_band=saved_pref.get("gym_band"),
        add_swim=saved_pref.get("add_swim", False),
        add_classes=saved_pref.get("add_classes", False),
        add_massage=saved_pref.get("add_massage", False),
        add_physio=saved_pref.get("add_physio", False),
    )


@app.route("/recommendation", methods=["GET", "POST"])
def recommendation():
    """Display gym recommendations and handle gym selection."""
    signup_data, preferences, flow_err = _get_plan_selection_flow()
    redir = _redirect_for_plan_flow_error(flow_err)
    if redir:
        return redir

    pricing_result = calculate_pricing_for_selection(signup_data, preferences)
    session["pricing_result"] = pricing_result
    recommended_gym_key = pricing_result["recommended_gym"]

    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("recommendation"))

        chosen_gym = request.form.get("chosen_gym")
        if chosen_gym not in data.GYMS:
            flash("Invalid gym selection. Please choose one of the available gyms.", "error")
            return render_template(
                "recommendation.html",
                signup=signup_data,
                preferences=preferences,
                pricing=pricing_result,
                recommended_gym=recommended_gym_key,
                chosen_gym=recommended_gym_key,
            )

        session["chosen_gym"] = chosen_gym
        return redirect(url_for("confirm"))

    chosen_gym = session.get("chosen_gym", recommended_gym_key)
    return render_template(
        "recommendation.html",
        signup=signup_data,
        preferences=preferences,
        pricing=pricing_result,
        recommended_gym=recommended_gym_key,
        chosen_gym=chosen_gym,
    )


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    """Display confirmation page before payment."""
    signup_data, preferences, flow_err = _get_plan_selection_flow()
    redir = _redirect_for_plan_flow_error(flow_err)
    if redir:
        return redir

    pricing_result = session.get("pricing_result") or calculate_pricing_for_selection(signup_data, preferences)
    pricing_result = hydrate_pricing_result(pricing_result)
    recommended_gym_key = pricing_result["recommended_gym"]
    chosen_gym = session.get("chosen_gym", recommended_gym_key)

    if chosen_gym not in data.GYMS:
        chosen_gym = recommended_gym_key

    chosen_pricing = pricing_result["gyms"][chosen_gym]

    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("confirm"))
        # When user clicks "Pay", we simulate payment and move to the payment confirmation page.
        session["chosen_gym"] = chosen_gym
        return redirect(url_for("pay"))

    return render_template(
        "confirm.html",
        signup=signup_data,
        preferences=preferences,
        chosen_gym=chosen_gym,
        chosen_pricing=chosen_pricing,
        recommended_gym=recommended_gym_key,
    )


@app.route("/pay", methods=["GET", "POST"])
def pay():
    """Handle payment processing and membership creation."""
    if "user_id" not in session:
        flash("Log in to complete payment.", "error")
        return redirect(url_for("login"))

    member = db.session.get(Member, session["user_id"])
    if not member:
        flash("Please log in again.", "error")
        return redirect(url_for("login"))

    if member.has_active_membership:
        flash("You already have an active membership.", "info")
        return redirect(url_for("membership_details", membership_id=member.membership_id))

    signup_data, preferences, flow_err = _get_plan_selection_flow()
    redir = _redirect_for_plan_flow_error(flow_err)
    if redir:
        return redir

    chosen_gym = session.get("chosen_gym")

    if not chosen_gym:
        flash("Your session has expired or is incomplete. Please choose your plan again.", "error")
        return redirect(url_for("preferences"))

    pricing_result = session.get("pricing_result") or calculate_pricing_for_selection(signup_data, preferences)
    pricing_result = hydrate_pricing_result(pricing_result)
    if chosen_gym not in pricing_result["gyms"]:
        flash("Invalid gym selection in your session. Please choose again.", "error")
        return redirect(url_for("recommendation"))

    chosen_pricing = pricing_result["gyms"][chosen_gym]

    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("pay"))

        membership_id = generate_membership_id(chosen_gym)

        monthly_total = money(chosen_pricing.get("monthly_total_after_discount"))
        joining_fee = money(chosen_pricing.get("joining_fee"))
        first_payment_total = money(joining_fee + monthly_total)

        member.membership_id = membership_id
        member.chosen_gym = chosen_gym
        member.wants_gym = preferences["wants_gym"]
        member.gym_band = preferences.get("gym_band")
        member.add_swim = preferences.get("add_swim", False)
        member.add_classes = preferences.get("add_classes", False)
        member.add_massage = preferences.get("add_massage", False)
        member.add_physio = preferences.get("add_physio", False)
        member.monthly_total = monthly_total
        member.joining_fee = joining_fee
        member.first_payment_total = first_payment_total
        member.has_active_membership = True

        db.session.commit()
        logger.info("Membership created: %s (gym=%s, monthly=£%s)", membership_id, chosen_gym, monthly_total)

        session["user_name"] = member.full_name

        flash("Payment successful and membership created!", "success")
        session.pop("preferences", None)
        session.pop("chosen_gym", None)
        session.pop("pricing_result", None)

        return redirect(url_for("success", membership_id=membership_id))

    # GET: show simulated payment confirmation + button to finalize
    return render_template(
        "pay.html",
        signup=signup_data,
        preferences=preferences,
        chosen_gym=chosen_gym,
        chosen_pricing=chosen_pricing,
    )


@app.route("/success/<membership_id>")
@login_required
def success(membership_id: str):
    """Display success page after membership creation."""
    member = _get_member_for_user(membership_id)
    if not member:
        flash("Membership not found or access denied.", "error")
        return redirect(url_for("home"))

    membership = member.to_dict()
    return render_template("success.html", membership=membership)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not _check_user_csrf():
            flash("Your session has expired. Please try again.", "error")
            return redirect(url_for("login"))

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        errors = []

        if not email:
            errors.append("Email address is required.")
        
        if not password:
            errors.append("Password is required.")
        
        if errors:
            for msg in errors:
                flash(msg, "error")
            return render_template("login.html", email=email)
        
        client_ip = request.remote_addr or "unknown"

        if _is_rate_limited(client_ip):
            logger.warning("Login rate-limited for IP %s (email attempt: %s)", client_ip, email)
            flash("Too many failed login attempts. Please wait 15 minutes before trying again.", "error")
            return render_template("login.html", email=email)

        # Find member by email
        member = Member.query.filter_by(email=email).first()

        if not member or not member.check_password(password):
            _record_login_failure(client_ip)
            logger.warning("Failed login attempt for email=%s from IP=%s", email, client_ip)
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html", email=email)

        _clear_login_failures(client_ip)
        logger.info("Successful login for member id=%s from IP=%s", member.id, client_ip)

        # Set session to logged in
        session["user_id"] = member.id
        session["user_email"] = member.email
        session["user_name"] = member.full_name

        flash(f"Welcome back, {member.full_name}!", "success")
        return redirect(url_for("membership_details", membership_id=member.membership_id))
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("preferences", None)
    session.pop("chosen_gym", None)
    session.pop("pricing_result", None)
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/access", methods=["GET", "POST"])
def access():
    """Handle membership access. Logged-in users go straight to their membership."""
    if "user_id" in session:
        member = Member.query.get(session["user_id"])
        if member:
            return redirect(url_for("membership_details", membership_id=member.membership_id))
    return render_template("access.html")


@app.route("/membership/<membership_id>")
@login_required
def membership_details(membership_id: str):
    """Display membership details. Only the account owner can view."""
    member = _get_member_for_user(membership_id)
    if not member:
        flash("Membership not found or access denied.", "error")
        return redirect(url_for("home"))

    membership = member.to_dict()
    return render_template("membership_details.html", membership=membership)


@app.errorhandler(404)
def not_found(error):
    return render_template("base.html", content="Page not found."), 404


# ============================================================================
# ADMIN ROUTES
# ============================================================================

from admin_auth import (
    require_admin, is_admin_logged_in, verify_password,
    ADMIN_USERNAME, ADMIN_PASSWORD_HASH, log_admin_action,
    generate_csrf_token, verify_csrf_token,
    generate_user_csrf_token, verify_user_csrf_token,
)


def _check_user_csrf() -> bool:
    """Return True when the request passes CSRF validation (or app is in test mode)."""
    if app.config.get("TESTING"):
        return True
    return verify_user_csrf_token(request.form.get("user_csrf_token", ""))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if is_admin_logged_in():
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
            session["is_admin"] = True
            session["admin_username"] = username
            session["admin_ip"] = request.remote_addr
            log_admin_action("LOGIN", f"Successful login from {request.remote_addr}")
            flash("Welcome to the admin panel!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            log_admin_action("LOGIN_FAILED", f"Failed login attempt for '{username}' from {request.remote_addr}")
            flash("Invalid credentials.", "error")
    
    return render_template("admin/login.html")


@app.route("/admin/logout")
@require_admin
def admin_logout():
    """Admin logout."""
    log_admin_action("LOGOUT", "Admin logged out")
    session.pop("is_admin", None)
    session.pop("admin_username", None)
    session.pop("admin_ip", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/admin")
@require_admin
def admin_dashboard():
    """Admin dashboard with statistics."""
    total_verified = db.session.query(
        func.count(Member.id).label("total"),
        func.sum(case((Member.email_verified == True, 1), else_=0)).label("verified"),
    ).first()
    total_members = total_verified.total or 0
    verified_members = int(total_verified.verified or 0)
    unverified_members = total_members - verified_members

    # Members by gym
    members_by_gym = db.session.query(
        Member.chosen_gym,
        func.count(Member.id).label('count')
    ).group_by(Member.chosen_gym).all()
    
    # Recent members
    recent_members = Member.query.order_by(Member.created_at.desc()).limit(10).all()
    
    # Revenue calculations (approximate)
    total_monthly_revenue = db.session.query(func.sum(Member.monthly_total)).scalar() or 0
    total_joining_fees = db.session.query(func.sum(Member.joining_fee)).scalar() or 0
    
    stats = {
        'total_members': total_members,
        'verified_members': verified_members,
        'unverified_members': unverified_members,
        'members_by_gym': dict(members_by_gym),
        'total_monthly_revenue': total_monthly_revenue,
        'total_joining_fees': total_joining_fees,
        'recent_members': recent_members
    }
    
    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/members")
@require_admin
def admin_members():
    """List all members."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Search and filter
    search = request.args.get('search', '').strip()
    gym_filter = request.args.get('gym', '')
    verified_filter = request.args.get('verified', '')
    
    query = Member.query
    
    if search:
        query = query.filter(
            (Member.full_name.ilike(f'%{search}%')) |
            (Member.email.ilike(f'%{search}%')) |
            (Member.membership_id.ilike(f'%{search}%'))
        )
    
    if gym_filter:
        query = query.filter_by(chosen_gym=gym_filter)
    
    if verified_filter == 'yes':
        query = query.filter_by(email_verified=True)
    elif verified_filter == 'no':
        query = query.filter_by(email_verified=False)
    
    members = query.order_by(Member.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template("admin/members.html", members=members, 
                         search=search, gym_filter=gym_filter, 
                         verified_filter=verified_filter)


@app.route("/admin/members/<int:member_id>")
@require_admin
def admin_member_detail(member_id):
    """View member details."""
    member = Member.query.get_or_404(member_id)
    return render_template("admin/member_detail.html", member=member)


@app.route("/admin/members/<int:member_id>/delete", methods=["POST"])
@require_admin
def admin_delete_member(member_id):
    """Delete a member."""
    if not verify_csrf_token(request.form.get("csrf_token", "")):
        flash("Invalid security token.", "error")
        return redirect(url_for("admin_members"))
    
    member = Member.query.get_or_404(member_id)
    membership_id = member.membership_id
    
    db.session.delete(member)
    db.session.commit()
    
    log_admin_action("DELETE_MEMBER", f"Deleted member: {membership_id}")
    flash(f"Member {membership_id} has been deleted.", "success")
    return redirect(url_for("admin_members"))


@app.route("/admin/members/<int:member_id>/verify", methods=["POST"])
@require_admin
def admin_verify_member(member_id):
    """Manually verify a member's email."""
    if not verify_csrf_token(request.form.get("csrf_token", "")):
        flash("Invalid security token.", "error")
        return redirect(url_for("admin_member_detail", member_id=member_id))
    
    member = Member.query.get_or_404(member_id)
    member.email_verified = True
    member.verification_token = None
    db.session.commit()
    
    log_admin_action("VERIFY_MEMBER", f"Manually verified: {member.membership_id}")
    flash(f"Email verified for {member.membership_id}.", "success")
    return redirect(url_for("admin_member_detail", member_id=member_id))


@app.route("/admin/gyms")
@require_admin
def admin_gyms():
    """Manage gyms and pricing."""
    gyms = Gym.query.all()
    return render_template("admin/gyms.html", gyms=gyms)


@app.route("/admin/database")
@require_admin
def admin_database():
    """Database statistics and management."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    tables = []

    for table_name in sorted(inspector.get_table_names()):
        try:
            result = db.session.execute(
                text(f'SELECT COUNT(*) AS count FROM "{table_name}"')
            )
            count = result.scalar() or 0
        except Exception:
            count = 0

        raw_cols = inspector.get_columns(table_name)
        pk_cols = set()
        try:
            pk = inspector.get_pk_constraint(table_name)
            if pk and pk.get("constrained_columns"):
                pk_cols = set(pk["constrained_columns"])
        except Exception:
            pass

        columns = []
        for c in raw_cols:
            col_type = c.get("type")
            type_str = str(col_type) if col_type else "—"
            columns.append({
                "name": c.get("name", "—"),
                "type": type_str,
                "nullable": c.get("nullable", False),
                "primary_key": c.get("name") in pk_cols,
            })

        tables.append({
            "name": table_name,
            "row_count": count,
            "column_count": len(columns),
            "columns": columns,
        })

    return render_template("admin/database.html", tables=tables)


@app.context_processor
def inject_admin_context():
    """Inject admin-related variables into templates."""
    admin_logged_in = is_admin_logged_in()
    return {
        "is_admin": admin_logged_in,
        "csrf_token": generate_csrf_token() if admin_logged_in else None,
    }


if __name__ == "__main__":
    # Debug mode is convenient during development; disable in production.
    # Use port 5001 to avoid conflict with AirPlay on macOS
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)

