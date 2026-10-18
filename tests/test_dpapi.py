from google_auth_pc import dpapi

def test_roundtrip():
    blob = dpapi.protect("gizli-veri".encode())
    assert blob != "gizli-veri".encode()
    assert dpapi.unprotect(blob) == "gizli-veri".encode()

def test_corrupt_blob_raises():
    import pytest
    with pytest.raises(dpapi.DpapiError):
        dpapi.unprotect(b"bu-dpapi-degil")
