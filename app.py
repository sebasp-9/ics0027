"""A small, single-process password manager for local HTTPS development."""
import hmac
import os
import secrets
import sqlite3
import time
from functools import wraps
from pathlib import Path

from argon2.exceptions import VerificationError
from cryptography.exceptions import InvalidTag
from flask import Flask, abort, g, redirect, render_template, request, url_for

from crypto import decrypt_item, derive_key, encrypt_item, password_hasher

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
Path(app.instance_path).mkdir(exist_ok=True)
app.config['DATABASE'] = str(Path(app.instance_path) / 'vault.db')

# Only random IDs go in cookies. Keys and CSRF tokens stay in server memory.
sessions = {}
COOKIE = 'vault_session'
IDLE_SECONDS = 15 * 60
TOTAL_SECONDS = 8 * 60 * 60
# Unknown-email and wrong-password failures both perform password verification.
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def database():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_database(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_database():
    with app.app_context():
        database().executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                kdf_salt BLOB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                nonce BLOB NOT NULL,
                encrypted_data BLOB NOT NULL
            );
        ''')


def new_session(user_id=None, key=None):
    sessions.pop(getattr(g, 'session_id', None), None)
    g.session_id = secrets.token_urlsafe(32)
    now = time.time()
    g.vault_session = {'user_id': user_id, 'key': key,
                       'csrf': secrets.token_urlsafe(32),
                       'created': now, 'last_seen': now}
    sessions[g.session_id] = g.vault_session


@app.before_request
def load_session():
    if not request.is_secure:
        abort(400, 'Please open this application using HTTPS.')
    now = time.time()
    # Remove expired keys even when their owners do not make another request.
    for sid, entry in list(sessions.items()):
        if (now - entry['last_seen'] >= IDLE_SECONDS or
                now - entry['created'] >= TOTAL_SECONDS):
            sessions.pop(sid, None)
    g.session_id = request.cookies.get(COOKIE)
    g.vault_session = sessions.get(g.session_id)
    if g.vault_session is None:
        new_session()
    g.vault_session['last_seen'] = now
    if request.method == 'POST':
        token = request.form.get('csrf', '')
        if not hmac.compare_digest(token.encode(), g.vault_session['csrf'].encode()):
            abort(400, 'This form expired. Reload the page and try again.')


@app.after_request
def protect_response(response):
    if hasattr(g, 'vault_session'):
        response.set_cookie(COOKIE, g.session_id, secure=True, httponly=True,
                            samesite='Strict', max_age=TOTAL_SECONDS)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'none'; style-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@app.context_processor
def template_session():
    return {'csrf': g.vault_session['csrf'],
            'logged_in': g.vault_session['user_id'] is not None}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.vault_session['user_id'] is None:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def index():
    return redirect(url_for('items'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if (not 3 <= len(email) <= 254 or email.count('@') != 1 or
                any(char.isspace() for char in email) or
                not all(email.split('@'))):
            error = 'Enter a valid email address.'
        elif not 12 <= len(password) <= 128:
            error = 'Use a master password between 12 and 128 characters.'
        else:
            try:
                database().execute(
                    'INSERT INTO users (email, password_hash, kdf_salt) VALUES (?, ?, ?)',
                    (email, password_hasher.hash(password), os.urandom(16)))
                database().commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = 'An account with this email already exists.'
    return render_template('auth.html', registering=True, error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = database().execute('SELECT * FROM users WHERE email = ?',
                                  (email,)).fetchone()
        valid = False
        if 1 <= len(password) <= 128 and len(email) <= 254:
            try:
                password_hasher.verify(user['password_hash'] if user else dummy_hash,
                                       password)
                valid = user is not None
            except VerificationError:
                pass
        if valid:
            new_session(user['id'], derive_key(password, user['kdf_salt']))
            return redirect(url_for('items'))
        error = 'Incorrect email or master password.'
    return render_template('auth.html', registering=False, error=error)


@app.post('/logout')
def logout():
    new_session()
    return redirect(url_for('login'))


def read_item(row):
    try:
        return decrypt_item(g.vault_session['key'], g.vault_session['user_id'], row)
    except InvalidTag:
        abort(400, 'This item could not be decrypted. Its stored data may be damaged.')


def owned_item(item_id):
    row = database().execute('SELECT * FROM items WHERE id = ? AND user_id = ?',
                              (item_id, g.vault_session['user_id'])).fetchone()
    if row is None:
        abort(404)
    return row


@app.get('/items')
@login_required
def items():
    rows = database().execute('SELECT * FROM items WHERE user_id = ? ORDER BY id',
                               (g.vault_session['user_id'],)).fetchall()
    titles = [{'id': row['id'], 'title': read_item(row)['title']} for row in rows]
    return render_template('items.html', items=titles)


@app.route('/items/new', methods=['GET', 'POST'])
@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id=None):
    fields = read_item(owned_item(item_id)) if item_id is not None else {}
    error = None
    if request.method == 'POST':
        fields = {name: request.form.get(name, '') for name in ('title', 'username', 'password')}
        if not all(1 <= len(value) <= 200 for value in fields.values()):
            error = 'Fill in all three fields, using at most 200 characters each.'
        else:
            user_id = g.vault_session['user_id']
            nonce, encrypted = encrypt_item(g.vault_session['key'], user_id, fields)
            if item_id is None:
                database().execute('INSERT INTO items (user_id, nonce, encrypted_data) VALUES (?, ?, ?)',
                                   (user_id, nonce, encrypted))
            else:
                database().execute('UPDATE items SET nonce = ?, encrypted_data = ? WHERE id = ? AND user_id = ?',
                                   (nonce, encrypted, item_id, user_id))
            database().commit()
            return redirect(url_for('items'))
    return render_template('edit.html', fields=fields, error=error, editing=item_id is not None)


@app.get('/items/<int:item_id>')
@app.post('/items/<int:item_id>/reveal')
@login_required
def view_item(item_id):
    fields = read_item(owned_item(item_id))
    return render_template('view.html', fields=fields, item_id=item_id,
                           revealed=request.method == 'POST')


@app.post('/items/<int:item_id>/delete')
@login_required
def delete_item(item_id):
    owned_item(item_id)
    database().execute('DELETE FROM items WHERE id = ? AND user_id = ?',
                       (item_id, g.vault_session['user_id']))
    database().commit()
    return redirect(url_for('items'))


init_database()

if __name__ == '__main__':
    # Temporary self-signed certificate; never enable the interactive debugger.
    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=5000, ssl_context='adhoc', debug=False,
            threaded=False)
