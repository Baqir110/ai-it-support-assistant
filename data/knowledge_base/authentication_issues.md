# Authentication and Login Issues

## Symptoms

- "Incorrect username or password" on a known-correct password
- Account locked out after repeated attempts
- MFA/2FA code not accepted
- Password reset email never arrives

## Initial Troubleshooting

1. Verify Caps Lock and keyboard layout are correct.
2. Confirm the account is not locked (check with IT admin console).
3. Try the password reset flow from a different browser/incognito window.
4. Clear cached credentials (Windows Credential Manager / browser saved
   passwords) if login silently fails.

## MFA / 2FA Issues

1. Confirm device time is synced (drift causes TOTP codes to fail).
2. Regenerate backup codes if the authenticator app was reinstalled.
3. Check whether the MFA provider is reporting an outage.

## Account Lockout Policy

Accounts lock after 5 failed attempts within 15 minutes and auto-unlock
after 30 minutes, or can be unlocked immediately by an administrator.

## When to Escalate

Escalate to identity/security team if lockout persists after admin unlock,
if MFA reset is required, or if there is suspicion of credential compromise
(logins from unfamiliar locations).
