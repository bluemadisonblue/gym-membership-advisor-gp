## IY470 Gym Membership Advisor (uGym & Power Zone)

A modern Flask web application for the IY470 Web Programming group project.  
It compares two gyms, **uGym** and **Power Zone**, and recommends the cheapest option
for a user based on their age, student status, and selected facilities.

All data is stored in memory (no database yet) and the code has been organized so that
it is easy to plug in SQLAlchemy models later.

---

### ✨ Features

- **Two gyms**: uGym and Power Zone, each with joining fees and different price tables.
- **Age restrictions**: users under 16 cannot sign up.
- **Smart discount rules**:
  - Students and young adults (age \< 25):
    - uGym: 20% discount
    - Power Zone: 15% discount
  - Pensioners (age \> 66):
    - uGym: 15% discount
    - Power Zone: 20% discount
  - Discounts never apply to massage therapy or physiotherapy.
- **Guided membership flow**:
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
- **Modern UI/UX**:
  - Tailwind CSS framework for responsive, mobile-first design
  - Step indicator for multi-page signup flow
  - Smooth animations and transitions
  - Image gallery showcasing gym facilities
  - Embedded video preview on preferences page
  - Premium form inputs with clear validation
  - Toast notifications for user feedback
  - Accessible design with semantic HTML

---

### 📁 Project structure

```
webdev group project/
├── app.py                          # Flask application, routes, and session management
├── data.py                         # Static gym data, pricing tables, and discount constants
├── pricing.py                      # Pricing calculation logic using decimal.Decimal
├── README.md                       # This file
├── templates/
│   ├── base.html                  # Base layout with navigation, step indicator, and flash messages
│   ├── home.html                  # Landing page with hero section, image gallery, and features
│   ├── signup.html                # Step 1: Personal details form (name, age, student status)
│   ├── preferences.html           # Step 2: Membership preferences with embedded video preview
│   ├── recommendation.html        # Step 3: Side-by-side pricing comparison and recommendation
│   ├── confirm.html               # Step 4: Final review with detailed pricing breakdown
│   ├── pay.html                   # Step 5: Simulated payment page
│   ├── success.html               # Success page with copyable membership ID
│   ├── access.html                # Form to retrieve membership by ID
│   └── membership_details.html    # Detailed view of stored membership
└── static/
    ├── styles.css                 # Custom CSS animations and utilities
    ├── images/
    │   ├── 1.jpg                  # Gym facility image (desktop/laptop view)
    │   ├── 2.jpg                  # Mobile app mockup
    │   ├── 3.jpg                  # Gym equipment/products
    │   └── 4.jpg                  # Additional gym experience photo
    └── videos/
        └── swimming pool.mp4      # Swimming pool facilities video
```

---

### 📋 Requirements

- **Python 3.9+** (Python 3.10+ recommended)
- **Flask** (installed via `pip`)
- **Tailwind CSS** (loaded via CDN, no installation required)

No other third‑party libraries or build tools are required.

---

### 🚀 How to run

1. **Clone the repository**

   ```bash
   git clone git@github.com:bluemadisonblue/gym-membership-advisor-gp.git
   cd gym-membership-advisor-gp
   ```

2. **Create and activate a virtual environment (recommended)**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Flask**

   ```bash
   pip install Flask
   ```

4. **Run the app**

   ```bash
   python3 app.py
   ```

5. **Open in browser**

   Visit `http://127.0.0.1:5000/` in your browser.

   **Note**: Make sure to include the port number (`:5000`) in the URL.

---

### 🔧 Implementation notes

- **No database**:
  - Memberships are stored in a global in‑memory dict in `app.py` keyed by `membership_id`.
  - Restarting the server clears all memberships.
  - Data persists only for the duration of the server process.

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

- **Frontend**:
  - Tailwind CSS loaded via CDN for rapid UI development.
  - Custom CSS animations in `static/styles.css` for fade-in effects and hover states.
  - Vanilla JavaScript for interactive features (clipboard copy, form validation, video controls).
  - Fully responsive design tested on mobile, tablet, and desktop viewports.

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

### 🎯 Future extensions

- **Database integration**:
  - Replace the in‑memory membership store with a proper database (e.g. PostgreSQL) using SQLAlchemy models.
  - Persist price tables in the database and add an admin interface for editing them.

- **Authentication & authorization**:
  - Add user authentication for members and staff.
  - Implement role-based access control (member vs. admin).

- **Testing**:
  - Add automated unit tests for pricing logic (around `pricing.calculate_pricing_for_selection`).
  - Add integration tests for the full signup flow.
  - Add end-to-end tests using Selenium or Playwright.

- **Enhanced features**:
  - Email confirmation on membership creation.
  - PDF generation for membership cards.
  - Payment integration with Stripe or PayPal.
  - Member dashboard with usage statistics.
  - Admin panel for managing memberships and pricing.

- **Performance**:
  - Optimize image loading (lazy loading, WebP format).
  - Consider using Git LFS for video files.
  - Add caching for static assets.

---

### 📝 Recent Updates

**January 2026**:
- ✅ Added Tailwind CSS for modern UI/UX design
- ✅ Implemented step indicator for signup flow
- ✅ Added image gallery to homepage with 4 gym photos
- ✅ Embedded swimming pool video on preferences page
- ✅ Enhanced all pages with animations and smooth transitions
- ✅ Improved pricing breakdown tables with better visual hierarchy
- ✅ Added clipboard copy functionality for membership IDs
- ✅ Redesigned all forms with premium styling
- ✅ Improved accessibility and mobile responsiveness

---

### 👥 Contributing

This is a group project for IY470 Web Programming. To contribute:

1. **Clone the repository**
2. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```
4. **Push to GitHub**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create a Pull Request** on GitHub for review

---

### 📄 License

This project is for educational purposes as part of the IY470 Web Programming course.

