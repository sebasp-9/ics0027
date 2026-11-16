# Security tests and results

Environment: Python 3.12 on Windows. Use fictional accounts and passwords only.

## Run automated tests

After installing `requirements.txt` in a Python virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`. Each test creates disposable accounts in a temporary SQLite database. Result: **14 tests passed** (raw output in `docs/security-test-results.txt`).

Only the account `email` is passed to SQLite as user-supplied text. Account and item IDs (`user_id`, `item_id`) are integers, and saved vault fields (`title`, `username`, `password`) are encrypted with AES-256-GCM before being stored as a binary `BLOB`, so vault text never reaches SQL command parsing.

| Threat | Attack attempted | Mitigation | Result |
|---|---|---|---|
| SQL injection | Submit `' OR 1=1 --`, `alice@example.test' --`, and `'; DROP TABLE users; --` as the login email with a valid master password | Parameterized SQLite queries (`?` placeholders) in `app.py` | Login denied (`200`); `users` table count unchanged |
| Vault-data round-trip | Save, edit, reveal, and delete `Robert'); DROP TABLE items; --` and `' OR 1=1 --` in vault fields | Vault fields are serialized as JSON and encrypted with AES-256-GCM before `INSERT`/`UPDATE` | Stored and displayed as literal text; edit and delete work normally |
| Stored XSS | Save `<script>alert("demo")</script>` in `title`, `username`, and `password` | Jinja2 auto-escaping in all templates and `Content-Security-Policy: ... script-src 'none'` in `app.py` | Rendered as `&lt;script&gt;` across list, view, edit, and reveal pages; CSP header present |
| Cross-user access control (IDOR) | Logged-in user Bob requests Alice's item view/edit pages (`GET`) and reveal/edit/delete routes (`POST`) | `owned_item()` queries `WHERE id = ? AND user_id = ?` and aborts with `404` when no row matches | All cross-user requests return `404`; Alice's entry is unchanged |
| CSRF | Send `POST` requests with a missing token or another user's token to all seven `POST` routes | Per-session random token verified on every `POST` with `hmac.compare_digest` in `load_session()`, plus `SameSite=Strict` cookie | Rejected with `400`; no account or item changes occur |
| Input length and request size | Submit empty or 201-character item fields; send a 40 KB request body | Server-side length checks (`1..200` chars) and `MAX_CONTENT_LENGTH = 32 * 1024` in `app.py` | Invalid fields rejected with form error; oversized body rejected with `413` |
| Ciphertext tampering | Flip one bit of `encrypted_data` in SQLite and request `/reveal` | AES-256-GCM authentication tag verified in `crypto.py` (`decrypt_item`) with `user_id` as associated data | `InvalidTag` caught; returns `400` without plaintext or traceback and logs `decrypt: failed` |
| Session fixation, replay, and expiry | Check session ID on login, replay logged-out cookie, and exceed 15-minute idle or 8-hour total timeout | `new_session()` rotates the session ID on login and clears it on logout; `load_session()` deletes expired sessions | Old, logged-out, and expired cookies redirect (`302`) to `/login` |
| Cookie flags and plain HTTP | Inspect `Set-Cookie` header; send request over `http://` | `Secure`, `HttpOnly`, `SameSite=Strict` set in `protect_response()`; `request.is_secure` checked in `load_session()` | All three cookie flags present; plain HTTP rejected with `400` |
| Unauthenticated vault access | Request `/items`, `/items/new`, `/items/1`, and `/items/1/edit` without logging in | `@login_required` checks `g.vault_session['user_id']` before running vault routes | All four routes redirect (`302`) to `/login` |
| Error handling and structured logging | Trigger normal/denied actions with secret markers, and simulate `sqlite3.OperationalError('SECRET database path')` | `safe_error()` returns a generic `500` page; `audit()` logs only fixed JSON keys (`time`, `event`, `outcome`, `user_id`, `source`) | Generic `500` returned; secret markers, passwords, emails, tokens, and exception text absent from logs |

## Live Docker, HTTPS, and browser checks (recorded 14 November 2026)

On 14 November 2026, I also ran the Docker container and tested the live HTTPS server (`tests/verify_https.py`) and manual flows in Brave:

- Two separate HTTPS clients registered, logged in, created, viewed, revealed, and edited entries, and confirmed that SQL-injection login payloads (`200` with error message), forged CSRF tokens (`400`), and cross-user read/edit/reveal/delete requests (`404`) were rejected.
- Stopping and recreating the container without `--volumes` preserved the SQLite database and saved entries.
- In Brave, `<script>alert("demo")</script>` displayed as literal text with no alert popup, a second account in a private window received `Not Found` (`404`) on the first account's entry URLs, and changing the hidden `csrf` input to `wrong` in developer tools returned `400` without saving an entry.

To repeat the live HTTPS script when Docker is running:

```powershell
.\.venv\Scripts\python.exe tests/verify_https.py before
docker compose down
docker compose up -d
.\.venv\Scripts\python.exe tests/verify_https.py after
```

## Repeat a short browser demonstration

1. Run `docker compose up --build` and open https://127.0.0.1:5000.
2. Register two sample accounts in separate normal and private windows.
3. Create an entry in the first account; view, reveal, and edit it.
4. Save `<script>alert("demo")</script>` as its title and confirm it renders as plain text with no popup.
5. Open that entry's view and `/edit` URLs from the second account's window and confirm both return `Not Found` (`404`).
6. On the new-entry form, inspect the hidden `name="csrf"` input, change its value to `wrong`, and submit. Confirm HTTP `400` is returned and no entry is created.
7. Delete the sample entry, log out, and inspect JSON audit events with `docker compose logs --tail 30`.
