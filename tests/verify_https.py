"""Real HTTPS smoke checks. Run: python tests/verify_https.py before|after.
Creates fictional accounts in the Docker database. State stays in ignored instance/.
The local self-signed development certificate is explicitly accepted by this client.
"""
import http.cookiejar
import json
import re
import secrets
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://127.0.0.1:5000'
STATE = Path('instance/https-check.json')


def client():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))


def request(c, path, data=None):
    try:
        response = c.open(BASE + path, None if data is None else urllib.parse.urlencode(data).encode())
    except urllib.error.HTTPError as error:
        response = error
    return response.status, response.read().decode(), response.headers


def post(c, path, **data):
    _, page, _ = request(c, '/login')
    token = re.search(r'name="csrf" value="([^"]+)"', page).group(1)
    return request(c, path, {'csrf': token, **data})


def login(c, email, password):
    status, page, _ = post(c, '/login', email=email, password=password)
    assert status == 200 and 'My vault' in page


if sys.argv[1] == 'before':
    tag = secrets.token_hex(5)
    password = secrets.token_urlsafe(24)
    alice, bob = client(), client()
    emails = [f'https-{name}-{tag}@example.test' for name in ('alice', 'bob')]
    for c, email in zip((alice, bob), emails):
        assert post(c, '/register', email=email, password=password)[0] == 200
        login(c, email, password)
    print('PASS HTTPS registration and login for two fictional accounts')
    payload = '<script>alert("demo")</script>'
    status, page, _ = post(alice, '/items/new', title=payload, username='demo', password='fixture-password')
    assert status == 200 and '&lt;script&gt;' in page and '<script>' not in page
    item = re.search(r'href="/items/(\d+)"', page).group(1)
    for path in (f'/items/{item}', f'/items/{item}/edit'):
        status, page, headers = request(alice, path)
        assert status == 200 and '&lt;script&gt;' in page and '<script>' not in page
        assert "script-src 'none'" in headers['Content-Security-Policy']
    assert 'fixture-password' in post(alice, f'/items/{item}/reveal')[1]
    print('PASS stored XSS escaping/CSP and password reveal over HTTPS')
    for path in (f'/items/{item}', f'/items/{item}/edit'):
        assert request(bob, path)[0] == 404
    for action in ('edit', 'reveal', 'delete'):
        assert post(bob, f'/items/{item}/{action}', title='changed', username='x', password='x')[0] == 404
    assert request(alice, f'/items/{item}')[0] == 200
    print('PASS cross-user read/reveal/edit/delete denied; owner entry unchanged')
    assert request(alice, '/items/new', {'csrf': 'wrong', 'title': 'forged'})[0] == 400
    print('PASS forged CSRF token rejected with HTTP 400')
    attacker = client()
    status, page, _ = post(attacker, '/login', email="' OR 1=1 --", password='wrong')
    assert status == 200 and 'Incorrect email or master password.' in page
    print('PASS SQL injection login denied')
    assert post(alice, f'/items/{item}/edit', title='Persistence sample', username='demo', password='fixture-password')[0] == 200
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({'email': emails[0], 'password': password, 'item': item}))
    print('PASS edit; fixture saved for restart verification (state ignored by Git)')
else:
    state = json.loads(STATE.read_text())
    c = client()
    login(c, state['email'], state['password'])
    assert 'Persistence sample' in request(c, f"/items/{state['item']}")[1]
    print('PASS login and saved entry survive container removal/recreation')
    assert post(c, f"/items/{state['item']}/delete")[0] == 200
    assert request(c, f"/items/{state['item']}")[0] == 404
    post(c, '/logout')
    assert 'Log in' in request(c, '/items')[1]
    STATE.unlink()
    print('PASS delete and logout; temporary client state removed')
