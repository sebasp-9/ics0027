# Secure Password Manager

Course project for **ICS0027 Web Application Security** (TalTech).
Author: Sebastian Parra Pinto.

A small Python website for saving website logins. Each user signs in with an
email and a master password, then adds, views, edits or deletes saved logins.

## Run with Docker (recommended)

Install and start Docker Desktop on Windows or macOS, using Linux containers.
On Linux, use Docker Engine with the Docker Compose plugin. Python and MySQL
do not need to be installed on your computer.

Open a terminal in the project folder and run:

```sh
docker compose up --build
```

The first run downloads Python and installs the libraries inside the image.
Open **https://127.0.0.1:5000**. The temporary, self-signed certificate causes a
browser warning: use Advanced to continue for this local address.

Stop with Ctrl+C. To remove the stopped container:

```sh
docker compose down
```

Saved accounts and logins stay in the named Docker volume `vault-data`.
Running the app again uses the same data. Do not add `--volumes` to the down
command unless you intend to delete the saved data. Docker uses its own
database; it does not import an existing local `instance/vault.db`.

The Dockerfile defines the Python environment. Compose builds that image,
connects the HTTPS port to your computer and keeps the database in a volume.
Only this computer can access the published port. The app runs as a non-root
user inside the container.

Submit the project folder (or repository), including `Dockerfile`,
`compose.yaml` and the application files. The Dockerfile needs these files to
build the application.

## Run directly with Python (alternative)

Install **Python 3.12 or newer** with pip from https://www.python.org/downloads/.
On Windows, select **Add Python to PATH** during installation.

Open a terminal in the project folder.

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

If Linux reports that venv is missing, install your distribution's Python venv
package first (on Ubuntu/Debian: `sudo apt install python3-venv`).

Open **https://127.0.0.1:5000**. The server creates a temporary, self-signed TLS
certificate automatically. Your browser will show a certificate warning.
Use its Advanced option to continue **for this local development address**.
A new certificate is generated each time the server starts.

No MySQL, database account, .env file or secret key setup is needed. SQLite
creates `instance/vault.db` automatically. Keep this file to keep your accounts
and saved logins. Stop the server with Ctrl+C.

## Try the core flows

1. Create an account with an email and a master password of 12–128 characters.
2. Log in and select **Add a saved login**.
3. Enter a title, login name and password, then save.
4. Open the saved login. Use **Show password**, **Hide password**, or **Edit login**.
5. To delete it, tick the confirmation box and select **Delete login**.
6. Log out when finished.

A forgotten master password cannot be recovered. Use sample passwords for this
course demonstration.

## How it works

- **Flask** handles the pages and forms.
- **SQLite** stores the accounts and encrypted saved logins in one file.
  Python's built-in `sqlite3` library uses SQL parameters for user input.
- **Argon2id** hashes master passwords. A separate random salt derives each
  user's vault key from their master password.
- **AES-256-GCM** encrypts the title, login name and password together on the
  server, using a new random nonce each time. Decryption happens on the server
  when an authorised user opens their vault.
- The browser receives only a random session ID. The vault key stays in server
  memory. Cookies use Secure, HttpOnly and SameSite=Strict.
- Login replaces the session ID. Logout removes the old session and its key.
  Access expires after 15 idle minutes or 8 hours in total. Expired session
  records are removed on the next request.
- Forms have CSRF tokens. Every item lookup checks the signed-in owner.
  HTML output is escaped, and sensitive responses are not cached.

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Python environment and app startup |
| `compose.yaml` | One-command Docker startup and persistent database |
| `.dockerignore` | Excludes local data and unrelated files from builds |
| `app.py` | Routes, SQLite queries, validation and sessions |
| `crypto.py` | Password hashing, key derivation and encryption |
| `templates/` | Simple HTML pages |
| `static/style.css` | Basic page styling |
| `docs/DESIGN.md` | Original design and checkpoint 2 implementation notes |
| `docs/PROGRESS.md` | Short checkpoint 2 progress note |

## Status and limits

| Checkpoint | Status |
|---|---|
| 1: Design document and README | Done |
| 2: Basic web interface, authentication, encrypted vault and development TLS | Implemented |
| 3: Rate limiting, logging, optional TOTP and a permanent test suite | Planned; not included here |

This is a local, single-process development application. Restarting it logs
everyone out, while saved items stay in SQLite. The built-in development server
and temporary certificate are for the course demonstration, not public hosting.

The checkpoint sheet says “file encryption” under the password-manager heading.
Here that is implemented as encryption/decryption of vault records stored in the
SQLite file. There is no arbitrary file-upload feature.
