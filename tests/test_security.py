"""Security checks on disposable accounts and a temporary SQLite database."""
from contextlib import closing
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
import app as vault


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = vault.app.config['DATABASE']
        vault.app.config.update(TESTING=True, DATABASE=str(Path(self.temp.name) / 'test.db'))
        vault.sessions.clear()
        vault.init_database()
        self.alice, self.bob = vault.app.test_client(), vault.app.test_client()
        for client, email in ((self.alice, 'alice@example.test'), (self.bob, 'bob@example.test')):
            for path in ('/register', '/login'):
                self.assertEqual(self.post(client, path, email=email,
                    password='Example master password!').status_code, 302)

    def tearDown(self):
        vault.sessions.clear()
        vault.app.config.update(TESTING=False, DATABASE=self.original)
        self.temp.cleanup()

    def get(self, client, path):
        return client.get(path, base_url='https://localhost')

    def token(self, client):
        page = self.get(client, '/login').get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', page).group(1)

    def post(self, client, path, **fields):
        return client.post(path, data={'csrf': self.token(client), **fields},
                           base_url='https://localhost')

    def create(self, title='Example login'):
        self.assertEqual(self.post(self.alice, '/items/new', title=title,
            username='sample-user', password='sample-secret').status_code, 302)
        with closing(sqlite3.connect(vault.app.config['DATABASE'])) as db:
            return db.execute('SELECT max(id) FROM items').fetchone()[0]

    def test_sql_injection_cannot_log_in(self):
        client = vault.app.test_client()
        for payload in ("' OR 1=1 --", "alice@example.test' --", "'; DROP TABLE users; --"):
            with self.subTest(payload=payload):
                response = self.post(client, '/login', email=payload, password='wrong password')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Incorrect email or master password.', response.data)
                self.assertEqual(self.get(client, '/items').status_code, 302)
        with closing(sqlite3.connect(vault.app.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0], 2)

    def test_sql_payload_round_trips_as_item_data(self):
        payload = "Robert'); DROP TABLE items; --"
        item = self.create(payload)
        self.assertIn(b'DROP TABLE items;', self.get(self.alice, f'/items/{item}').data)
        self.assertEqual(self.post(self.alice, f'/items/{item}/edit', title=payload,
            username="' OR 1=1 --", password='still-data').status_code, 302)
        self.assertIn(b'still-data', self.post(self.alice, f'/items/{item}/reveal').data)
        self.assertEqual(self.post(self.alice, f'/items/{item}/delete').status_code, 302)
        self.assertEqual(self.get(self.alice, f'/items/{item}').status_code, 404)

    def test_stored_xss_is_escaped(self):
        payload = '<script>alert("demo")</script>'
        item = self.create(payload)
        self.post(self.alice, f'/items/{item}/edit', title=payload, username=payload, password=payload)
        responses = [self.get(self.alice, path) for path in
                     ('/items', f'/items/{item}', f'/items/{item}/edit')]
        responses.append(self.post(self.alice, f'/items/{item}/reveal'))
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'<script>', response.data)
            self.assertIn(b'&lt;script&gt;', response.data)
            self.assertIn("script-src 'none'", response.headers['Content-Security-Policy'])

    def test_other_user_cannot_read_reveal_edit_or_delete(self):
        item = self.create('Alice private title')
        for path in (f'/items/{item}', f'/items/{item}/edit'):
            self.assertEqual(self.get(self.bob, path).status_code, 404)
        for action in ('reveal', 'edit', 'delete'):
            response = self.post(self.bob, f'/items/{item}/{action}', title='stolen',
                                 username='attacker', password='attacker')
            self.assertEqual(response.status_code, 404)
            self.assertNotIn(b'Alice private title', response.data)
        self.assertNotIn(b'Alice private title', self.get(self.bob, '/items').data)
        self.assertIn(b'Alice private title', self.get(self.alice, f'/items/{item}').data)

    def test_missing_and_foreign_csrf_tokens_rejected(self):
        item = self.create()
        for path in ('/register', '/login', '/logout', '/items/new',
                     f'/items/{item}/edit', f'/items/{item}/reveal', f'/items/{item}/delete'):
            for token in (None, self.token(self.bob)):
                with self.subTest(path=path, missing=token is None):
                    data = {} if token is None else {'csrf': token}
                    response = self.alice.post(path, data=data, base_url='https://localhost')
                    self.assertEqual(response.status_code, 400)
        self.assertEqual(self.get(self.alice, f'/items/{item}').status_code, 200)
        with closing(sqlite3.connect(vault.app.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM items').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0], 2)

    def test_server_enforces_length_limits(self):
        for title in ('', 'x' * 201):
            response = self.post(self.alice, '/items/new', title=title,
                                 username='sample', password='sample')
            self.assertIn(b'Fill in all three fields', response.data)
        with closing(sqlite3.connect(vault.app.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM items').fetchone()[0], 0)

    def test_ciphertext_tampering_fails(self):
        item = self.create()
        with closing(sqlite3.connect(vault.app.config['DATABASE'])) as db:
            encrypted = db.execute('SELECT encrypted_data FROM items WHERE id = ?', (item,)).fetchone()[0]
            self.assertNotIn(b'sample-secret', encrypted)
            db.execute('UPDATE items SET encrypted_data = ? WHERE id = ?',
                       (bytes([encrypted[0] ^ 1]) + encrypted[1:], item))
            db.commit()
        response = self.post(self.alice, f'/items/{item}/reveal')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(b'sample-secret', response.data)
        self.assertNotIn(b'Traceback', response.data)


if __name__ == '__main__':
    unittest.main()

