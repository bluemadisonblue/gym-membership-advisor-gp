"""
Email utilities for sending verification emails and managing tokens.
"""

import os
import secrets
from datetime import datetime, timedelta
from flask import url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail with the app."""
    # Email configuration
    # For development, we'll use console output or configure with environment variables
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 8025))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@gymmembership.com')
    
    mail.init_app(app)
    return mail


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def generate_timed_token(app, email):
    """Generate a time-sensitive token for email verification using itsdangerous."""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification')


def verify_timed_token(app, token, max_age=3600):
    """
    Verify a time-sensitive token.
    
    Args:
        app: Flask application instance
        token: The token to verify
        max_age: Maximum age of token in seconds (default 1 hour)
    
    Returns:
        Email address if valid, None if invalid or expired
    """
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification', max_age=max_age)
        return email
    except:
        return None


def send_verification_email(app, member, verification_url):
    """
    Send verification email to a member.
    
    Args:
        app: Flask application instance
        member: Member model instance
        verification_url: Full URL for email verification
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        msg = Message(
            subject='Verify Your Email - Gym Membership',
            recipients=[member.email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Plain text version
        msg.body = f"""
Hello {member.full_name},

Thank you for signing up for a gym membership!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 1 hour.

If you did not create this account, please ignore this email.

Best regards,
Gym Membership Team
"""
        
        # HTML version
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to Gym Membership!</h1>
    </div>
    <div class="content">
        <p>Hello <strong>{member.full_name}</strong>,</p>
        
        <p>Thank you for signing up for a gym membership! We're excited to have you join us.</p>
        
        <p>To complete your registration and proceed with payment, please verify your email address:</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="button">Verify Email Address</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #4CAF50;">{verification_url}</p>
        
        <p><strong>Note:</strong> This verification link will expire in 1 hour.</p>
        
        <p>If you did not create this account, please ignore this email.</p>
    </div>
    <div class="footer">
        <p>Best regards,<br>Gym Membership Team</p>
    </div>
</body>
</html>
"""
        
        # In development mode, print email to console
        if app.config['MAIL_SERVER'] == 'localhost' and app.config['MAIL_PORT'] == 8025:
            print("\n" + "="*80)
            print("EMAIL VERIFICATION (Development Mode)")
            print("="*80)
            print(f"To: {member.email}")
            print(f"Subject: {msg.subject}")
            print(f"\nVerification URL: {verification_url}")
            print("="*80 + "\n")
            # Don't actually send in dev mode if mail server not configured
            return True
        else:
            mail.send(msg)
            return True
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_resend_verification_email(app, member, verification_url):
    """
    Send a resend verification email to a member.
    Same as send_verification_email but with different subject line.
    """
    try:
        msg = Message(
            subject='Resend: Verify Your Email - Gym Membership',
            recipients=[member.email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.body = f"""
Hello {member.full_name},

You requested to resend your email verification link.

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Best regards,
Gym Membership Team
"""
        
        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Email Verification</h1>
    </div>
    <div class="content">
        <p>Hello <strong>{member.full_name}</strong>,</p>
        
        <p>You requested to resend your email verification link.</p>
        
        <p>Please click the button below to verify your email address:</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="button">Verify Email Address</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #4CAF50;">{verification_url}</p>
        
        <p><strong>Note:</strong> This verification link will expire in 1 hour.</p>
        
        <p>If you did not request this, please ignore this email.</p>
    </div>
    <div class="footer">
        <p>Best regards,<br>Gym Membership Team</p>
    </div>
</body>
</html>
"""
        
        # In development mode, print email to console
        if app.config['MAIL_SERVER'] == 'localhost' and app.config['MAIL_PORT'] == 8025:
            print("\n" + "="*80)
            print("RESEND EMAIL VERIFICATION (Development Mode)")
            print("="*80)
            print(f"To: {member.email}")
            print(f"Subject: {msg.subject}")
            print(f"\nVerification URL: {verification_url}")
            print("="*80 + "\n")
            return True
        else:
            mail.send(msg)
            return True
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
