"""Audit logs and safe errors."""
import json
import sqlite3
from unittest.mock import patch
import test_security as fixtures
import app as vault


class LoggingTests(fixtures.SecurityTests):
    def test_fixed_log_fields_and_no_secrets(self):
        with self.assertLogs('vault.audit', level='INFO') as captured:
            item = self.create('DO-NOT-LOG-TITLE')
            self.post(self.alice, f'/items/{item}/reveal')
            self.get(self.bob, f'/items/{item}')
            self.alice.post('/logout', base_url='https://localhost')
            self.post(self.alice, '/login', email='alice@example.test', password='DO-NOT-LOG-PASSWORD')
            self.post(self.alice, f'/items/{item}/delete')
        events = [json.loads(record.getMessage()) for record in captured.records]
        self.assertTrue({'item_create', 'item_reveal', 'item_access', 'csrf', 'login', 'item_delete'} <=
                        {event['event'] for event in events})
        for event in events:
            self.assertEqual(set(event), {'time', 'event', 'outcome', 'user_id', 'source'})
        for secret in ('DO-NOT-LOG', 'sample-secret', 'alice@example.test', self.token(self.alice)):
            self.assertNotIn(secret, str(events))

    def test_database_failure_is_generic(self):
        with patch('app.database', side_effect=sqlite3.OperationalError('SECRET database path')):
            with self.assertLogs('vault.audit', level='INFO') as captured:
                response = self.get(self.alice, '/items')
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Something went wrong', response.data)
        self.assertNotIn(b'SECRET', response.data)
        self.assertNotIn('SECRET', str(captured.output))
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
