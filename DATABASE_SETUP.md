# Database Setup Guide

This document explains how to set up and use the database for the Gym Membership Advisor application.

## Overview

The application now uses a database to store:
- Gym information (names, joining fees)
- Membership options (gym plans and add-ons with pricing)
- Discount configurations
- Member registrations and memberships

## Database Setup

### 1. Install Dependencies

First, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

This will install Flask-SQLAlchemy and other required packages.

### 2. Initialize the Database

Run the database initialization script to create tables and populate them with initial data:

```bash
python init_db.py
```

This script will:
- Drop any existing tables (if present)
- Create all necessary tables
- Seed the database with gym data, pricing options, and discounts
- Display a summary of the initialized data

### 3. Run the Application

Start the Flask application:

```bash
python app.py
```

The application will automatically connect to the database and load gym data on startup.

## Database Configuration

### Local Development (Default)

By default, the application uses SQLite for local development:
- Database file: `gym_membership.db` (created automatically in the project root)
- No external database server required
- Perfect for development and testing

### Production (MySQL/PostgreSQL)

For production deployment, set the `DATABASE_URL` environment variable:

```bash
# MySQL example
export DATABASE_URL="mysql://username:password@localhost/gym_membership"

# PostgreSQL example
export DATABASE_URL="postgresql://username:password@localhost/gym_membership"
```

## Database Schema

### Tables

1. **gyms** - Stores gym locations
   - gym_key (Primary Key)
   - gym_name
   - joining_fee

2. **membership_option** - Stores gym plans and add-ons
   - id (Primary Key)
   - gym_key (Foreign Key)
   - option_type (enum: 'gym_plan', 'addon')
   - option_key
   - label
   - price (for gym plans)
   - price_with_full_gym_access (for add-ons)
   - price_for_addons_only (for add-ons)
   - discount_allowed

3. **discounts** - Stores discount rates
   - id (Primary Key)
   - discount_type (enum: 'student_Discount', 'pensioner_Discount')
   - gym_key (Foreign Key)
   - rate

4. **members** - Stores member information and memberships
   - id (Primary Key)
   - membership_id (Unique)
   - full_name
   - date_of_birth
   - age
   - is_student
   - is_young_adult
   - is_pensioner
   - chosen_gym (Foreign Key)
   - wants_gym
   - gym_band
   - add_swim, add_classes, add_massage, add_physio
   - monthly_total
   - joining_fee
   - first_payment_total
   - created_at

## Resetting the Database

To reset the database and reload seed data:

```bash
python init_db.py
```

**Warning**: This will delete all existing data, including member registrations!

## Troubleshooting

### "No module named 'flask_sqlalchemy'"

Install the dependencies:
```bash
pip install -r requirements.txt
```

### "RuntimeError: Working outside of application context"

Ensure you're running commands within the Flask application context. The init_db.py script handles this automatically.

### SQLite database is locked

Close any other connections to the database file (e.g., database browsers, other application instances).

## Migration Notes

The application has been migrated from in-memory storage to a persistent database. Key changes:

1. **Data Loading**: Gym and discount data is now loaded from the database instead of static Python dictionaries
2. **Member Storage**: Member data is persisted in the database instead of in-memory dictionary
3. **Backward Compatibility**: The API remains the same - existing templates and routes work without changes

## Adding New Gyms or Modifying Pricing

To add new gyms or modify pricing:

1. Update the `init_db.py` script with the new data
2. Run `python init_db.py` to reset and reload the database
3. Alternatively, use a database management tool to directly modify the data

For production, consider implementing a proper migration system using Flask-Migrate (Alembic).
