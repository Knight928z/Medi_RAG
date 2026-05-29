from agents.parser_schema import ParserOutput


def test_parser_schema_validates():
    payload = {
        "parsed_report": {
            "schema_version": "v1",
            "language": "zh",
            "report_type": "血常规",
            "source_text": "白细胞 5.0 10^9/L",
            "biomarkers": [
                {
                    "name": "白细胞",
                    "value": "5.0",
                    "unit": "10^9/L",
                    "abnormal_flag": "N",
                    "reference_range": "3.5-9.5",
                    "raw_snippet": "白细胞 5.0 10^9/L",
                    "confidence": 0.9,
                    "valid": True,
                    "errors": [],
                }
            ],
            "notes": [],
            "extraction_confidence": 0.9,
            "ocr_noise": False,
            "invalid_fields": [],
        },
        "parser_notes": "ok",
        "parser_confidence": 0.9,
        "parser_errors": [],
    }
    output = ParserOutput.model_validate(payload)
    assert output.parsed_report.biomarkers[0].name == "白细胞"
