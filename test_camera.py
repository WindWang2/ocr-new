"""
相机连接测试脚本
用法:
  python test_camera.py              # 测试所有相机 F0-F8
  python test_camera.py 0 3 5        # 只测试 F0、F3、F5
  python test_camera.py --port 9000  # 指定端口基址
"""

import socket
import sys
import time
from datetime import datetime

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT_BASE = 9000
TRIGGER_PREFIX = "XXXX"
TIMEOUT = 5.0


def test_camera(camera_id: int, host: str, port_base: int) -> dict:
    """测试单台相机连接"""
    port = port_base + camera_id
    addr = f"{host}:{port}"
    result = {"camera_id": camera_id, "port": port, "addr": addr}

    # 1. TCP 连接测试
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        start = time.time()
        sock.connect((host, port))
        latency = (time.time() - start) * 1000
        result["tcp"] = "ok"
        result["latency_ms"] = round(latency, 1)
    except socket.timeout:
        result["tcp"] = "timeout"
        result["error"] = f"连接超时 ({TIMEOUT}s)"
        return result
    except ConnectionRefusedError:
        result["tcp"] = "refused"
        result["error"] = "连接被拒绝"
        return result
    except Exception as e:
        result["tcp"] = "error"
        result["error"] = str(e)
        return result

    # 2. 发送拍照指令
    command = f"{TRIGGER_PREFIX},{camera_id}"
    try:
        sock.sendall(command.encode("utf-8"))
        result["command_sent"] = command
    except Exception as e:
        result["response"] = f"发送失败: {e}"
        sock.close()
        return result

    # 3. 等待响应
    try:
        response = sock.recv(4096).decode("utf-8").strip()
        result["response"] = response[:200]  # 截断过长响应
        result["response_len"] = len(response)
    except socket.timeout:
        result["response"] = f"等待响应超时 ({TIMEOUT}s)"
    except Exception as e:
        result["response"] = f"接收失败: {e}"
    finally:
        sock.close()

    return result


def main():
    host = DEFAULT_HOST
    port_base = DEFAULT_PORT_BASE

    # 解析参数
    args = sys.argv[1:]
    camera_ids = []
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port_base = int(args[i + 1])
            i += 2
        else:
            try:
                camera_ids.append(int(args[i]))
            except ValueError:
                print(f"忽略无效参数: {args[i]}")
            i += 1

    if not camera_ids:
        camera_ids = list(range(9))

    print(f"相机连接测试  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {host}  端口基址: {port_base}")
    print(f"测试相机: {['F'+str(i) for i in camera_ids]}")
    print("=" * 70)

    ok_count = 0
    for cid in camera_ids:
        r = test_camera(cid, host, port_base)
        status = r["tcp"]
        if status == "ok":
            ok_count += 1
            resp = r.get("response", "")
            latency = r.get("latency_ms", "?")
            resp_preview = resp[:60] + ("..." if len(resp) > 60 else "")
            print(f"  F{cid}  {r['addr']}  连接成功  {latency}ms  响应: {resp_preview}")
        else:
            err = r.get("error", status)
            print(f"  F{cid}  {r['addr']}  失败  {err}")

    print("=" * 70)
    print(f"结果: {ok_count}/{len(camera_ids)} 台连接成功")


if __name__ == "__main__":
    main()
