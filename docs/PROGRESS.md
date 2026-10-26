# Checkpoint 2 progress

Implemented a basic running password manager using Python, Flask and SQLite.

- Web interface: register, log in, log out, and add/view/edit/delete saved logins.
- Server-side encryption: AES-256-GCM protects the title, login name and password.
  Argon2id derives the vault key from the master password with a separate salt.
- Authentication: Argon2id password hashes, random server-side sessions, secure
  cookie flags, session rotation, expiry and logout. CSRF tokens and ownership
  checks protect the core flows.
- Development TLS: `python app.py` starts HTTPS with a temporary self-signed
  certificate. The README explains the local browser warning.
- Clean-machine setup: three commands after installing Python; SQLite creates
  the database automatically.
- Changes are recorded in separate commits for backend, web pages and documentation.

Validation used Python 3.12 and a newly created virtual environment. Checks
covered registration, duplicate accounts, incorrect login, all item operations,
hidden/revealed passwords, HTML escaping, CSRF rejection, owner isolation,
encrypted database contents, fresh nonces, tampering detection, cookie flags,
session rotation, logout and both session expiry limits. A real HTTPS request also returned the login page and a Secure cookie.

The checkpoint sheet repeats “file encryption” for both project choices. For
this password manager, saved login records in the database file are encrypted
and decrypted; arbitrary file uploads are not implemented.

Kept for checkpoint 3: rate limiting, audit logging, optional TOTP and a permanent
automated test suite. The current application is a local development demo.
