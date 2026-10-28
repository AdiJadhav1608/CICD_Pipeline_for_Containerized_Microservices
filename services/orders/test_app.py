import unittest
from app import app


class OrdersServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_orders_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["service"], "orders-service")
        self.assertGreaterEqual(len(response.get_json()["orders"]), 1)


if __name__ == "__main__":
    unittest.main()
