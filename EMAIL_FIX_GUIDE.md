# Fix Email Verification on Production

## Problem
The verification emails are not being sent because the email server is not configured for production.

## Solution

You have two options:

### Option 1: Use Gmail SMTP (Recommended for small sites)

1. **Create a Gmail App Password:**
   - Go to your Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the generated 16-character password

2. **Set Environment Variables in Vercel:**

   Go to your Vercel project dashboard → Settings → Environment Variables and add:

   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USE_SSL=false
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password-here
   MAIL_DEFAULT_SENDER=noreply@gymmship.tech
   ```

3. **Redeploy your application**

### Option 2: Use SendGrid (Recommended for production)

1. **Create SendGrid Account:**
   - Go to https://sendgrid.com/
   - Sign up for free account (100 emails/day free)
   - Create an API key

2. **Set Environment Variables in Vercel:**

   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USE_SSL=false
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=your-sendgrid-api-key-here
   MAIL_DEFAULT_SENDER=noreply@gymmship.tech
   ```

3. **Redeploy your application**

### Option 3: Use Mailgun (Alternative)

1. **Create Mailgun Account:**
   - Go to https://www.mailgun.com/
   - Sign up and verify your domain
   - Get your SMTP credentials

2. **Set Environment Variables:**

   ```
   MAIL_SERVER=smtp.mailgun.org
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=postmaster@your-domain.com
   MAIL_PASSWORD=your-mailgun-password
   MAIL_DEFAULT_SENDER=noreply@gymmship.tech
   ```

## How to Set Environment Variables in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. Click "Settings" tab
4. Click "Environment Variables" in the left sidebar
5. Add each variable one by one
6. Click "Save"
7. Redeploy your application

## Alternative: Quick Fix Without SMTP

If you want a quick temporary fix, I can modify the code to show the verification link on the success page instead of sending email:

**Edit `templates/success.html`:**

Add this section after line 35:

```html
<!-- Verification Link Display -->
<div class="rounded-xl bg-blue-50 border-2 border-blue-200 p-5 mt-4">
    <div class="flex items-start gap-3">
        <svg class="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
        </svg>
        <div class="flex-1">
            <p class="text-sm font-bold text-blue-900 mb-2">Verify Your Email</p>
            <p class="text-sm text-blue-800 mb-2">
                Click this link to verify your email:
            </p>
            <a href="{{ verification_url }}" class="text-sm text-blue-600 font-semibold break-all hover:underline">
                {{ verification_url }}
            </a>
        </div>
    </div>
</div>
```

**But you also need to pass the URL to the template. Edit `app.py` around line 300:**

Find the success route and modify it to pass the verification URL.

## Testing After Fix

1. Sign up on https://www.gymmship.tech/
2. Complete the payment flow
3. Check your email inbox (and spam folder)
4. You should receive a verification email

## Still Not Working?

Check the Vercel logs:
1. Go to Vercel dashboard
2. Click your project
3. Click "View Function Logs"
4. Look for any email-related errors

Common issues:
- Wrong SMTP credentials
- Port blocked by firewall
- TLS/SSL configuration mismatch
- Gmail blocking "less secure apps" (use App Passwords!)

## Need Help?

If you're still having issues, check the logs and let me know what error message you see!
