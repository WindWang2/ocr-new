import pytest

def test_camera_table_has_mode_column():
    from backend.models.database import get_connection, get_camera_by_id, add_camera, init_db
    init_db()
    # 添加测试相机（如果已存在则跳过）
    try:
        add_camera('Test Camera Mode', 99, mode='multi')
    except Exception:
        pass
    camera = get_camera_by_id(99)
    assert camera is not None, 'Camera should exist'
    assert 'mode' in camera, 'Camera should have mode column after migration'
    assert camera['mode'] in ('single', 'multi'), f'mode should be single or multi, got {camera["mode"]}'
