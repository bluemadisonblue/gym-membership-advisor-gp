from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
import itertools
import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from models import db, Gym, Member
import data
from pricing import calculate_pricing_for_selection, format_currency
from email_utils import init_mail, generate_timed_token, verify_timed_token, send_verification_email


# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(basedir, 'templates'),
    static_folder=os.path.join(basedir, 'static')
)
# Use environment variable for production, fallback to dev key for local development
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Database configuration
# Use SQLite for local development, can be changed to MySQL/PostgreSQL for production
database_url = os.environ.get("DATABASE_URL", "sqlite:///gym_membership.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize email
mail = init_mail(app)

# Membership counter for generating unique IDs
MEMBERSHIP_COUNTER = itertools.count(1)


# Load gym data from database on application startup
@app.before_request
def load_data():
    """Load gym data from database before handling requests."""
    if not data.GYMS:
        data.load_gyms_from_db()
        data.load_discounts_from_db()
        data.load_non_discounted_addons_from_db()


def generate_membership_id(gym_key: str) -> str:
    """
    Generate a human-friendly membership ID.

    Args:
        gym_key: The gym key identifier ("ugym" or "power_zone")

    Returns:
        A formatted membership ID string (e.g., "UG-2026-000123" or "PZ-2026-000124")
    """
    year = datetime.now().year
    prefix = "UG" if gym_key == "ugym" else "PZ"
    seq = next(MEMBERSHIP_COUNTER)
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


@app.context_processor
def inject_globals():
    """Inject commonly used helpers into all templates."""
    return {
        "gyms": data.GYMS,
        "format_currency": format_currency,
    }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup form submission and display."""
    # Calculate max date (today - 16 years) for the date picker
    today = date.today()
    max_date = date(today.year - 16, today.month, today.day)

    if request.method == "POST":
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

        # Derive flags
        is_young_adult = age < 25
        is_pensioner = age > 66

        # Store in session for later steps
        session["signup"] = {
            "full_name": full_name,
            "email": email,
            "password": password,  # Store temporarily in session, will be hashed when creating member
            "age": age,
            "is_student": is_student,
            "is_young_adult": is_young_adult,
            "is_pensioner": is_pensioner,
        }

        flash("Signup details saved. Please select your membership preferences.", "success")
        return redirect(url_for("preferences"))

    # GET: Load saved values if returning to this page
    saved = session.get("signup", {})
    return render_template(
        "signup.html",
        max_date=max_date.isoformat(),
        full_name=saved.get("full_name", ""),
        date_of_birth=saved.get("date_of_birth", ""),
        is_student=saved.get("is_student", False),
    )


@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    """Handle membership preferences form submission and display."""
    signup_data = session.get("signup")
    if not signup_data:
        flash("Please start by completing the signup form.", "error")
        return redirect(url_for("signup"))

    if request.method == "POST":
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
    signup_data = session.get("signup")
    preferences = session.get("preferences")
    if not signup_data or not preferences:
        flash("Please complete the signup and preferences steps first.", "error")
        return redirect(url_for("signup"))

    pricing_result = calculate_pricing_for_selection(signup_data, preferences)
    recommended_gym_key = pricing_result["recommended_gym"]

    if request.method == "POST":
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
    signup_data = session.get("signup")
    preferences = session.get("preferences")
    if not signup_data or not preferences:
        flash("Please complete the signup and preferences steps first.", "error")
        return redirect(url_for("signup"))

    pricing_result = calculate_pricing_for_selection(signup_data, preferences)
    recommended_gym_key = pricing_result["recommended_gym"]
    chosen_gym = session.get("chosen_gym", recommended_gym_key)

    if chosen_gym not in data.GYMS:
        chosen_gym = recommended_gym_key

    chosen_pricing = pricing_result["gyms"][chosen_gym]

    if request.method == "POST":
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
    signup_data = session.get("signup")
    preferences = session.get("preferences")
    chosen_gym = session.get("chosen_gym")

    if not signup_data or not preferences or not chosen_gym:
        flash("Your session has expired or is incomplete. Please start again.", "error")
        return redirect(url_for("signup"))

    pricing_result = calculate_pricing_for_selection(signup_data, preferences)
    if chosen_gym not in pricing_result["gyms"]:
        flash("Invalid gym selection in your session. Please choose again.", "error")
        return redirect(url_for("recommendation"))

    chosen_pricing = pricing_result["gyms"][chosen_gym]

    if request.method == "POST":
        # Simulate payment success and create membership in database
        membership_id = generate_membership_id(chosen_gym)
        
        # Calculate date_of_birth from age (approximation)
        today = date.today()
        age = signup_data['age']
        date_of_birth = date(today.year - age, today.month, today.day)
        
        # Generate verification token
        token = generate_timed_token(app, signup_data['email'])
        
        # Create new member in database
        new_member = Member(
            membership_id=membership_id,
            full_name=signup_data['full_name'],
            email=signup_data['email'],
            password_hash='',  # Temporary, will be set below
            email_verified=False,
            verification_token=token,
            verification_sent_at=datetime.utcnow(),
            date_of_birth=date_of_birth,
            age=signup_data['age'],
            is_student=signup_data['is_student'],
            is_young_adult=signup_data.get('is_young_adult', False),
            is_pensioner=signup_data.get('is_pensioner', False),
            chosen_gym=chosen_gym,
            wants_gym=preferences['wants_gym'],
            gym_band=preferences.get('gym_band'),
            add_swim=preferences.get('add_swim', False),
            add_classes=preferences.get('add_classes', False),
            add_massage=preferences.get('add_massage', False),
            add_physio=preferences.get('add_physio', False),
            monthly_total=chosen_pricing['monthly_total_after_discount'],
            joining_fee=chosen_pricing['joining_fee'],
            first_payment_total=chosen_pricing['joining_fee'] + chosen_pricing['monthly_total_after_discount']
        )
        
        # Hash and set password
        new_member.set_password(signup_data['password'])
        
        db.session.add(new_member)
        db.session.commit()
        
        # Send verification email
        verification_url = url_for('verify_email', token=token, _external=True)
        send_verification_email(app, new_member, verification_url)

        flash("Payment successful and membership created! Please check your email to verify your account.", "success")
        # Clear sensitive data from session but keep membership ID in flash/redirect
        session.pop("signup", None)
        session.pop("preferences", None)
        session.pop("chosen_gym", None)

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
def success(membership_id: str):
    """Display success page after membership creation."""
    member = Member.query.filter_by(membership_id=membership_id).first()
    if not member:
        flash("Membership not found. Please check your ID or create a new membership.", "error")
        return redirect(url_for("access"))

    membership = member.to_dict()
    return render_template("success.html", membership=membership)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
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
        
        # Find member by email
        member = Member.query.filter_by(email=email).first()
        
        if not member or not member.check_password(password):
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html", email=email)
        
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
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/access", methods=["GET", "POST"])
def access():
    """Handle membership access form."""
    if request.method == "POST":
        membership_id = (request.form.get("membership_id") or "").strip()
        if not membership_id:
            flash("Please enter a membership ID.", "error")
            return render_template("access.html")

        member = Member.query.filter_by(membership_id=membership_id).first()
        if not member:
            flash("No membership found with that ID. Please check and try again.", "error")
            return render_template("access.html")

        return redirect(url_for("membership_details", membership_id=membership_id))

    return render_template("access.html")


@app.route("/membership/<membership_id>")
def membership_details(membership_id: str):
    """Display membership details."""
    member = Member.query.filter_by(membership_id=membership_id).first()
    if not member:
        flash("Membership not found. Please check your ID or create a new membership.", "error")
        return redirect(url_for("access"))

    membership = member.to_dict()
    return render_template("membership_details.html", membership=membership)


@app.route("/verify-email/<token>")
def verify_email(token):
    """Verify email address using the token."""
    email = verify_timed_token(app, token, max_age=3600)  # 1 hour expiry
    
    if not email:
        flash("Invalid or expired verification link. Please request a new one.", "error")
        return redirect(url_for("resend_verification"))
    
    # Find member by email
    member = Member.query.filter_by(email=email).first()
    
    if not member:
        flash("Member not found. Please sign up again.", "error")
        return redirect(url_for("signup"))
    
    if member.email_verified:
        flash("Your email is already verified!", "success")
        return redirect(url_for("access"))
    
    # Mark email as verified
    member.email_verified = True
    member.verification_token = None
    db.session.commit()
    
    flash("Email verified successfully! You can now proceed with your membership.", "success")
    
    # Render verification success page
    return render_template("email_verified.html", member=member)


@app.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    """Resend verification email."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        
        if not email:
            flash("Please enter your email address.", "error")
            return render_template("resend_verification.html")
        
        member = Member.query.filter_by(email=email).first()
        
        if not member:
            # Don't reveal if email exists or not for security
            flash("If an account exists with this email, a verification link has been sent.", "info")
            return render_template("resend_verification.html")
        
        if member.email_verified:
            flash("Your email is already verified! You can access your membership.", "success")
            return redirect(url_for("access"))
        
        # Generate new token and send email
        token = generate_timed_token(app, member.email)
        verification_url = url_for('verify_email', token=token, _external=True)
        
        from email_utils import send_resend_verification_email
        if send_resend_verification_email(app, member, verification_url):
            member.verification_sent_at = datetime.utcnow()
            db.session.commit()
            flash("Verification email sent! Please check your inbox.", "success")
        else:
            flash("Failed to send verification email. Please try again later.", "error")
        
        return render_template("resend_verification.html")
    
    return render_template("resend_verification.html")


@app.errorhandler(404)
def not_found(error):
    return render_template("base.html", content="Page not found."), 404


# ============================================================================
# ADMIN ROUTES
# ============================================================================

from admin_auth import (
    require_admin, is_admin_logged_in, verify_password, 
    ADMIN_USERNAME, ADMIN_PASSWORD_HASH, log_admin_action, generate_csrf_token, verify_csrf_token
)
from sqlalchemy import func


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
    # Get statistics
    total_members = Member.query.count()
    verified_members = Member.query.filter_by(email_verified=True).count()
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
    from sqlalchemy import inspect
    
    # Get all table information
    inspector = inspect(db.engine)
    tables = []
    
    for table_name in inspector.get_table_names():
        # Get row count
        result = db.session.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = result.scalar()
        
        # Get columns
        columns = inspector.get_columns(table_name)
        
        tables.append({
            'name': table_name,
            'row_count': count,
            'column_count': len(columns),
            'columns': columns
        })
    
    return render_template("admin/database.html", tables=tables)


@app.context_processor
def inject_admin_context():
    """Inject admin-related variables into templates."""
    return {
        'is_admin': is_admin_logged_in(),
        'csrf_token': generate_csrf_token() if is_admin_logged_in() else None
    }


# For Vercel serverless deployment
# The 'app' object is automatically detected by Vercel

if __name__ == "__main__":
    # Debug mode is convenient during development; disable in production.
    # Use port 5001 to avoid conflict with AirPlay on macOS
    app.run(debug=True, port=5001)

