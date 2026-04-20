"""
多相机实验功能测试（使用内置urllib）
"""

import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8001"

def api_call(path, method="GET", data=None, timeout=5):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode()
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "status": resp.status, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, color=""):
    print(f"{color}{msg}{RESET}")

def check_health():
    r = api_call("/health")
    if r.get("ok"):
        log(f"✓ 服务健康: {r['data'].get('message')}", GREEN)
        return True
    log(f"✗ 服务未运行", RED)
    return False

def setup_cameras():
    cameras = []
    # 列出并禁用旧相机
    r = api_call("/cameras")
    if r.get("ok"):
        for cam in r["data"].get("cameras", []):
            api_call(f"/cameras/{cam['camera_id']}", "DELETE")
    
    for i in range(1, 6):
        r = api_call("/cameras", "POST", {
            "name": f"测试相机{i}",
            "camera_id": i,
            "control_host": "127.0.0.1",
            "control_port": 8000 + i
        })
        if r.get("ok"):
            cameras.append(i)
            log(f"✓ 创建相机 {i}", GREEN)
    return cameras

def test_create_single():
    r = api_call("/experiments", "POST", {"name": "单相机测试", "camera_id": 1})
    if r.get("ok"):
        exp_id = r["data"].get("experiment_id")
        log(f"✓ 单相机实验: ID={exp_id}", GREEN)
        
        r2 = api_call(f"/experiments/{exp_id}")
        exp = r2["data"].get("experiment", {})
        if exp.get("camera_id") == 1:
            log(f"✓ 记录正确", GREEN)
            return exp_id
    log(f"✗ 单相机创建失败: {r.get('error')}", RED)
    return None

def _test_create_multi(count):
    r = api_call("/experiments", "POST", {
        "name": f"{count}相机实验",
        "camera_ids": list(range(1, count+1))
    })
    if r.get("ok"):
        exp_id = r["data"].get("experiment_id")
        log(f"✓ {count}相机实验: ID={exp_id}", GREEN)
        
        r2 = api_call(f"/experiments/{exp_id}")
        exp = r2["data"].get("experiment", {})
        if exp.get("camera_id_list") == list(range(1, count+1)):
            log(f"✓ 相机列表正确", GREEN)
            return exp_id
    log(f"✗ {count}相机创建失败", RED)
    return None

def _test_run(exp_id):
    r = api_call(f"/experiments/{exp_id}/run", "POST")
    if r.get("ok"):
        log(f"✓ 执行成功: 相机={r['data'].get('camera_ids')}", GREEN)
        log(f"  结果数={len(r['data'].get('results', []))}", YELLOW)
        return r["data"]
    log(f"✗ 执行失败: {r.get('error')}", RED)
    return None

def _test_detail(exp_id):
    r = api_call(f"/experiments/{exp_id}")
    if r.get("ok"):
        exp = r["data"].get("experiment", {})
        log(f"✓ 详情: 相机={exp.get('camera_id_list')}, 读数={exp.get('readings_summary')}", GREEN)
        return True
    log(f"✗ 详情获取失败", RED)
    return False

def main():
    log("=" * 50, YELLOW)
    log("多相机实验功能测试", YELLOW)
    log("=" * 50, YELLOW)
    
    if not check_health():
        log("\n✗ 后端未运行: ./start-backend.sh", RED)
        sys.exit(1)
    
    log("\n=== 准备相机 ===", YELLOW)
    cameras = setup_cameras()
    log(f"✓ 已创建 {len(cameras)} 相机", GREEN)
    
    results = {}
    
    # 单相机
    exp = test_create_single()
    results["单相机创建"] = bool(exp)
    if exp:
        r = _test_run(exp)
        results["单相机执行"] = bool(r)
        results["单相机详情"] = _test_detail(exp)
    
    # 1相机
    exp = _test_create_multi(1)
    results["1相机创建"] = bool(exp)
    if exp:
        r = _test_run(exp)
        results["1相机执行"] = bool(r)
        results["1相机详情"] = _test_detail(exp)
    
    # 3相机
    exp = _test_create_multi(3)
    results["3相机创建"] = bool(exp)
    if exp:
        r = _test_run(exp)
        results["3相机执行"] = bool(r)
        results["3相机详情"] = _test_detail(exp)
    
    # 5相机
    if len(cameras) >= 5:
        exp = _test_create_multi(5)
        results["5相机创建"] = bool(exp)
        if exp:
            r = _test_run(exp)
            results["5相机执行"] = bool(r)
            results["5相机详情"] = _test_detail(exp)
    
    # 汇总
    log("\n" + "=" * 50, YELLOW)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        log(f"  {'✓' if ok else '✗'}: {name}", GREEN if ok else RED)
    log(f"\n通过: {passed}/{len(results)}", GREEN if passed == len(results) else RED)
    
    # 写报告
    report = f"""# 多相机实验功能测试报告

## 测试概览
- 时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
- 结果: {passed}/{len(results)} 通过

## 结果

| 测试项 | 结果 |
|--------|------|
"""
    for name, ok in results.items():
        report += f"| {name} | {'✓' if ok else '✗'} |\n"
    
    report += f"""
## 结论

{"全部通过" if passed == len(results) else "有失败项"}

---
测试人: Tester-Agent
分支: feature/multi-camera-experiment
"""
    
    with open("tests/TEST_REPORT.md", "w") as f:
        f.write(report)
    
    log("\n报告: tests/TEST_REPORT.md", GREEN)
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
