# Security tests and results

Verified 14 November 2026. Environment: Python 3.12, Docker Desktop Linux
containers and Brave on Windows. Use fictional accounts and passwords only.

## Run automated tests

After installing requirements.txt in a Python virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`. Tests use disposable accounts and a
temporary SQLite database. Result: **28 passing executions covering 14 distinct
checks**; shared checks repeat in the extended suites. Full output is in
`security-test-results.txt`.

| Check | Attempt | Recorded result |
|---|---|---|
| Login SQL injection | `' OR 1=1 --`, `alice@example.test' --`, `'; DROP TABLE users; --` | Login denied; users table unchanged |
| SQL text in entries | `Robert'); DROP TABLE items; --` | Treated as text; create/edit/delete still work |
| Stored XSS | `<script>alert("demo")</script>` in saved fields | Escaped in list/view/edit/reveal responses; CSP blocks scripts |
| Ownership | Bob requests Alice's view/edit pages and reveal/edit/delete actions | All HTTP checks returned 404; original entry unchanged |
| CSRF | Missing and foreign tokens on every POST route | 400; no unintended data change |
| Validation | Empty/201-character title; oversized body | Invalid entries rejected; oversized body returned 413 |
| Ciphertext tampering | Change one ciphertext byte | 400; no decrypted password or traceback |
| Session rotation/logout | Reuse old or logged-out session ID | Redirect to login |
| Session expiry | Exceed idle or absolute time limit | Redirect to login; expired session removed |
| Cookies/HTTP | Inspect flags; request plain HTTP | Secure, HttpOnly, SameSite=Strict; HTTP rejected |
| Anonymous access | Open protected routes without login | Redirect to login |
| Audit logs | Trigger actions/denials with secret markers | Fixed JSON fields; markers absent |
| Unexpected error | Simulate a database failure | Generic 500 and a safe audit event |

The row groups summarize the tests rather than defining their execution count.
These checks support the listed cases, not every possible attack.

## Live Docker and HTTPS results

The image built and started. Two independent HTTPS clients registered and logged
in, created/viewed/revealed/edited entries, and confirmed SQL injection and forged
CSRF rejection. Cross-account read/edit/reveal/delete requests returned 404.
The saved entry and account survived container removal/recreation without deleting
the volume. Deletion and logout passed. JSON audit events were inspected.

The test client explicitly accepts the local self-signed certificate. It does not
establish public certificate trust. Temporary client credentials were removed;
fictional accounts remain in the local Docker database.

To repeat those checks with Docker running:

```powershell
.\.venv\Scripts\python.exe tests/verify_https.py before
docker compose down
docker compose up -d
.\.venv\Scripts\python.exe tests/verify_https.py after
```

Wait until the server starts before the last command. These scripts create sample
accounts; their temporary state stays under ignored `instance/`. Never commit it.

## Manual Brave results

I completed these checks on 14 November 2026:

- Register, login, create, view, reveal and edit: PASS.
- Save the script title: PASS. Literal text on the list and entry pages, no popup.
- Second account in a private window: PASS. Not Found for the first account's
  view and edit URLs; the owner still opened the same entry.
- Change the add-entry CSRF token to `wrong`: PASS. HTTP 400 with the expired-form
  message; no new entry appeared.
- Delete the test entry: PASS. Its URL then showed Not Found.
- Logout: PASS. Opening /items returned the login page.

## Repeat a short browser demonstration

1. Run `docker compose up --build` and open https://127.0.0.1:5000.
2. Register two sample accounts in separate normal/private windows.
3. Create an entry in the first account; view, reveal and edit it.
4. Save `<script>alert("demo")</script>` as its title. Expect literal text, no popup.
5. Open that entry's URL as the second account. Expect Not Found; repeat with `/edit`.
6. For CSRF, fill a new-entry form. Right-click **Save login**, choose **Inspect**,
   and find the hidden `name="csrf"` input in that form. Change only its value to
   `wrong`, press Enter and submit. Expect HTTP 400 and no new entry.
7. Delete only your sample entry and log out. Confirm the entry is gone and /items
   returns the login page. Check JSON events using `docker compose logs --tail 30`.

Known limits: no rate limiting or MFA, single-process sessions, development TLS
certificate and no durable log retention. The report explains these limits.
