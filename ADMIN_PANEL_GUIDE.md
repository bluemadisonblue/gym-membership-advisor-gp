# Admin Panel Guide

## Overview

A comprehensive admin panel has been added for developers to manage all system data, monitor activities, and maintain the database.

## Access

**URL:** `/admin` or `/admin/login`

**Default Credentials (Development):**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change these credentials in production!

## Setting Custom Credentials

### Option 1: Environment Variables

```bash
export ADMIN_USERNAME="your_username"
export ADMIN_PASSWORD_HASH="your_hash_here"
```

### Option 2: Generate Password Hash

```bash
python3 -c "from admin_auth import generate_admin_password_hash; generate_admin_password_hash('YourSecurePassword123!')"
```

This will output a hash to set as `ADMIN_PASSWORD_HASH`.

## Features

### 1. Dashboard (`/admin`)
- **Total Members** - Count of all registered members
- **Verified Members** - Members with verified emails
- **Unverified Members** - Pending email verification
- **Monthly Revenue** - Total recurring revenue
- **Recent Members** - Last 5 registered members
- **Members by Gym** - Distribution across gyms
- **Quick Actions** - Links to key functions

### 2. Members Management (`/admin/members`)
- **List all members** with pagination (20 per page)
- **Search** by name, email, or membership ID
- **Filter** by gym or verification status
- **View details** - Click any member to see full profile
- **Delete members** - With CSRF protection
- **Manually verify** - Force email verification

### 3. Member Detail (`/admin/members/<id>`)
- Complete member information
- Membership details
- Pricing breakdown
- Email verification status
- Actions: Verify email, Delete member

### 4. Gyms Management (`/admin/gyms`)
- List all gyms
- View membership options
- See pricing for each gym
- Discount configurations

### 5. Database Info (`/admin/database`)
- All tables and row counts
- Column information
- Database schema overview
- System statistics

## Security Features

### Authentication
- Password-based login
- Session management
- Automatic logout on browser close

### Authorization
- `@require_admin` decorator protects all admin routes
- Redirects to login if not authenticated
- Flash messages for feedback

### CSRF Protection
- All forms include CSRF tokens
- Tokens verified on submission
- Prevents cross-site request forgery

### Activity Logging
- All admin actions are logged
- Includes: username, IP address, timestamp, action
- Logs: LOGIN, LOGOUT, DELETE_MEMBER, VERIFY_MEMBER

### Example Log Entry:
```
[2026-02-10T12:34:56] ADMIN: admin (192.168.1.1) - DELETE_MEMBER - Deleted member: UG-2026-000123
```

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/admin/login` | GET, POST | Admin login page |
| `/admin/logout` | GET | Logout and clear session |
| `/admin` | GET | Dashboard with statistics |
| `/admin/members` | GET | List all members (paginated) |
| `/admin/members/<id>` | GET | View member details |
| `/admin/members/<id>/delete` | POST | Delete a member |
| `/admin/members/<id>/verify` | POST | Verify member email |
| `/admin/gyms` | GET | Manage gyms and pricing |
| `/admin/database` | GET | Database information |

## Usage Examples

### Searching Members

1. Go to `/admin/members`
2. Enter search term (name, email, or ID)
3. Results update automatically

### Filtering Members

1. Go to `/admin/members`
2. Select gym from dropdown
3. Select verification status
4. Click "Apply Filters"

### Manually Verifying Email

1. Go to `/admin/members/<id>`
2. Click "Verify Email" button
3. Confirmation required
4. Member email marked as verified

### Deleting a Member

1. Go to `/admin/members/<id>`
2. Click "Delete Member" button
3. Confirmation required
4. Member permanently removed

## Production Deployment

### 1. Change Default Credentials

```bash
# Generate new password hash
python3 -c "from admin_auth import generate_admin_password_hash; generate_admin_password_hash('YourStrongPassword!')"

# Set environment variables
export ADMIN_USERNAME="youradmin"
export ADMIN_PASSWORD_HASH="generated_hash_here"
```

### 2. Enable HTTPS

Admin panel should ONLY be accessed over HTTPS in production.

### 3. IP Whitelist (Recommended)

Add IP restriction in your web server config:

**Nginx:**
```nginx
location /admin {
    allow 192.168.1.0/24;  # Your office network
    deny all;
    proxy_pass http://your_app;
}
```

**Apache:**
```apache
<Location /admin>
    Require ip 192.168.1.0/24
</Location>
```

### 4. Rate Limiting

Implement rate limiting on `/admin/login` to prevent brute force:

```python
# Using Flask-Limiter
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def admin_login():
    # ... existing code
```

### 5. Two-Factor Authentication (Future)

Consider adding 2FA for production:
- Google Authenticator
- SMS verification
- Email verification codes

## Troubleshooting

### Can't Login

1. Check credentials are correct
2. Verify environment variables are set
3. Check if session cookies are enabled
4. Clear browser cache and cookies

### "Admin access required" Error

- Session expired - login again
- Cookies disabled - enable in browser
- Multiple tabs - logout and login again

### CSRF Token Invalid

- Session expired - refresh page
- Cookies blocked - enable cookies
- Form timeout - resubmit form

### No Members Showing

- Database may be empty - create test members
- Pagination issue - check page number in URL
- Search filters active - clear filters

## Development Tips

### Adding New Admin Routes

```python
@app.route("/admin/new-feature")
@require_admin
def admin_new_feature():
    log_admin_action("ACCESS_NEW_FEATURE", "Description")
    # Your code here
    return render_template("admin/new_feature.html")
```

### Adding CSRF to Forms

```html
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <!-- form fields -->
</form>
```

```python
if not verify_csrf_token(request.form.get("csrf_token", "")):
    flash("Invalid security token.", "error")
    return redirect(...)
```

### Logging Custom Actions

```python
from admin_auth import log_admin_action

log_admin_action("CUSTOM_ACTION", "Details about what happened")
```

## API for External Tools

The admin panel is web-based, but you can create API endpoints:

```python
@app.route("/api/admin/stats")
@require_admin
def api_admin_stats():
    stats = {
        'members': Member.query.count(),
        'verified': Member.query.filter_by(email_verified=True).count()
    }
    return jsonify(stats)
```

## Future Enhancements

Potential improvements:
- Export members to CSV/Excel
- Bulk email sending
- Advanced analytics dashboard
- Audit log viewer in UI
- Member activity timeline
- Revenue charts and graphs
- Automated reports
- Email template editor
- Discount code management
- Payment tracking integration

## Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Check admin action logs
4. Verify database connection
5. Test with default credentials first

## Security Checklist

Before going to production:

- [ ] Changed default admin password
- [ ] Set strong ADMIN_PASSWORD_HASH
- [ ] Enabled HTTPS only
- [ ] Added IP whitelist
- [ ] Enabled rate limiting
- [ ] Removed development credentials message
- [ ] Set up audit log monitoring
- [ ] Tested all admin functions
- [ ] Backed up database
- [ ] Documented custom changes

---

**Remember:** The admin panel provides full access to all data. Protect it carefully!
