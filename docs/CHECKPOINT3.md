# Checkpoint 3 progress

14 November 2026. **Started, not complete.** The project brief lists the deadline
as 16 November 2026.

## What changed

Added seven automated security tests and saved their results.
Application behavior is unchanged. We are keeping Flask, SQLite and the current
schema. The Database Basics MySQL project stays separate.

Reviewed the code, templates, Git history through `1b1695f`, setup and existing
notes against Project.pdf sections 4.2 and 4.4.3 and checkpoint 3.txt.
Used the AI context and relevant master PDF chapters; this was a focused review,
not an audit of every slide.

## Run the tests

After the Python setup in the README, run from the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On macOS/Linux, use `.venv/bin/python`. No extra test library is needed.
Tests create and remove a temporary database with fictional accounts.
Importing the app also initializes its normal instance database, but tests
put no accounts or entries there. Run tests separately from the running app.

## Results

**7 tests passed** on 14 November 2026 using Python 3.12 and requirements.txt.
[Full test output](security-test-results.txt).

| Check | Attempt | Result |
|---|---|---|
| Login SQL injection | `' OR 1=1 --`, `alice@example.test' --`, `'; DROP TABLE users; --` | Login denied; accounts unchanged |
| SQL text in entries | `Robert'); DROP TABLE items; --` | Stored and edited as text; normal deletion works |
| Stored XSS | `<script>alert("demo")</script>` in every entry field | Escaped on list/view/edit/reveal pages; CSP header blocks scripts |
| Ownership | Bob tries to read, reveal, edit and delete Alice's entry | All return 404; Alice's entry unchanged |
| CSRF | Missing token or Bob's token on every POST route as Alice | All return 400; accounts and entries unchanged |
| Validation | Empty or 201-character title sent directly | Rejected; no entry created |
| Encryption integrity | Change one encrypted byte | Decryption rejected with 400; no password or traceback shown |

These tests check Flask responses directly. They do not test real TLS connections,
browser script execution or Docker startup. Passing them is evidence for these
cases, not proof that every possible attack is blocked.

## Next steps

1. Add structured logging: event, time, user ID, source address and outcome.
   Never log passwords, keys, tokens, cookies or saved entry contents.
2. Simulate server/database errors and check that users see generic messages.
3. Test session rotation, logout, expiry, cookie flags and malformed requests.
4. Demonstrate attacks in a browser over HTTPS; verify Docker and saved data.
5. Draft the report: Introduction, Implementation, Security Analysis, Conclusion.
6. Review and commit the work before the deadline.

Rate limiting was planned and remains to do. TOTP is optional.

## Explain the protections

- **SQL parameters:** Submitted text is data, separate from SQL commands.
- **Ownership:** Both the entry ID and logged-in user ID must match.
- **XSS:** Templates display saved text safely; CSP also blocks scripts.
- **CSRF:** Each submitted form needs this session's token.
- **Encryption:** The master password derives the key; AES-GCM detects changes.

Course references in the master/AI context: S04 (XSS), S07 (access control),
S08-S09 (SQL injection), S10 (CSRF), S11 (secrets and encryption).
Report requirements: Project.pdf section 1.3.
