def test_read_multi_endpoint_exists():
    from backend.api.main import app
    routes = [route.path for route in app.routes]
    assert "/api/read-multi" in routes


def test_rebuild_clip_cache_endpoint_exists():
    from backend.api.main import app
    routes = [route.path for route in app.routes]
    assert "/api/rebuild-clip-cache" in routes
