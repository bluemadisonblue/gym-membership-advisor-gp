# Gym Membership Advisor (uGym & Power Zone)

A small Flask application that compares **uGym** and **Power Zone** memberships (including add-ons) and recommends the cheapest option based on a user's age category and chosen components.

It includes:
- A guided signup flow (signup -> preferences -> compare plans -> confirm -> create membership)
- User login and membership access
- An admin panel for managing memberships and viewing database stats

## Key features

1. Plan comparison and recommendation
- Calculates pricing for each gym based on:
  - Age category (student/young adult vs pensioner)
  - Selected gym time band (optional)
  - Add-ons (optional): `swim`, `classes`, `massage`, `physio`
- Produces:
  - A recommended gym (cheapest monthly total after discounts)
  - A per-gym pricing breakdown for display

2. Membership creation
- On confirmation, creates a row in the `members` table and logs the user in automatically.

3. User experience
- Users can view their membership details at `/membership/<membership_id>` after login.

4. Admin panel
- Admin dashboard with aggregated stats (counts, revenue totals, recent members)
- List/view members, verify email, and delete members
- Admin views for gyms and the database schema overview

## Tech stack

- Python 3.9+
- Flask
- Flask-SQLAlchemy
- SQLite (local file database)
- `Decimal` for money math

## Application flow (user)

1. Home: `/`
2. Signup: `/signup` (GET/POST)
   - Fields: `full_name`, `email`, `date_of_birth`, `password`, `confirm_password`, `is_student`
   - Age is derived from DOB
   - Under 16 is blocked
   - Stores signup data in `session` for the next steps
3. Preferences: `/preferences` (GET/POST)
   - `wants_gym` (`yes`/`no`)
   - If `wants_gym=yes`: `gym_band`
   - Add-ons: `swim`, `classes`, `massage`, `physio`
   - Validates that you choose either a gym band or at least one add-on
   - Stores preferences in `session`
4. Recommendation: `/recommendation` (GET/POST)
   - Calculates pricing for each gym using `pricing.calculate_pricing_for_selection`
   - Saves the computed `pricing_result` in `session`
   - If you POST, sets `chosen_gym` in `session` and continues
5. Confirm: `/confirm` (GET/POST)
   - Shows the selected plan breakdown
   - POST moves to `/pay`
6. Pay / create membership: `/pay` (GET/POST)
   - POST simulates successful payment and inserts a new `Member` row
   - Computes:
     - `monthly_total` (stored as `Decimal`)
     - `joining_fee` (stored as `Decimal`)
     - `first_payment_total` (joining fee + monthly total)
   - Logs the user in automatically and redirects to:
     - `/success/<membership_id>`
7. Login and membership access
   - Login: `/login`
   - Direct access: `/access` (redirects to the logged-in user's membership)
   - Membership details: `/membership/<membership_id>`

## Admin flow

- Admin login: `/admin/login`
- Admin dashboard: `/admin`
- Manage members:
  - `/admin/members`
  - `/admin/members/<int:member_id>`
  - `/admin/members/<int:member_id>/delete` (POST with CSRF token)
  - `/admin/members/<int:member_id>/verify` (POST with CSRF token)
- Admin gyms list: `/admin/gyms`
- Admin database overview: `/admin/database`

## Pricing logic (high-level)

Pricing is computed in `pricing.py` by `calculate_pricing_for_selection(signup, preferences)`:

- Discount category:
  - Pensioner if `age > 66`
  - Otherwise student/young adult if `is_student` or `age < 25`
  - Otherwise no category (no discount)
- Discount application:
  - Gym plan price is discounted using the configured discount rate per gym
  - Add-ons are discounted only when the add-on is marked as discount-allowed
  - `massage` and `physio` are treated as non-discounted add-ons
- Recommendation rule:
  - Choose the gym with the lowest `monthly_total_after_discount`

## Database and schema

### Storage

- SQLite database file: `instance/gym_membership.db`
- Default database URL is set in `app.py` via:
  - `DATABASE_URL=sqlite:///<project>/instance/gym_membership.db`

### Tables

The app uses these main tables:
- `gyms` (uGym, Power Zone)
- `membership_option` (gym plans + add-ons)
- `discounts` (discount rate per gym per category)
- `members` (created memberships)

### Seeding

Reference data (gyms, membership options, discounts) is seeded automatically the first time the app needs it.

To fully reset and reseed:
```bash
python3 init_db.py
```

## Configuration

Environment variables you can set:

- `SECRET_KEY`
  - Used for Flask session signing
  - Default: `dev-secret-key-change-me`
- `DATABASE_URL`
  - Override the DB connection string
  - Default: local SQLite file in `instance/`
- Admin:
  - `ADMIN_USERNAME` (default: `admin`)
  - `ADMIN_PASSWORD_HASH`
    - Default hash corresponds to password `admin123`
    - Recommended: set your own hash for production-like use

To generate an admin password hash:
```bash
python3 -c "from admin_auth import generate_admin_password_hash; generate_admin_password_hash('your_password')"
```

## Running locally

1. Install:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:
```bash
python3 app.py
```

3. Open:
`http://127.0.0.1:5001/`

Note: the app uses port `5001` by default (to avoid a macOS AirPlay conflict).

## Troubleshooting

1. Pricing/compare-plan errors after previous attempts
- This project stores `pricing_result` in Flask session.
- If you previously had a failing browser session cookie, you might need to clear cookies for this site and try again.

2. Database issues
- If schema/data looks wrong, run a reset:
```bash
python3 init_db.py
```

## Project structure (at a glance)

- `app.py`: Flask app, routes, and membership creation logic
- `pricing.py`: pricing calculations and currency formatting
- `models.py`: SQLAlchemy models (`Gym`, `MembershipOption`, `Discount`, `Member`)
- `data.py`: loads gyms/discounts into in-memory structures used by pricing
- `db_seed.py`: reference data seeders
- `init_db.py`: reset + reseed script
- `templates/`: HTML templates for user/admin pages

