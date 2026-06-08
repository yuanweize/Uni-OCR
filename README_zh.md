<p align="center">
  <img src="assets/logo.svg" alt="UniOCR Logo" width="400"/>
</p>

<p align="center">
  <strong>一套接口，多引擎驱动，零摩擦使用。</strong>
</p>

<p align="center">
  <a href="https://github.com/yuanweize/uni-ocr/actions"><img src="https://img.shields.io/github/actions/workflow/status/yuanweize/uni-ocr/ci.yml?style=flat-square&logo=github" alt="CI"></a>
  <a href="https://pypi.org/project/uniocr/"><img src="https://img.shields.io/pypi/v/uniocr?style=flat-square&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://github.com/yuanweize/uni-ocr/pkgs/container/uni-ocr"><img src="https://img.shields.io/badge/GHCR-Docker-blue?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/yuanweize/uni-ocr?style=flat-square" alt="License"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Docs-English-blue?style=flat-square" alt="English Docs"></a>
</p>

---

**UniOCR** 是一个统一的多语言 OCR 抽象层，将最优秀的 OCR 引擎封装在一套简洁的接口之后。无论传入图片还是 PDF，都会返回结构化的文本、Markdown 和版面块信息 —— 无需关心底层使用了哪个引擎。

专为开发者、AI Agent 和自动化管线（n8n、Dify、Telegram Bot 等）设计。

## ✨ 核心特性

- 🔌 **可插拔引擎** — PaddleOCR-VL（深度文档 AI）和 Apple Vision（macOS 原生），自动优先级回退
- ⚡ **零配置加速** — 自动检测 Apple Silicon → 启动 MLX-VLM → Neural Engine 硬件加速，无需手动配置
- 📄 **接受一切输入** — 文件路径、URL、Base64、多页 PDF（自动压平为图像）
- 📦 **统一输出格式** — `Document → Pages → Blocks`，支持 `.text` / `.markdown` / `.to_dict()`
- 🌐 **内置 REST API** — 基于 FastAPI，支持 Swagger 文档、批量处理、请求追踪 —— 可直接被 n8n / Dify / 任何 HTTP 客户端调用
- 🐳 **Docker 就绪** — 一条命令部署
- 🖥️ **命令行工具** — `uniocr extract` · `uniocr engines` · `uniocr serve`

## 🚀 快速开始

### 方式一：pip 安装

```bash
# 核心包（轻量）
pip install uniocr

# 包含 PaddleOCR-VL（约 1.8 GB 模型，首次运行时下载）
pip install "uniocr[paddle]"

# 包含 Apple Vision（仅 macOS，零依赖）
pip install "uniocr[apple]"

# 全部安装
pip install "uniocr[all]"
```

### 方式二：Docker（推荐用于服务器）

```bash
# 快速启动 — 后台运行
docker run -d --name uniocr -p 8000:8000 ghcr.io/yuanweize/uni-ocr:latest

# 或使用 Docker Compose（推荐）
docker compose up -d

# 检查运行状态
curl http://localhost:8000/health
```

## 📖 使用方式

### Python SDK

```python
from uniocr import UniOCR

ocr = UniOCR(engine="auto")          # 自动选择最佳引擎
doc = ocr.extract("发票.pdf")

print(doc.text)                       # 纯文本
print(doc.markdown)                   # 结构化 Markdown
print(doc.to_dict())                  # JSON 可序列化字典
```

### 命令行

```bash
# 列出可用引擎
uniocr engines

# 提取文本（默认输出 Markdown）
uniocr extract document.pdf

# 指定引擎和输出格式
uniocr extract scan.png --engine apple --format json -o result.json

# 启动 API 服务（生产模式，4 个 worker）
uniocr serve --port 8000 --workers 4
```

### REST API

```bash
# 启动
uniocr serve --port 8000

# 上传文件提取
curl -X POST http://localhost:8000/extract \
  -F "file=@document.pdf" -F "engine=auto"

# 通过 URL 提取
curl -X POST http://localhost:8000/extract/url \
  -F "url=https://example.com/image.png"

# 批量处理
curl -X POST http://localhost:8000/extract/batch \
  -F "files=@page1.png" -F "files=@page2.png"
```

交互式 API 文档：`http://localhost:8000/docs`

#### API 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查（含引擎列表） |
| `GET` | `/engines` | 列出可用 OCR 引擎 |
| `GET` | `/docs` | Swagger 交互式文档 |
| `POST` | `/extract` | 上传文件提取 |
| `POST` | `/extract/url` | 通过 URL 提取 |
| `POST` | `/extract/batch` | 批量处理多个文件 |

#### 响应格式

```json
{
  "request_id": "ab07767c-...",
  "engine": "PaddleOCRVLAdapter",
  "page_count": 1,
  "text": "发票编号 #12345\n合计：€1,234.56",
  "markdown": "# 发票编号 #12345\n\n合计：€1,234.56",
  "pages": [...],
  "elapsed_seconds": 2.35
}
```

## 🐳 Docker 部署

### 快速运行

```bash
docker run -d \
  --name uniocr \
  -p 8000:8000 \
  -v uniocr-models:/root/.paddlex \
  ghcr.io/yuanweize/uni-ocr:latest
```

### Docker Compose（推荐）

```bash
# 后台启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

### 本地构建

```bash
git clone https://github.com/yuanweize/uni-ocr.git
cd uni-ocr
docker compose up -d --build
```

## 🔧 引擎优先级

| 优先级 | 引擎 | 适用场景 | 速度 |
|--------|------|---------|------|
| 1 | **PaddleOCR-VL** + MLX-VLM | 复杂版面、表格、公式，109 种语言 | ⚡⚡ |
| 2 | **PaddleOCR-VL** (CPU) | 同上，未安装 MLX-VLM 时 | ⚡ |
| 3 | **Apple Vision** | 简单文本，仅 macOS，极速 | ⚡⚡⚡ |

> 在 Apple Silicon 上，安装 `mlx-vlm` 后 UniOCR 会**自动启动** MLX-VLM 服务，退出时自动清理。完全零配置。

## 🔗 集成示例

### n8n 工作流

```
Telegram Trigger → HTTP Request (UniOCR) → AI Agent → ERPNext API
```

### Bob (macOS OCR 插件)

```bash
uniocr serve --port 8000
# Bob → 偏好设置 → OCR → 自定义 API → http://localhost:8000/extract
```

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `UNIOCR_PORT` | API 服务端口 (Docker Compose) | `8000` |
| `UNIOCR_MLX_VLM_URL` | 手动指定 MLX-VLM 服务地址 | 自动检测 |
| `UNIOCR_MLX_VLM_MODEL` | MLX-VLM 模型名 | `PaddlePaddle/PaddleOCR-VL-1.6` |

## 📄 许可证

[MIT](LICENSE) © 2026 Weize Yuan
