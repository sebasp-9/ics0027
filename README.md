# Secure Password Manager

ICS0027 Web Application Security, TalTech. Sebastian Parra Pinto.

A small Flask website for storing encrypted website logins. Register, log in,
then add, view, reveal, edit or delete your own entries.

## Run with Docker

Install and start Docker Desktop with Linux containers. In this folder, run:

```sh
docker compose up --build
```

Open **https://127.0.0.1:5000**. The local, self-signed certificate causes a
browser warning. Check this is your local address before continuing.
Stop with Ctrl+C, then `docker compose down`.

SQLite data stays in the `vault-data` volume. **Adding `--volumes` deletes it.**
Docker includes Python and SQLite.

## Run with Python instead

Install Python 3.12 or newer. On Windows, run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

On macOS/Linux use `python3` to create the environment and `.venv/bin/python`
for the next commands. Open the same HTTPS address. Direct Python execution
stores data in `instance/vault.db`, separate from Docker's database.

## Use and security

- Register with an email and a master password of 12-128 characters.
- Saved title, login name and password must each contain 1-200 characters.
- Argon2id verifies the master password and separately derives the vault key.
  AES-256-GCM encrypts the saved fields on the server.
- Random server-side sessions use secure cookies, rotation and expiry.
- SQL parameters, ownership checks, CSRF tokens, escaped HTML and CSP protect requests.
- JSON audit events appear in the terminal without passwords, keys or tokens.

Use sample passwords only. If you forget the master password, saved entries cannot
be recovered. Restarting the server clears active sessions while keeping saved entries.
This is a local course project; production deployment would need additions such as
a trusted certificate and rate limiting.

## Tests

After the Python setup:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

All 14 automated tests pass (raw output in `docs/security-test-results.txt`).

## Files

- `app.py`: routes, database queries, validation, sessions and logs.
- `crypto.py`: password hashing, key derivation and encryption.
- `templates/` and `static/`: HTML pages and styling. No JavaScript is needed.
- `tests/`: automated security tests and a live HTTPS check.
- [Report](docs/REPORT.pdf) and [editable report text](docs/REPORT.md).
- [Test results and demonstration steps](docs/TEST_RESULTS.md).
