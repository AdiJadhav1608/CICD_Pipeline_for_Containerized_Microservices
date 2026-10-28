import unittest
from app import app


class CatalogServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_catalog_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["service"], "catalog-service")
        self.assertGreaterEqual(len(response.get_json()["products"]), 1)


if __name__ == "__main__":
    unittest.main()
