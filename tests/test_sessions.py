"""Session lifecycle and request limits."""
import time
import test_security as fixtures
import app as vault


class SessionTests(fixtures.SecurityTests):
    def test_login_rotates_id_and_logout_blocks_replay(self):
        client = vault.app.test_client()
        self.get(client, '/login')
        old = client.get_cookie(vault.COOKIE).value
        self.post(client, '/login', email='alice@example.test', password='Example master password!')
        current = client.get_cookie(vault.COOKIE).value
        self.assertNotEqual(old, current)
        self.assertNotIn(old, vault.sessions)
        self.post(client, '/logout')
        self.assertNotIn(current, vault.sessions)
        client.set_cookie(vault.COOKIE, current)
        self.assertEqual(self.get(client, '/items').status_code, 302)

    def test_idle_and_absolute_expiry(self):
        for field, age in (('last_seen', vault.IDLE_SECONDS), ('created', vault.TOTAL_SECONDS)):
            self.post(self.alice, '/login', email='alice@example.test', password='Example master password!')
            sid = self.alice.get_cookie(vault.COOKIE).value
            vault.sessions[sid][field] = time.time() - age - 1
            self.assertEqual(self.get(self.alice, '/items').status_code, 302)
            self.assertNotIn(sid, vault.sessions)

    def test_cookie_flags_and_http_rejection(self):
        response = self.get(self.alice, '/items')
        cookie = response.headers['Set-Cookie']
        for flag in ('Secure', 'HttpOnly', 'SameSite=Strict'):
            self.assertIn(flag, cookie)
        self.assertEqual(self.alice.get('/login', base_url='http://localhost').status_code, 400)

    def test_oversized_request_rejected(self):
        response = self.alice.post('/items/new', data={'title': 'x' * 40000}, base_url='https://localhost')
        self.assertEqual(response.status_code, 413)

    def test_anonymous_item_access_redirects(self):
        client = vault.app.test_client()
        for path in ('/items', '/items/new', '/items/1', '/items/1/edit'):
            self.assertEqual(self.get(client, path).status_code, 302)
