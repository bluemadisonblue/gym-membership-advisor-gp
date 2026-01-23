from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
import itertools
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from data import GYMS
from pricing import calculate_pricing_for_selection, format_currency


# Get the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(basedir, 'templates'),
    static_folder=os.path.join(basedir, 'static')
)
# Use environment variable for production, fallback to dev key for local development
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


# In-memory membership store (no database for now)
MEMBERSHIPS: Dict[str, Dict[str, Any]] = {}
MEMBERSHIP_COUNTER = itertools.count(1)


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


def calculate_age(date_of_birth: date) -> int:
    """
    Calculate age from date of birth.

    Args:
        date_of_birth: The date of birth

    Returns:
        The calculated age
    """
    today = date.today()
    age = today.year - date_of_birth.year
    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age


def validate_signup_data(full_name: str, date_of_birth_raw: str) -> Tuple[Optional[int], Optional[date], list[str]]:
    """
    Validate signup form data.

    Args:
        full_name: The user's full name
        date_of_birth_raw: The date of birth as a string

    Returns:
        A tuple of (age, date_of_birth, errors)
    """
    errors = []
    age = None
    date_of_birth = None

    if not full_name:
        errors.append("Full name is required.")

    if not date_of_birth_raw:
        errors.append("Date of birth is required.")
    else:
        try:
            date_of_birth = datetime.strptime(date_of_birth_raw, "%Y-%m-%d").date()
            age = calculate_age(date_of_birth)

            if age < 0:
                errors.append("Invalid date of birth.")
            elif age < 16:
                errors.append("We are sorry, but users under 16 cannot sign up for a membership.")
        except ValueError:
            errors.append("Invalid date format.")

    return age, date_of_birth, errors


@app.context_processor
def inject_globals():
    """Inject commonly used helpers into all templates."""
    return {
        "gyms": GYMS,
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
        date_of_birth_raw = (request.form.get("date_of_birth") or "").strip()
        is_student = bool(request.form.get("is_student"))

        age, date_of_birth, errors = validate_signup_data(full_name, date_of_birth_raw)

        if errors:
            for msg in errors:
                flash(msg, "error")
            # Keep entered values so user does not have to retype
            return render_template(
                "signup.html",
                full_name=full_name,
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
        if chosen_gym not in GYMS:
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

    if chosen_gym not in GYMS:
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
        # Simulate payment success and create membership immediately
        membership_id = generate_membership_id(chosen_gym)
        membership_data = {
            "membership_id": membership_id,
            "gym_key": chosen_gym,
            "signup": signup_data,
            "preferences": preferences,
            "pricing": chosen_pricing,
            "created_at": datetime.now(),
        }
        MEMBERSHIPS[membership_id] = membership_data

        flash("Payment successful and membership created!", "success")
        # Clear sensitive data from session but keep membership ID in flash/redirect
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
    membership = MEMBERSHIPS.get(membership_id)
    if not membership:
        flash("Membership not found. Please check your ID or create a new membership.", "error")
        return redirect(url_for("access"))

    return render_template("success.html", membership=membership)


@app.route("/access", methods=["GET", "POST"])
def access():
    """Handle membership access form."""
    if request.method == "POST":
        membership_id = (request.form.get("membership_id") or "").strip()
        if not membership_id:
            flash("Please enter a membership ID.", "error")
            return render_template("access.html")

        membership = MEMBERSHIPS.get(membership_id)
        if not membership:
            flash("No membership found with that ID. Please check and try again.", "error")
            return render_template("access.html")

        return redirect(url_for("membership_details", membership_id=membership_id))

    return render_template("access.html")


@app.route("/membership/<membership_id>")
def membership_details(membership_id: str):
    """Display membership details."""
    membership = MEMBERSHIPS.get(membership_id)
    if not membership:
        flash("Membership not found. Please check your ID or create a new membership.", "error")
        return redirect(url_for("access"))

    return render_template("membership_details.html", membership=membership)


@app.errorhandler(404)
def not_found(error):
    return render_template("base.html", content="Page not found."), 404


# For Vercel serverless deployment
# The 'app' object is automatically detected by Vercel

if __name__ == "__main__":
    # Debug mode is convenient during development; disable in production.
    # Use port 5001 to avoid conflict with AirPlay on macOS
    app.run(debug=True, port=5001)

