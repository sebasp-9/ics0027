# Checkpoint 3 progress

14 November 2026. **Started, not complete.** The project brief lists the deadline
as 16 November 2026.

## What changed

Added seven automated security tests and saved their results.
Application behavior is unchanged. We are keeping Flask, SQLite and the current
schema. The Database Basics MySQL project stays separate.

Reviewed the code, templates, Git history through `1b1695f`, setup and existing
notes against Project.pdf sections 4.2 and 4.4.3 and checkpoint 3.txt.
Reviewed the relevant course master PDF chapters; this was a focused review,
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

## New prepared work

- JSON audit logging and generic unexpected-error messages implemented.
- Session rotation, logout replay, both expiry limits, cookie flags, HTTP rejection,
  anonymous access, oversized input, log fields and simulated errors tested.
- 28 executions passed (14 distinct checks; inherited checks repeat).
- [Report draft](REPORT_DRAFT.md) and [manual demo steps](DEMO.md) prepared.

## Current status

Docker build, real HTTPS attack checks and persistence passed on 14 November.
Guided manual checks in Brave also passed: entry actions, XSS, ownership,
CSRF rejection with no saved entry, delete and logout. See DEMO.md.

The code, tests and verified results are ready for checkpoint 3. Final report
formatting and the submission package are the next project tasks. Rate limiting is a documented limitation.
