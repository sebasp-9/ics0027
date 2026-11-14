# Demonstration guide and verification results

Use sample accounts and passwords only. The server checks below were verified
over real HTTPS on 14 November 2026. Manual browser results are recorded
separately below.

1. Start Docker Desktop, then run `docker compose up --build` in the project
   folder. Open https://127.0.0.1:5000 and accept its local certificate warning.
2. Register Alice and Bob. Use different browser profiles (or a private window)
   so their sessions stay separate. Save an entry as Alice; view, reveal and edit it.
3. Ownership: copy Alice's entry URL into Bob's browser. Expect 404. Try its
   `/edit` URL too. Alice's entry must remain unchanged. Automated tests also
   cover blocked cross-user POST edits, reveals and deletes.
4. XSS: as Alice, save `<script>alert("demo")</script>` as the title. Expect
   literal text, no popup, on the list and entry pages.
5. SQL injection: log out and try email `' OR 1=1 --` with any password.
   Expect the normal failed-login message. Log in normally afterward.
6. CSRF: while logged in, open the add-entry page. In browser developer tools,
   inspect the hidden input named `csrf`, change its value to `wrong`, and
   submit the form. Expect HTTP 400 and no new entry.
7. Logs: watch the terminal. Expect JSON events for the actions and denials,
   without your master password, entry contents or CSRF token.
8. Persistence: stop with Ctrl+C, run `docker compose down`, then
   `docker compose up`. Log in again. Expect the saved entry to remain.
   Do not use `--volumes`, which deletes stored data.
9. Delete the sample entry, then log out. Open its URL again; expect a login redirect.

If a check fails, stop and resolve it before claiming it passed.

## Recorded results - 14 November 2026

Environment: Windows, Docker Desktop Linux containers, Python 3.12-slim image,
local HTTPS at https://127.0.0.1:5000. Tested using Python's HTTP client with
separate cookie jars for Alice and Bob. The client explicitly accepts the local
self-signed certificate; this does not verify a publicly trusted certificate.

| Check | Actual result |
|---|---|
| Docker build/start | PASS: image built and container started |
| HTTPS register/login | PASS: two fictional accounts registered and logged in |
| Create/view/reveal/edit | PASS: entry saved, retrieved, revealed and edited |
| Stored XSS | PASS: script text escaped in returned HTML; restrictive CSP present |
| Ownership | PASS: Bob's read/edit GET and edit/reveal/delete POST all returned 404; owner still had access |
| CSRF | PASS: forged token returned 400 |
| SQL injection | PASS: injection login received normal failed-login message |
| Audit logs | PASS: JSON success/denial events observed; fixed fields contain no submitted credentials or entry contents |
| Persistence | PASS: entry and login worked after compose down/up without deleting volume |
| Delete/logout | PASS: deleted entry returned 404; after logout vault redirected to login |

The HTTPS checks verify responses and CSP headers. They do not execute browser
scripts or assess appearance. See the separate manual results below.
Two fictional test accounts remain in the Docker database; the test entry and
local client state were removed. No existing user data was deleted.

## Repeat the HTTPS check

With Docker running, from the project folder:

```powershell
.\.venv\Scripts\python.exe tests/verify_https.py before
docker compose down
docker compose up -d
.\.venv\Scripts\python.exe tests/verify_https.py after
```

Wait for the server to start before the last command. The first script creates
fictional accounts and saves temporary credentials under ignored `instance/`.
The second checks persistence, deletes its entry, and removes that temporary file.
Never commit `instance/`. Each run creates new sample accounts.

For the lab: show the app, an attack being blocked, test output and Git history.

## Manual browser results

I completed these checks in Brave on 14 November 2026.

| Check | Result |
|---|---|
| Login, create, view, reveal and edit | PASS |
| Stored script title | PASS: literal text appeared on the list and entry pages; no popup |
| Ownership | PASS: the owner could open the entry; a second account saw Not Found for view and edit |
| CSRF | PASS: I changed the add-entry token to `wrong`; submission returned HTTP 400 and created no entry |
| Delete | PASS: the deleted sample entry's URL showed Not Found |
| Logout | PASS: opening /items after logout returned the login page |

The HTTP 404 status for denied ownership requests was separately confirmed by
both automated and live HTTPS tests.
