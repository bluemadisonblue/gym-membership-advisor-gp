# Email Verification Guide

This document explains the email verification feature added to the Gym Membership Advisor application.

## Overview

Email verification has been integrated into the membership signup flow to ensure that users provide valid email addresses and can receive important communications about their membership.

## How It Works

### 1. Signup Process

When a user signs up, they now provide:
- Full Name
- **Email Address** (new field)
- Date of Birth
- Student Status

The email address is validated for basic format (contains @ and domain with .).

### 2. Payment & Membership Creation

After completing the signup, preferences, and payment steps:
1. A membership is created in the database
2. The email is marked as **unverified** initially
3. A secure, time-limited verification token is generated
4. A verification email is sent to the provided address

### 3. Email Verification

The user receives an email with:
- A personalized greeting
- A verification link (valid for 1 hour)
- Instructions on what to do next

When the user clicks the verification link:
- The token is validated
- If valid, the email is marked as verified
- The user is shown a success page
- They can now access their membership details

### 4. Resending Verification

If the user doesn't receive the email or the link expires:
- Visit `/resend-verification`
- Enter their email address
- A new verification link is sent

## Technical Implementation

### Database Changes

**New fields in `members` table:**
- `email` (String, unique, indexed, required)
- `email_verified` (Boolean, default False)
- `verification_token` (String, unique, nullable)
- `verification_sent_at` (DateTime, nullable)

### New Routes

**1. `/verify-email/<token>` (GET)**
- Validates the verification token
- Marks email as verified if valid
- Shows success page or error message

**2. `/resend-verification` (GET, POST)**
- GET: Shows form to enter email
- POST: Sends new verification email if account exists

### Email Configuration

Configured via environment variables:

```bash
# Email Server Settings
MAIL_SERVER=smtp.gmail.com          # SMTP server
MAIL_PORT=587                        # SMTP port
MAIL_USE_TLS=true                    # Use TLS
MAIL_USE_SSL=false                   # Use SSL
MAIL_USERNAME=your-email@gmail.com   # SMTP username
MAIL_PASSWORD=your-app-password      # SMTP password
MAIL_DEFAULT_SENDER=noreply@gym.com  # From address
```

### Development Mode

In development (when `MAIL_SERVER=localhost` and `MAIL_PORT=8025`):
- Emails are printed to the console instead of being sent
- The verification URL is displayed for testing
- No actual email server is required

### Security Features

1. **Time-Limited Tokens**: Verification links expire after 1 hour
2. **Secure Token Generation**: Uses `itsdangerous` for tamper-proof tokens
3. **Email Privacy**: Resend verification doesn't reveal if email exists
4. **Unique Emails**: Database enforces email uniqueness

## User Flow

```
┌─────────────┐
│   Signup    │
│ (with email)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Preferences │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Recommendation│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Confirm     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Payment    │
└──────┬───────┘
       │
       ├──> Membership Created
       │
       └──> Verification Email Sent
            │
            ▼
       ┌────────────────┐
       │ User Checks    │
       │     Email      │
       └────────┬───────┘
                │
                ▼
       ┌────────────────┐
       │ Clicks Link    │
       └────────┬───────┘
                │
                ▼
       ┌────────────────┐
       │ Email Verified │
       └────────┬───────┘
                │
                ▼
       ┌────────────────┐
       │ Access         │
       │ Membership     │
       └────────────────┘
```

## Testing

### Manual Testing (Development Mode)

1. **Start the application:**
   ```bash
   python3 app.py
   ```

2. **Sign up with test email:**
   - Go to http://localhost:5000/signup
   - Fill in details with a test email
   - Complete the signup flow

3. **Check console output:**
   - The verification URL will be printed to console
   - Copy the URL and paste in browser

4. **Verify email:**
   - Click the verification link
   - See success message

### Testing Expiration

To test token expiration, modify the `max_age` parameter in `verify_email()` route temporarily:

```python
email = verify_timed_token(app, token, max_age=10)  # 10 seconds for testing
```

### Testing Production Email

For production testing with real emails:

1. **Configure environment variables:**
   ```bash
   export MAIL_SERVER=smtp.gmail.com
   export MAIL_PORT=587
   export MAIL_USE_TLS=true
   export MAIL_USERNAME=your-email@gmail.com
   export MAIL_PASSWORD=your-app-password
   ```

2. **For Gmail, generate an App Password:**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this as `MAIL_PASSWORD`

3. **Restart the application** and test with real email

## Email Templates

### Verification Email

**Subject:** "Verify Your Email - Gym Membership"

**Content:**
- Welcoming message with user's name
- Clear call-to-action button
- Plain text alternative
- Expiration warning (1 hour)
- Security note (ignore if not you)

### Resend Verification Email

**Subject:** "Resend: Verify Your Email - Gym Membership"

**Content:**
- Acknowledgment of resend request
- New verification link
- Same structure as initial email

## Troubleshooting

### Emails not being sent

1. **Check environment variables** are set correctly
2. **Verify SMTP credentials** are valid
3. **Check firewall** allows outbound connections on SMTP port
4. **Review console logs** for error messages

### Verification link expired

1. Use **"Resend Verification"** feature
2. Links expire after 1 hour for security

### Email marked as spam

1. Configure **SPF/DKIM** records for your domain
2. Use a **reputable SMTP provider**
3. Advise users to check spam folder

### Database errors

If you get unique constraint errors:
```bash
python3 init_db.py  # Reinitialize database
```

## API Reference

### Email Utility Functions

**`send_verification_email(app, member, verification_url)`**
- Sends verification email to member
- Returns True if successful, False otherwise

**`generate_timed_token(app, email)`**
- Generates secure, time-limited token
- Returns token string

**`verify_timed_token(app, token, max_age=3600)`**
- Verifies and decodes token
- Returns email if valid, None if invalid/expired

## Future Enhancements

Potential improvements to consider:

1. **Email Templates System**: Use template engine for emails
2. **Customizable Expiration**: Admin-configurable token lifetime
3. **Email Resend Throttling**: Limit resend requests to prevent abuse
4. **Welcome Email**: Send welcome email after verification
5. **Email Preferences**: Allow users to manage email notifications
6. **Multi-language Support**: Localized verification emails

## Security Best Practices

1. **Never log tokens** in production
2. **Use HTTPS** for verification links in production
3. **Implement rate limiting** on resend endpoint
4. **Monitor for abuse** patterns
5. **Keep SECRET_KEY secure** and rotated regularly
6. **Use environment variables** for all sensitive configuration

## Support

For issues or questions:
1. Check application logs
2. Verify configuration
3. Test with development mode first
4. Review this documentation
5. Check error messages in flash notifications
