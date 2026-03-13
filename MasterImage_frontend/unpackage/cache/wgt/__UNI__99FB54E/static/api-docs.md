# 智影前后端接口占位（增删改查记录）

接口以 `/api` 为前缀，返回值均为 `application/json`，以下数据结构仅作前端联调占位，后端接入时请根据实际字段调整。

| 接口 | 方法 | 说明 | 请求体 | 返回示例 |
| --- | --- | --- | --- | --- |
| /auth/login | POST | 登录，占位默认成功 | `{ "username": "string", "password": "string" }` | `{ "token": "xxx", "user": { "name": "王晨" } }` |
| /auth/register | POST | 注册新用户 | `{ "name": "string", "hospital": "string", "dept": "string", "mobile": "string", "password": "string" }` | `{ "id": "U001", "mobile": "string" }` |
| /patients | GET | 分页获取患者列表 | `?keyword=&page=&pageSize=` | `{ "items": [ { "id": "P20241201", "name": "王晨", "studyId": "ST-1" } ], "total": 1 }` |
| /patients | POST | 新增患者 | `{ "name": "string", "sex": "男/女", "age": 49, "diagnosis": "string" }` | `{ "id": "P20241201" }` |
| /patients/{id} | GET | 患者详情 | - | `{ "id": "P20241201", "gtvReady": true, "ctvReady": false }` |
| /patients/{id} | PUT | 更新患者基础信息 | `{ "diagnosis": "string", "stage": "string" }` | `{ "id": "P20241201" }` |
| /patients/{id}/review | PUT | 医生确认AI勾画 | `{ "status": "approved", "comment": "string" }` | `{ "ok": true }` |
| /patients/{id}/studies | POST | 上传或替换影像（DICOM/NIfTI） | `multipart/form-data` | `{ "studyId": "ST-202412-001" }` |
| /patients/{id}/studies | GET | 获取影像序列列表 | - | `{ "items": [ { "id": "ST-202412-001", "modality": "CT" } ] }` |
| /studies/{studyId}/segments | GET | 获取GTV/CTV/OAR分割结果 | `?version=latest` | `{ "gtv": "...", "ctv": "...", "confidenceMap": "url" }` |
| /studies/{studyId}/rtstruct | GET | 下载RT结构集 | - | 二进制流 |
| /studies/{studyId}/model | GET | three.js 所需3D数据 | - | `{ "meshUrl": "xxx.obj/glb", "heatmap": "xxx.png" }` |

> 说明：表中接口均在页面中以 TODO 注释占位，当前前端使用假数据或本地存储保证可跑通基本流程。接入真实后端时，保持黑白简约风的UI不变。负责3D部分的接口 `/studies/{studyId}/model` 预期返回 three.js 可直接加载的网格或体数据。 
