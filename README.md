## IY470 Gym Membership Demo (uGym & Power Zone)

This is a small Flask web application for the IY470 Web Programming group project.  
It compares two gyms, **uGym** and **Power Zone**, and recommends the cheapest option
for a user based on their age, student status, and selected facilities.

All data is stored in memory (no database yet) and the code has been organized so that
it is easy to plug in SQLAlchemy models later.

---

### Features

- **Two gyms**: uGym and Power Zone, each with joining fees and different price tables.
- **Age restrictions**: users under 16 cannot sign up.
- **Discount rules**:
  - Students and young adults (age \< 25):
    - uGym: 20% discount
    - Power Zone: 15% discount
  - Pensioners (age \> 66):
    - uGym: 15% discount
    - Power Zone: 20% discount
  - Discounts never apply to massage therapy or physiotherapy.
- **Membership flow**:
  - Home → Sign up (collects personal details)
  - Preferences (choose gym times and add-ons)
  - Recommendation (side‑by‑side cost breakdown and recommended gym)
  - Confirmation (final review)
  - Payment simulation (no real payment)
  - Success page with generated membership ID
  - Access membership by ID to view stored details.
- **In-memory membership store**:
  - Unique, human-friendly membership IDs such as `UG-2026-000001`.
  - Stored in a global Python dictionary for the duration of the process.
- **Responsive UI** using plain CSS, semantic HTML, and Jinja templates.

---

### Project structure

- `app.py` — Flask application, routes, and in-memory membership store.
- `data.py` — Static membership option tables and discount constants.
- `pricing.py` — Pricing and discount calculation logic using `decimal.Decimal`.
- `templates/base.html` — Base layout with navigation and flash messages.
- `templates/home.html` — Landing page with project overview and main actions.
- `templates/signup.html` — Signup form (name, age, student status).
- `templates/preferences.html` — Membership components: gym time band & add‑ons.
- `templates/recommendation.html` — Side‑by‑side pricing and recommendation.
- `templates/confirm.html` — Final selection review and “Pay” button.
- `templates/pay.html` — Simulated payment confirmation and “Create Membership”.
- `templates/success.html` — Membership ID and summary after creation.
- `templates/access.html` — Form to enter membership ID.
- `templates/membership_details.html` — Detailed view of a stored membership.
- `static/styles.css` — Responsive, accessible styling (no JS frameworks).

---

### Requirements

- Python 3.10+ (recommended)
- Flask (installed via `pip`)

No other third‑party libraries are required.

---

### How to run

1. **Create and activate a virtual environment (recommended)**

   ```bash
   cd "webdev group project"
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Flask**

   ```bash
   pip install Flask
   ```

3. **Run the app**

   ```bash
   python app.py
   ```

4. **Open in browser**

   Visit `http://127.0.0.1:5000/` in your browser.

---

### Implementation notes

- **No database**:
  - Memberships are stored in a global in‑memory dict in `app.py` keyed by `membership_id`.
  - Restarting the server clears all memberships.
- **Money handling**:
  - Prices and discounts are stored as `decimal.Decimal` values in `data.py`.
  - All rounding is to 2 decimal places (banking‑style) in `pricing.py`.
  - Templates use a helper `format_currency` to display values as `£xx.xx`.
- **Separation of concerns**:
  - `data.py` holds all price tables and discount definitions.
  - `pricing.py` contains pure functions for calculating totals and recommendations.
  - `app.py` handles request flow, sessions, and user feedback (via `flash`).
- **Session flow**:
  - `/signup` saves personal details into `session["signup"]`.
  - `/preferences` saves preference choices into `session["preferences"]`.
  - `/recommendation` and `/confirm` compute pricing from those structures.
  - `/pay` simulates payment and, on POST, creates and stores the membership.

---

### Manual testing checklist

Use these scenarios to manually verify the business rules and UI:

1. **Under‑16 rejection**
   - Go to **Sign Up**, enter age `15`, any name, any student choice.
   - Submit and confirm you see a friendly message that users under 16 cannot sign up.

2. **Student / young adult with gym + swimming**
   - Age: `19`, tick **student**.
   - Preferences: choose **gym** with *off‑peak* band and add **swimming pool**.
   - Verify:
     - Student/young adult discount is applied to gym and swim (where eligible) for both gyms.
     - The recommendation selects the cheaper monthly option.
     - Joining fee appears separately.

3. **Pensioner with physiotherapy only (no gym)**
   - Age: `70`, do **not** tick student.
   - Preferences: choose **no gym**, tick **physiotherapy** only.
   - Verify:
     - Pensioner discount category is used (overrides student/young logic).
     - No discount is applied to physiotherapy in either gym (price is unchanged).
     - Both gyms show correct monthly totals and joining fees.

4. **Pensioner with gym + classes**
   - Age: `72`, not a student.
   - Preferences: select **gym anytime** + **classes**.
   - Verify:
     - Pensioner discounts apply to gym and classes (where eligible).
     - Massage and physio remain undiscounted if added.
     - The cheaper gym is recommended and highlighted.

5. **Membership ID access and invalid ID handling**
   - Complete a full signup flow and create a membership.
   - On the **Success** page, copy the membership ID.
   - Go to **Access Membership**, enter:
     - A random invalid ID (e.g. `UG-0000-000000`) → you should see a clear error.
     - Then the valid ID you just copied → you should see the correct membership details.

---

### Future extensions

- Replace the in‑memory membership store with a proper database (e.g. PostgreSQL) using SQLAlchemy models.
- Persist price tables in the database and add an admin interface for editing them.
- Add authentication for staff and members.
- Add automated tests for pricing logic (unit tests around `pricing.calculate_pricing_for_selection`).

