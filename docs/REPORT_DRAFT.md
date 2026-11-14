# Secure Password Manager - report draft

ICS0027 Web Application Security. Sebastian Parra Pinto.
Prepared 14 November 2026. Checkpoint 3 draft.

## Introduction

This project is a small website for storing website logins. Users register with
an email and master password, then create, view, edit and delete their own entries.
The goal is to apply encryption, authentication, access control and protection
against common web attacks. Flask and SQLite keep the implementation small.

## Implementation

Flask renders HTML forms. SQLite stores users and encrypted entries. Each entry
has a foreign key linking it to its owner. SQL uses placeholders and separate
values, rather than inserting user input into SQL command text.

Argon2id hashes master passwords for login verification. A separate random salt
is used to derive a 256-bit vault key from the master password. AES-GCM encrypts
the title, login name and password together with a fresh 12-byte random nonce.
The owner ID is authenticated with the encrypted data. The key is kept in server
memory during a session, not stored in SQLite. Encryption and decryption happen
on the server; HTTPS protects the browser connection.

The browser holds a random session ID. Login replaces that ID; logout removes
its session. Sessions expire after 15 idle minutes or 8 hours total. Cookies use
Secure, HttpOnly and SameSite=Strict. Restarting the single-process server clears
sessions. Saved entries remain in the database.

Every POST form checks a session-bound CSRF token. Every entry operation uses
the logged-in user ID; submitted owner fields cannot choose another user.
Templates escape output, and the Content Security Policy blocks scripts and
framing. The server validates input lengths and limits request bodies to 32 KiB.

Audit events are JSON records written to the terminal (Docker captures these
as container logs). Records contain UTC time, event, outcome, user ID when known
and source address. Events cover login, logout, item actions, ownership denial,
CSRF rejection, decryption failure and unexpected server errors. Submitted text,
keys, passwords, cookies, tokens and exception messages are not included.
Unexpected errors return a generic message with HTTP 500. Expected request
errors keep their HTTP status. Debug mode is disabled.

## Security Analysis

Tests use fictional accounts and temporary databases. See security-test-results.txt
for actual output and CHECKPOINT3.md for payloads and results. All 28 test
executions passed; these cover 14 distinct checks because the extended suites
also repeat the seven original checks.

| Threat | Defence | Evidence |
|---|---|---|
| SQL injection | Parameterized queries | Login injection denied; SQL-like entry text stays data |
| Stored XSS | HTML escaping and restrictive CSP | Script text escaped on list, view, edit and reveal pages |
| Cross-user access | Owner condition on lookups and writes | Bob cannot read, reveal, edit or delete Alice's entry |
| CSRF | Token checked against server-side session | Missing and another session's tokens rejected on all POST routes |
| Changed ciphertext | AES-GCM authentication | Modified ciphertext rejected without plaintext |
| Session reuse | Rotation, server-side logout and expiry | Old and expired sessions cannot open the vault |
| Browser validation bypass | Server checks and body-size limit | Invalid lengths rejected; oversized requests return 413 |
| Error or log leakage | Generic error and fixed audit fields | Simulated database failure reveals no exception text; secret markers absent from audit events |

Additional live checks built and ran the Docker image and exercised the app over
real HTTPS with two independent cookie jars. Registration, login, entry actions,
SQL injection rejection, forged-CSRF rejection and owner isolation passed.
The encrypted entry survived removing and recreating the container with its volume
retained. JSON audit events were inspected. DEMO.md records these results and
the repeatable HTTPS script.

Test coverage: automated XSS checks verify escaped HTML and CSP headers.
Manual checks in Brave on 14 November 2026 also passed: normal entry actions,
literal script text without a popup, cross-user view/edit denial, rejection of a
changed CSRF token with HTTP 400 and no inserted entry, deletion and logout.
I performed these browser checks and recorded the results in DEMO.md. The HTTPS client accepts the local self-signed certificate;
it does not establish public certificate trust. The server sees plaintext while processing
entries, so a compromised running server can expose active vaults. Emails and
entry ownership/counts are not encrypted. There is no account recovery, rate
limiting or MFA. Rate limiting was planned but deferred; online guessing remains
a limitation. MFA is optional in the brief. This is a local course demo, not a
public hosting setup. JSON audit logging is checked; durable log retention is
outside the current local setup.

## Conclusion

The implementation connects safe SQL queries, owner checks, form protection,
safe page rendering and encrypted storage in one small application. Tests show
that these controls work for the recorded cases. Docker and real HTTPS checks
also passed, together with the guided Brave checks recorded in DEMO.md.

### Learning and challenges

This project illustrates why login and ownership are separate checks: Bob can
log in successfully but must still be denied access to Alice's entries. It also
shows why browser field limits are insufficient and why SQL parameters keep
submitted text separate from executable commands.

A practical challenge was keeping the project small enough to explain. I kept
SQLite and the existing two-table schema rather than importing the separate
Database Basics MySQL model. Another challenge was distinguishing implemented
controls from evidence: the first tests called Flask directly, so a separate
HTTPS check was needed to verify the running Docker app and persistence.

Windows test cleanup initially failed because a SQLite context manager commits
or rolls back but does not close its connection. Explicit connection closing
fixed the temporary-file cleanup. A separate live HTTPS test verified Docker
startup, access controls and data persistence across container recreation.
Automated response checks and manual browser checks provide different evidence,
so their results are recorded separately.

## References

- ICS0027 Project.pdf: sections 1.3, 4.2 and 4.4.3.
- Web Application Security course master: S04 (XSS), S07 (access control), S08-S09 (SQL
  injection), S10 (CSRF), S11 (encryption and sessions).
- Repository: app.py, crypto.py and tests/. These are the implementation and evidence.
