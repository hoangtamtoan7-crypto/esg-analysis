import unittest


class AppDataQualityTests(unittest.TestCase):
    def test_build_industry_coverage_uses_company_name_fallback(self):
        from src.app.data_quality import build_industry_coverage

        results = [
            {
                "company_name": "平安银行",
                "report_year": "2026",
                "validation": {"overall_quality_score": 0.8},
                "completeness": {"completeness": 71.2},
            },
            {
                "company_name": "招商银行",
                "report_year": "2026",
                "validation": {"overall_quality_score": 0.6},
                "completeness": {"completeness": 50.0},
            },
            {
                "company_name": "宁德时代",
                "report_year": "2026",
                "validation": {"overall_quality_score": 0.7},
                "completeness": {"completeness": 60.0},
            },
        ]

        coverage = build_industry_coverage(results)

        finance = next(row for row in coverage if row["行业"] == "金融")
        self.assertEqual(finance["公司数"], 2)
        self.assertEqual(finance["报告数"], 2)
        self.assertEqual(finance["平均质量分"], 0.7)
        self.assertEqual(finance["平均覆盖度"], 60.6)
        self.assertEqual(coverage[0]["行业"], "金融")

    def test_displayable_company_filter_hides_low_signal_st_samples_by_default(self):
        from src.app.data_quality import filter_company_options

        results = [
            {
                "company_name": "*ST万方",
                "report_year": "2026",
                "validation": {"overall_quality_score": 0.1},
                "completeness": {"completeness": 71.2},
                "quantitative_indicators": [{"id": "E_Q01", "value": None}],
                "qualitative_indicators": [{"id": "E_L01", "status": "no", "summary": ""}],
            },
            {
                "company_name": "平安银行",
                "report_year": "2026",
                "validation": {"overall_quality_score": 0.8},
                "completeness": {"completeness": 71.2},
                "quantitative_indicators": [
                    {"id": "E_Q01", "value": 100.0},
                    {"id": "S_Q01", "value": 1000},
                ],
                "qualitative_indicators": [
                    {"id": "E_L01", "status": "yes", "summary": "制定低碳策略"},
                    {"id": "G_L01", "status": "partial", "summary": "披露部分制度"},
                ],
            },
        ]

        visible = filter_company_options(results, include_low_signal=False, min_valid_indicators=3)
        all_options = filter_company_options(results, include_low_signal=True, min_valid_indicators=3)

        self.assertEqual([row["company"] for row in visible], ["平安银行"])
        self.assertEqual([row["company"] for row in all_options], ["平安银行", "*ST万方"])
        self.assertEqual(visible[0]["valid_total"], 4)

    def test_build_validation_detail_makes_missing_values_concrete(self):
        from src.app.data_quality import build_validation_detail

        result = {
            "company_name": "测试公司",
            "report_year": "2026",
            "quantitative_indicators": [
                {"id": "E_Q01", "name": "温室气体排放总量", "value": None, "unit": "吨"},
                {"id": "S_Q01", "name": "员工总数", "value": 500, "unit": "人"},
            ],
            "qualitative_indicators": [
                {"id": "E_L01", "name": "气候变化应对策略", "status": "yes", "summary": "已制定"},
                {"id": "G_L01", "name": "董事会多元化政策", "status": "", "summary": ""},
            ],
        }

        detail = build_validation_detail(result)

        self.assertGreaterEqual(detail["summary"]["missing_value_count"], 2)
        issue_labels = {row["问题类型"] for row in detail["issues"]}
        self.assertIn("缺失定量数值", issue_labels)
        self.assertIn("缺失定性判断", issue_labels)
        self.assertGreater(detail["summary"]["missing_indicator_count"], 0)
        self.assertTrue(detail["missing"])


if __name__ == "__main__":
    unittest.main()
