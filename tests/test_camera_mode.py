def test_add_camera_with_mode():
    from backend.models.database import add_camera, get_camera_by_id, init_db
    init_db()
    try:
        add_camera('Test Multi Camera', 100, mode='multi')
    except Exception:
        pass
    camera = get_camera_by_id(100)
    assert camera is not None
    assert camera['mode'] == 'multi'
