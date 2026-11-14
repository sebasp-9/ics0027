# Secure Password Manager

ICS0027 Web Application Security, TalTech. Sebastian Parra Pinto.

Save website logins in an encrypted vault. Create an account, log in, and
add, view, edit or delete your saved logins.

## Run with Docker

Install and start Docker Desktop with Linux containers. Open a terminal in
this project folder and run:

```sh
docker compose up --build
```

Open **https://127.0.0.1:5000**. Accept the certificate warning for this local
address. The app creates a temporary, self-signed certificate at each start.

Stop with Ctrl+C, then run `docker compose down` if you want to remove the
container. Accounts and logins stay in the `vault-data` volume.
**Adding `--volumes` deletes that saved data.**

Docker includes Python and the database. No MySQL setup is needed.
The app runs as a non-root user and the port is available only on this computer.
Docker build and startup still need verification.

## Run with Python instead

Install [Python 3.12 or newer](https://www.python.org/downloads/).
On Windows, select **Add Python to PATH** during installation.
Run these commands in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

If Linux cannot create the environment, install its `python3-venv` package.
Open **https://127.0.0.1:5000** and accept the local certificate warning.
Stop with Ctrl+C.

SQLite creates `instance/vault.db` automatically. Keep it to keep your data.
Docker uses a separate database in its volume.

## Use it

1. Register with an email and a master password of 12-128 characters.
2. Log in and select **Add a saved login**.
3. Save a title, login name and password (up to 200 characters each).
4. Open an entry to show its password, edit it or delete it.
5. Log out when finished.

Use sample passwords for this course demo. A forgotten master password
cannot be recovered.

## Security

- **Storage:** SQLite stores accounts and encrypted entries. Argon2id hashes
  master passwords and separately derives each user's encryption key.
- **Encryption:** AES-256-GCM encrypts titles, login names and passwords on the
  server. Each save uses a new random nonce (an encryption input).
- **Sessions:** The browser gets a random ID; the key stays in server memory.
  Cookies use Secure, HttpOnly and SameSite=Strict. Login replaces the ID;
  logout removes it. Sessions expire after 15 idle minutes or 8 hours total.
- **Requests:** SQL parameters keep submitted values separate from SQL commands.
  Each entry operation checks its owner. Form tokens protect against CSRF
  (requests made without the user's intent).
- **Pages:** Templates escape saved text to prevent XSS (injected browser code).
  A Content Security Policy blocks scripts. Responses are not cached.

This is a local, single-process demo. Restarting it logs everyone out but keeps
saved entries. The development server and certificate are for local use.
The app encrypts vault records; it has no file-upload feature.

## Tests and progress

After the Python setup, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux, use `.venv/bin/python`. Tests use temporary accounts and a
temporary database. They do not need a running server.

- **Checkpoint 1:** Design completed.
- **Checkpoint 2:** Core app and local HTTPS implemented.
- **Checkpoint 3:** Started. Seven security tests pass. Logging, error-handling
  checks, browser demonstrations and the report draft remain.

See [checkpoint 3 results and next steps](docs/CHECKPOINT3.md).

## Main files

- `app.py`: pages, database queries, validation and sessions.
- `crypto.py`: password hashing and encryption.
- `templates/` and `static/`: page layouts and styles.
- `Dockerfile` and `compose.yaml`: Docker setup.
- `tests/test_security.py`: automated security checks.
- `docs/DESIGN.md`: original design and later implementation notes.
- `docs/PROGRESS.md`: checkpoint 2 progress.
