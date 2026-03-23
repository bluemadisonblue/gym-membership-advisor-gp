# Database Overview

The app uses **SQLite** stored locally in `instance/gym_membership.db`.

---

## Storage

| Item | Value |
|------|-------|
| **Engine** | SQLAlchemy |
| **File** | `instance/gym_membership.db` |
| **Override** | `DATABASE_URL` environment variable |

---

## Tables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              gyms                                            │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ gym_key (PK)        │ varchar(20)  - "ugym" or "power_zone"                  │
│ gym_name            │ varchar(50)  - Display name                            │
│ joining_fee         │ numeric      - One-time joining fee                    │
└─────────────────────┴───────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         membership_option                                    │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ id (PK)             │ integer      - Auto-increment                          │
│ gym_key (FK)        │ → gyms.gym_key                                         │
│ option_type         │ enum         - 'gym_plan' or 'addon'                   │
│ option_key          │ varchar(30)  - super_off_peak, off_peak, anytime,      │
│                     │               swim, classes, massage, physio           │
│ label               │ varchar(120) - Display label                           │
│ price               │ numeric      - For gym plans                           │
│ price_with_full_gym │ numeric      - Addon price when member has gym         │
│ price_for_addons_only│ numeric     - Addon price without gym                 │
│ discount_allowed    │ boolean      - Can student/pensioner discount apply?   │
└─────────────────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             discounts                                        │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ id (PK)             │ integer      - Auto-increment                          │
│ discount_type       │ enum         - 'student_Discount' or 'pensioner_Discount'│
│ gym_key (FK)        │ → gyms.gym_key                                         │
│ rate                │ numeric      - e.g. 0.20 for 20%                       │
└─────────────────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             members                                          │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ id (PK)             │ integer      - Auto-increment                          │
│ membership_id       │ varchar(25)  - e.g. UG-2026-000001, unique             │
│ full_name           │ varchar(100)                                           │
│ email               │ varchar(120) - unique                                  │
│ password_hash       │ varchar(255)                                           │
│ email_verified      │ boolean                                                │
│ chosen_gym (FK)     │ → gyms.gym_key                                         │
│ wants_gym           │ boolean                                                │
│ gym_band            │ varchar(30)  - super_off_peak, off_peak, anytime       │
│ add_swim            │ boolean                                                │
│ add_classes         │ boolean                                                │
│ add_massage         │ boolean                                                │
│ add_physio          │ boolean                                                │
│ monthly_total       │ numeric                                                │
│ joining_fee         │ numeric                                                │
│ first_payment_total │ numeric                                                │
│ created_at          │ datetime                                               │
│ ...                 │ (age, is_student, is_young_adult, is_pensioner, etc.)  │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

## Flow

### 1. App startup

- `initialize_database_if_needed()` runs on first request
- Creates tables if missing
- Seeds gyms, membership options, and discounts if empty

### 2. Request handling

- `load_data()` runs on every request
- Loads gyms, discounts, and addon rules from DB into `data.GYMS` and `data.DISCOUNTS`
- Used by `pricing.py` for calculations

### 3. User signup → member

1. User fills signup and preferences forms
2. On payment, a new row is inserted into `members` with:
   - `membership_id` (e.g. `UG-2026-000001`)
   - Personal data and chosen plan
   - Hashed password
3. User is logged in via session (`user_id`)

### 4. User login

- Member is looked up by `email`
- Password checked with `check_password_hash`
- Session stores `user_id` for authorization

---

## File Roles

| File | Role |
|------|------|
| `models.py` | SQLAlchemy models: `Gym`, `MembershipOption`, `Discount`, `Member` |
| `data.py` | Loads gyms/discounts from DB into `GYMS`, `DISCOUNTS` dicts used by pricing |
| `init_db.py` | Manual init: drop all, create all, seed (run `python3 init_db.py`) |
| `app.py` | Configures DB, auto-init, seeds if empty |

---

## Useful Commands

```bash
# Manual full reset (drops all data)
python3 init_db.py

# Inspect DB with SQLite
sqlite3 instance/gym_membership.db
.tables
.schema members
```
