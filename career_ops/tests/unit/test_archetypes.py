from app.services.scoring.archetypes import classify_archetype


def test_classifies_data_streaming_role() -> None:
    text = "Build Kafka streaming pipelines and event-driven services for the data platform."
    assert classify_archetype(text) == "data_streaming"
