"""
相机连接测试脚本
通过同一端口发送 VTFP,X 指令触发不同相机拍照，并显示回复消息。

用法:
  python test_camera.py              # 测试所有相机 F0-F8
  python test_camera.py 0 3 5        # 只测试 F0、F3、F5
  python test_camera.py --port 9000  # 指定端口
  python test_camera.py --host 192.168.1.100  # 指定主机
"""

import socket
import sys
import time
from datetime import datetime

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 10401
TRIGGER_PREFIX = "VTFP"
TIMEOUT = 5.0


def test_camera(camera_id: int, host: str, port: int) -> dict:
    """测试单台相机: 连接同一端口，发送 VTFP,X 触发拍照"""
    addr = f"{host}:{port}"
    result = {"camera_id": camera_id, "addr": addr}

    # 1. TCP 连接
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

    # 2. 发送拍照指令 VTFP,X
    command = f"{TRIGGER_PREFIX},{camera_id}"
    try:
        sock.sendall((command + "\r\n").encode("utf-8"))
        result["command_sent"] = command
    except Exception as e:
        result["send_error"] = str(e)
        sock.close()
        return result

    # 3. 等待响应
    try:
        response = sock.recv(4096).decode("utf-8").strip()
        result["response"] = response
    except socket.timeout:
        result["response"] = f"等待响应超时 ({TIMEOUT}s)"
    except Exception as e:
        result["response"] = f"接收失败: {e}"
    finally:
        sock.close()

    return result


def main():
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    # 解析参数
    args = sys.argv[1:]
    camera_ids = []
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--timeout" and i + 1 < len(args):
            global TIMEOUT
            TIMEOUT = float(args[i + 1])
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
    print(f"目标: {host}:{port}  指令前缀: {TRIGGER_PREFIX}")
    print(f"测试相机: {['F'+str(i) for i in camera_ids]}")
    print("=" * 70)

    ok_count = 0
    for cid in camera_ids:
        r = test_camera(cid, host, port)
        cmd = r.get("command_sent", "")
        status = r["tcp"]

        if status == "ok":
            ok_count += 1
            latency = r.get("latency_ms", "?")
            response = r.get("response", "(无响应)")
            print(f"  F{cid}  [{cmd}]  连接成功  {latency}ms")
            print(f"        回复: {response}")
        else:
            err = r.get("error", status)
            print(f"  F{cid}  [{cmd}]  失败  {err}")
        print()

    print("=" * 70)
    print(f"结果: {ok_count}/{len(camera_ids)} 台相机响应成功")


if __name__ == "__main__":
    main()
