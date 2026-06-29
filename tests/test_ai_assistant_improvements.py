import unittest


class AIAssistantImprovementTests(unittest.TestCase):
    def test_sidebar_example_buttons_have_readable_dark_style(self):
        from src.app.styles import build_sidebar_style_overrides

        css = build_sidebar_style_overrides()

        self.assertIn('[data-testid="stSidebar"] div[data-testid="stButton"] button', css)
        self.assertIn('background: rgba(255, 255, 255, .10)', css)
        self.assertIn('color: #f4fffb', css)
        self.assertIn('white-space: normal', css)


    def test_global_layout_adds_top_breathing_room(self):
        from src.app.styles import build_global_layout_overrides

        css = build_global_layout_overrides()

        self.assertIn('.block-container', css)
        self.assertIn('padding-top: 2.75rem', css)
        self.assertIn('@media (max-width: 760px)', css)
    def test_deepseek_authentication_error_is_actionable(self):
        from src.agent.query_engine import format_ai_service_error

        raw_error = (
            "Error code: 401 - {'error': {'message': 'Authentication Fails, "
            "Your api key: ****06e8 is invalid', 'type': 'authentication_error'}}"
        )

        message = format_ai_service_error(raw_error)

        self.assertIn("DeepSeek API Key 无效", message)
        self.assertIn("Streamlit Cloud", message)
        self.assertIn("DEEPSEEK_API_KEY", message)
        self.assertNotIn("****06e8", message)


if __name__ == "__main__":
    unittest.main()
