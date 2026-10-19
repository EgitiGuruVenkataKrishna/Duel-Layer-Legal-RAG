from src.nyayasetu.offence.schedule_store import OffenceClassificationStore


def test_murder_classification():
    store = OffenceClassificationStore()
    off = store.get_offence("103(1)")
    assert off is not None
    assert off["cognizable"] == "Cognizable"
    assert off["bailable"] == "Non-bailable"
    assert "Court of Session" in off["triable_by"]


def test_theft_classification():
    store = OffenceClassificationStore()
    off = store.get_offence("303(2)")
    assert off is not None
    assert off["bailable"] == "Non-bailable"
    assert "Magistrate" in off["triable_by"]
