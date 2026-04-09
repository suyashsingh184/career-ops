from app.services.scoring.keyword_gap import extract_keyword_gaps


def test_extract_keyword_gaps_returns_missing_terms() -> None:
    gaps = extract_keyword_gaps("Python Kafka Flink Streaming Data Platform", "Python APIs PostgreSQL")
    assert "kafka" in gaps
