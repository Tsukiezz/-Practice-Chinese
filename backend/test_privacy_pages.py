import unittest
from fastapi.testclient import TestClient
from main import app


class PrivacyPagesTests(unittest.TestCase):
    def test_public_pages_without_login(self):
        client = TestClient(app)
        for path, title in [('/privacy-policy', 'Chính sách quyền riêng tư'),
                            ('/data-deletion', 'Hướng dẫn yêu cầu xóa dữ liệu')]:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('text/html', response.headers['content-type'])
                self.assertIn(title, response.text)
                self.assertIn('nguyenvovinhnguyen@gmail.com', response.text)
                self.assertIn('name="viewport"', response.text)
                self.assertNotIn('<script', response.text)
                self.assertIn('Content-Security-Policy', response.headers)


if __name__ == '__main__':
    unittest.main()
