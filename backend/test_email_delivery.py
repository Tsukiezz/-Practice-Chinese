"""Transport regression tests with no real credentials or network requests."""
import io
import json
import os
import smtplib
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from email_service import EmailDeliveryError, get_email_config, send_verification_email


class EmailDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'VERCEL':'1', 'BREVO_API_KEY':'xkeysib-api-current',
            'SMTP_PASSWORD':'xsmtpsib-smtp-separate',
            'SMTP_HOST':'smtp-relay.brevo.com', 'SMTP_USERNAME':'login@example.com',
            'SMTP_FROM':'HanziGo <sender@example.com>',
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_api_uses_dedicated_key_even_when_smtp_password_is_set(self):
        response = MagicMock()
        response.__enter__.return_value.status = 201
        with patch('email_service.urllib.request.urlopen', return_value=response) as send:
            self.assertTrue(send_verification_email('learner@example.com', '123456', 'forgot_password'))
        request = send.call_args.args[0]
        self.assertEqual(request.get_header('Api-key'), 'xkeysib-api-current')
        self.assertNotIn('xsmtpsib-smtp-separate', json.dumps(dict(request.header_items())))
        self.assertNotIn('123456', json.loads(request.data)['subject'])

    def test_unconfigured_development_does_not_log_or_report_delivery(self):
        with patch.dict(os.environ, {}, clear=True), patch('email_service.smtp_is_configured', return_value=False):
            with self.assertLogs('hanzigo.email', level='WARNING') as logs, patch('builtins.print') as console:
                self.assertFalse(send_verification_email('learner@example.com', '123456'))
        self.assertNotIn('123456', ' '.join(logs.output))
        console.assert_not_called()

    def test_legacy_api_key_in_smtp_variable_is_still_supported(self):
        os.environ.pop('BREVO_API_KEY')
        os.environ['SMTP_PASSWORD'] = 'xkeysib-legacy'
        cfg = get_email_config()
        self.assertEqual(cfg['api_key'], 'xkeysib-legacy')
        self.assertEqual(cfg['password'], '')
        self.assertEqual(cfg['transport'], 'brevo_api')

    def test_smtp_auth_failure_does_not_send_smtp_key_to_rest_api(self):
        os.environ.pop('BREVO_API_KEY')
        with patch('email_service._send_via_smtp', side_effect=smtplib.SMTPAuthenticationError(535, b'bad login')):
            with patch('email_service._send_via_brevo_api') as api:
                with self.assertRaises(EmailDeliveryError) as raised:
                    send_verification_email('learner@example.com', '123456')
        self.assertEqual(raised.exception.reason, 'authentication_failed')
        api.assert_not_called()

    def test_smtp_key_in_api_variable_is_reported_as_configuration_error(self):
        os.environ['BREVO_API_KEY'] = 'xsmtpsib-wrong-product'
        with patch('email_service.urllib.request.urlopen') as network:
            with self.assertRaises(EmailDeliveryError) as raised:
                send_verification_email('learner@example.com', '123456')
        self.assertEqual(raised.exception.reason, 'smtp_key_in_api_variable')
        network.assert_not_called()

    def _provider_failure(self, code, message, http_status=401):
        body = io.BytesIO(json.dumps({'code':code,'message':message}).encode())
        error = urllib.error.HTTPError('https://api.brevo.com/v3/smtp/email', http_status, 'rejected', {}, body)
        with patch('email_service.urllib.request.urlopen', side_effect=error):
            with self.assertRaises(EmailDeliveryError) as raised:
                send_verification_email('learner@example.com', '123456')
        return raised.exception

    def test_blocked_ip_is_distinguished_from_invalid_key_without_logging_secrets(self):
        error = self._provider_failure('unauthorized',
            'We have detected an unrecognised IP address 192.0.2.45. xkeysib-secret-value OTP 123456')
        self.assertEqual(error.reason, 'ip_not_authorized')
        self.assertEqual(error.source_ip, '192.0.2.45')
        self.assertNotIn('secret-value', str(error))
        self.assertNotIn('123456', str(error))

    def test_invalid_key_and_unknown_provider_codes_are_safe(self):
        error = self._provider_failure('xkeysib-secret-in-code', 'Key not found')
        self.assertEqual(error.reason, 'invalid_api_key')
        self.assertEqual(error.code, 'unknown')
        self.assertNotIn('secret-in-code', str(error))


if __name__ == '__main__':
    unittest.main()
