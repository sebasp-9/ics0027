# Secure Password Manager

Course project for **ICS0027 Web Application Security** (TalTech).

Author: Sebastian Parra Pinto (255940IVSB)

A web application for storing the logins a user has on other websites. Each user protects their vault with a master password, and every saved login is encrypted before it is stored. The database only contains password hashes, salts and encrypted data, so a stolen copy of it does not reveal any passwords.

The full design (architecture, cryptography, threat model and session model) is in [`docs/DESIGN.md`](docs/DESIGN.md).

## Scope

**Features**
- Registration and login with an email and a master password
- Items: create, view, edit and delete saved logins (title, login name, password)
- All items encrypted with AES-256-GCM, using a key derived from the master password
- Optional two-factor authentication with TOTP codes
- A small JavaScript file for a show/hide password button and a copy button

**Not included:** folders, password history, changing the master password, sharing items, browser extension, account recovery. A forgotten master password cannot be recovered, because the vault key is derived from it.

## Planned routes

| Method | Route | Purpose |
|---|---|---|
| GET, POST | `/register` | Create an account |
| GET, POST | `/login` | Log in with email and master password |
| GET, POST | `/login/mfa` | Enter the TOTP code (only if MFA is turned on) |
| POST | `/logout` | Log out and delete the session |
| GET | `/items` | List the user's items (titles only) |
| GET, POST | `/items/new` | Add an item |
| GET | `/items/<id>` | View an item, with the password hidden |
| POST | `/items/<id>/reveal` | Show the item's password |
| GET, POST | `/items/<id>/edit` | Edit an item |
| POST | `/items/<id>/delete` | Delete an item |
| GET, POST | `/account/mfa` | Turn TOTP on or off (optional feature) |

## Running locally (planned)

The code is added in Checkpoint 2. From then on, the application will be started with these steps. It will need Python 3.12 or newer, and [mkcert](https://github.com/FiloSottile/mkcert) for a local HTTPS certificate.

1. Clone the repository and create a virtual environment: `python -m venv .venv`
2. Install the libraries: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set a random `SECRET_KEY` of at least 32 characters. The `.env` file is never committed.
4. Create a trusted certificate for localhost with `mkcert localhost 127.0.0.1`.
5. Start the application over HTTPS: `flask --app app run --cert <certificate> --key <key>`
6. Open https://localhost:5000

The application will only work over HTTPS, because the session cookie has the `Secure` flag, and it will refuse to start without a proper `SECRET_KEY`.

## Status

| Checkpoint | Status |
|---|---|
| 1: Design document and repository with README | Done |
| 2: Registration, login, sessions, encrypted items | Planned |
| 3: Rate limiting, logging, optional TOTP, tests | Planned |
