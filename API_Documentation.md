# OCR 实验服务 API 接口说明

本文档包含最新的核心读数接口说明，主要分为**单仪表特写读数**与**多仪表视野扫描读数**两大类，分别支持**本地存储**与**阿里云 OSS 云端上传**。

---

## 一、 错误码字典 (Error Codes)
所有接口统一采用如下全局错误码体系，在 `success` 为 `false` 或单仪表读取异常时返回：

| 错误码 | 标识符 | 含义说明 |
|---|---|---|
| `1001` | `CAMERA_CAPTURE_FAILED` | 相机控制或硬件通信失败，拍照未成功。 |
| `1002` | `INSTRUMENT_NOT_FOUND` | YOLO 定位失败，在相机视野中没有找到对应的仪表特征。 |
| `1003` | `READINGS_INCOMPLETE` | 读取面板不完整、由于反光/遮挡等原因导致大模型无法提取合规数值。 |
| `1004` | `LLM_SERVICE_ERROR` | 大语言模型后台服务调用失败或格式解析异常。 |
| `1005` | `OSS_UPLOAD_FAILED` | 图片上传到阿里云 OSS 失败（检查网络或配置秘钥）。 |

---

## 二、 单仪表读数系列

此系列接口旨在为您获取特定仪表的截图及读数。

### 1. 本地存储版本：`POST /instruments/read`

拍摄物理照片，对请求的仪器进行定位裁剪，保存在本地并返回本地服务器的静态图片相对路径。

**请求格式：**
```json
{
  "instrument_id": 3,
  "camera_id": null
}
```
*(注：如果 `camera_id` 为 `null`，后端会自动通过配置表寻找该仪器映射的物理相机)*

**响应示例 (成功)：**
```json
{
  "success": true,
  "camera_image": "F3/crops/compressed_full_3_192244.png",
  "instrument_image": "F3/crops/instrument_crop_F3_192244.png",
  "readings": {
    "weight": 403.3,
    "unit": "g"
  }
}
```

---

### 2. 阿里云 OSS 版本：`POST /instruments/read-oss`

工作原理完全等同于本地接口，但会将生成的全景图与截图实时打包上传至阿里云 OSS 存储桶，返回能在公网访问的完全合格 URL。

**请求格式：**
同上。

**响应示例 (局部失败排查 - 1003)：**
即使读数无法提取，全景图与目标特写图(OSS路径)依然会返回供人工复检。
```json
{
  "success": false,
  "error_code": 1003,
  "message": "仪表读数面板可能不完整、被部分遮挡或无法提取到合规的数值",
  "camera_image": "https://shiyanfangcang-1.oss-cn-chengdu.aliyuncs.com/F3/compressed_full.png",
  "instrument_image": "https://shiyanfangcang-1.oss-cn-chengdu.aliyuncs.com/F3/instrument_crop.png",
  "readings": null
}
```

---

## 三、 多仪表视野扫描系列 (全局监控)

此系列接口控制指定相机拍照一次，自动探测视野中的**所有**已知仪表并并行解析读数。

### 1. 本地存储版本：`POST /cameras/read-visible`

**请求格式：**
```json
{
  "camera_id": 3
}
```

**响应示例：**
```json
{
  "success": true,
  "camera_id": 3,
  "camera_image": "F3/crops/compressed_full_3.png",
  "instruments": [
    {
      "instrument_id": 3,
      "instrument_name": "电子天平",
      "bbox": [105.2, 148.5, 302.1, 450.4],
      "instrument_image": "F3/crops/instrument_crop_3.png",
      "readings": { "weight": 403.3, "unit": "g" }
    }
  ]
}
```

---

### 2. 阿里云 OSS 版本：`POST /cameras/read-visible-oss`

将全景图和数组中的各个仪表特写全部推送到阿里云 OSS，独立管理每个仪表的识别错误码。

**响应示例 (含局部错误隔离)：**
注意：`success` 在视野扫描完成时会返回 `true`，但内部某几个仪表可能出现遮挡等情况，在数组子对象中带有 `error_code`。
```json
{
  "success": true,
  "camera_id": 3,
  "camera_image": "https://shiyanfangcang-1.oss-cn-chengdu.aliyuncs.com/F3/compressed_full_3.png",
  "instruments": [
    {
      "instrument_id": 3,
      "instrument_name": "电子天平",
      "bbox": [105.2, 148.5, 302.1, 450.4],
      "instrument_image": "https://shiyanfangcang-1.oss-cn-chengdu.aliyuncs.com/F3/instrument_crop_1.png",
      "readings": {
        "weight": 403.3,
        "unit": "g"
      },
      "error_code": null,
      "message": "解析成功"
    },
    {
      "instrument_id": 1,
      "instrument_name": "压力表",
      "bbox": [450.0, 102.3, 620.5, 310.1],
      "instrument_image": "https://shiyanfangcang-1.oss-cn-chengdu.aliyuncs.com/F3/instrument_crop_2.png",
      "readings": null,
      "error_code": 1003,
      "message": "仪表读数面板可能不完整、被部分遮挡或无法提取到合规的数值"
    }
  ]
}
```

---

## 附录：Linux/Mac 联调 Curl 参考

```bash
# 测试本地单仪表接口
curl -X POST http://127.0.0.1:8001/instruments/read \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"instrument_id": 3, "camera_id": null}'

# 测试阿里云单仪表接口
curl -X POST http://127.0.0.1:8001/instruments/read-oss \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"instrument_id": 3, "camera_id": null}'

# 测试阿里云多仪表视野扫描接口
curl -X POST http://127.0.0.1:8001/cameras/read-visible-oss \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"camera_id": 3}'
```
