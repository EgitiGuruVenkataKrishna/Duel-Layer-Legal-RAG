from src.nyayasetu.transition.mapper import StatutoryTransitionMapper


def test_transition_ipc_302():
    res = StatutoryTransitionMapper.lookup_transition("IPC", "302")
    assert res is not None
    assert res["new_code"] == "BNS"
    assert res["new_sec"] == "103(1)"
    assert "mob lynching" in res["key_differences"].lower()


def test_transition_ipc_420():
    res = StatutoryTransitionMapper.lookup_transition("IPC", "420")
    assert res is not None
    assert res["new_code"] == "BNS"
    assert "318" in res["new_sec"]


def test_transition_crpc_438():
    res = StatutoryTransitionMapper.lookup_transition("CRPC", "438")
    assert res is not None
    assert res["new_code"] == "BNSS"
    assert res["new_sec"] == "482"


def test_transition_iea_65b():
    res = StatutoryTransitionMapper.lookup_transition("IEA", "65B")
    assert res is not None
    assert res["new_code"] == "BSA"
    assert "61" in res["new_sec"]
