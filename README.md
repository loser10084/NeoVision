# SmartImage 比赛提交说明

本仓库已按比赛提交场景整理，保留了源码、依赖清单、参数模板和必要静态资源，去除了本地构建产物、密钥和运行期缓存。

## 项目结构

- `MasterImage_frontend`：uni-app 前端
- `SmartImage_backend`：Spring Boot / Spring Cloud 后端
- `SmartImage_multimodel`：Flask + LangGraph 模型服务

## 环境要求

- 前端：Node.js 18+，npm 9+，HBuilderX 3.8.7+
- 后端：JDK 17，Maven 3.9+，MySQL 8.0+，Redis 7+，Nacos 2.x
- 模型端：Python 3.9+

## 仓库内已包含的关键依赖与参数文件

### 前端

- `MasterImage_frontend/package.json`
- `MasterImage_frontend/package-lock.json`
- `MasterImage_frontend/.env.example`

### 后端

- `SmartImage_backend/pom.xml`
- `SmartImage_backend/smartimage-*/pom.xml`
- `SmartImage_backend/.env.example`
- `SmartImage_backend/smartimage-*/src/main/resources/application.yml`

### 模型端

- `SmartImage_multimodel/requirements.txt`
- `SmartImage_multimodel/.env.example`
- `SmartImage_multimodel/model_agents/*.md`

## 参数模板说明

### 前端参数

复制 `MasterImage_frontend/.env.example` 后按实际地址填写：

- `VUE_APP_GATEWAY_URL`：网关地址
- `VUE_APP_MODEL_URL`：模型服务地址
- `VUE_APP_AUTH_URL` / `VUE_APP_PATIENT_URL` / `VUE_APP_STUDY_URL`：如需拆分服务可单独指定

前端安装后也可以在“服务设置”页面修改网关和模型地址，不必重新打包。

### 后端参数

`SmartImage_backend/.env.example` 给出了后端启动所需环境变量模板。注意：Spring Boot 不会自动读取该文件，需要在 IDE、Shell 或启动脚本里显式导入这些环境变量。

关键参数：

- `MYSQL_*`：数据库连接
- `REDIS_*`：Redis 连接
- `NACOS_SERVER_ADDR`：服务注册中心地址
- `ALIOSS_*`：OSS 配置
- `MODEL_SERVICE_BASE_URL`：后端访问模型服务的地址

### 模型端参数

复制 `SmartImage_multimodel/.env.example` 为 `.env` 后填写：

- `OPENAI_API_KEY` / `OPENAI_BASE_URL`
- `MODEL_NAME` / `IMAGE_MODEL_NAME` / `EMBEDDING_MODEL_NAME`
- `REDIS_*`
- `SEG_*`、`CTV_*`、`CPDM_*` 权重和脚本路径

如果只做本地模型调试，可把 `MODEL_OUTPUT_STORAGE` 改为 `local`；如果需要后端统一接管模型输出并上传 OSS，则保持 `oss`。

## 快速启动

### 前端

```bash
cd MasterImage_frontend
npm install
```

然后使用 HBuilderX 打开 `MasterImage_frontend` 目录进行运行或打包。

### 后端

```bash
cd SmartImage_backend
mvn -pl smartimage-auth-service -am spring-boot:run
mvn -pl smartimage-patient-service -am spring-boot:run
mvn -pl smartimage-study-service -am spring-boot:run
mvn -pl smartimage-gateway -am spring-boot:run
```

启动前请先准备好 MySQL、Redis、Nacos，并导入 `SmartImage_backend/.env.example` 中对应环境变量。

### 模型端

```bash
cd SmartImage_multimodel
pip install -r requirements.txt
```

配置 `.env` 后运行：

```bash
python main.py
```

## 提交注意事项

- 本仓库中的参数模板均为 UTF-8 编码
- 本地 `.env`、签名文件、构建产物、运行期数据库与缓存目录已通过 `.gitignore` 排除
- 模型权重、超大医学影像样例和运行生成结果如需一并提交，建议单独打包说明来源与用途
