import unittest

import app


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.init_db()

    def test_compute_recommendations_returns_top_three(self):
        conn = app.get_connection()
        profile = app.get_profile(conn)
        dishes = app.list_dishes(conn)
        history = app.list_history(conn)
        context = app.RecommendationContext(
            mode="cook",
            mood="ocupado",
            time_available=25,
            supermarket="Mercado Local",
            wants_variety=True,
        )

        recommendations = app.compute_recommendations(profile, dishes, history, context)
        conn.close()

        self.assertEqual(len(recommendations), 3)
        self.assertTrue(all(item["score"] >= recommendations[-1]["score"] for item in recommendations[:-1]))

    def test_bootstrap_contains_profile_and_ai(self):
        payload = app.serialize_bootstrap()
        self.assertIn("profile", payload)
        self.assertIn("recommendations", payload)
        self.assertIn("ai", payload)
        self.assertGreaterEqual(len(payload["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
