# UniOCR 项目开发规范与技能标准 (Skill Standard)

## 1. 项目定位与目标
- **名称**：UniOCR (通用多语言 OCR 抽象层)
- **目标**：打造一个高内聚、低耦合的多语言 OCR 工具包与 API 服务。屏蔽底层引擎差异（如 PaddleOCR、Apple Vision 等），提供统一的文档抽象结构。

## 2. 核心架构设计与开发原则

### 2.1 引擎适配器模式 (Adapter Pattern)
- 所有底层 OCR 引擎必须继承自统一的基类（如 `BaseOCREngine`）。
- **统一输出格式**：无论什么引擎，对外必须输出标准的 `Document` 对象，包含 `text`, `markdown`, 和统一规范的 `blocks` (bbox, confidence, block_type)。

### 2.2 引擎调度优先级 (Priority Logic)
如果用户选择 `engine="auto"`，系统需按以下优先级自动回退与检测：
1. **PaddleOCR-VL**：默认首选，最强版面分析与复杂内容解析（适用：复杂 PDF、论文、带公式表格的扫描件）。
2. **Apple Vision**：如果检测到运行环境为 macOS，且未安装 Paddle/遇到错误，或用户明确指定需要“极速模式”，则自动回退调用 macOS 原生 Vision 框架。
3. **Tesseract**：最后的回退选项，适用于轻量级纯文本识别。

### 2.3 输入格式统一化 (Input Standardization)
- 对外统一接收: `Path`, `URL`, `Base64`。
- 内部自动实现**防呆预处理**：对长篇 PDF 或 Word 自动执行“压平”（Flattening）切分为图片流，然后分发给具体的引擎处理。不要让具体的引擎去操心“如何处理 PDF”。

## 3. 代码规范 (Coding Standards)

- **语言风格**：
  - 代码注释请使用清晰的英文或中文。
  - 函数命名采用标准的 `snake_case`，类名使用 `PascalCase`。
- **类型提示 (Type Hints)**：
  - 强制使用 Python Type Hints (如 `Dict`, `List`, `Optional`, `Union`)。这对一个将要做成 SDK 的项目至关重要。
- **环境与依赖**：
  - 首选通过 `uv` 管理依赖。
  - 提供 `pyproject.toml` 或 `requirements.txt` 清单。
  - 尽量实现**可选依赖 (Optional Dependencies)**。例如，没有装 PaddlePaddle 也能 `import uniocr` 并使用 Apple Vision 引擎。

## 4. 业务边界 (Scope)
在本项目内，AI Agent 应聚焦于：
1. 构建 SDK 核心库架构。
2. 编写 `PaddleOCRAdapter` 和 `AppleVisionAdapter` 的具体实现代码。
3. 封装输入处理和 PDF 压平逻辑。
4. 提供简单的 FastAPI / CLI 入口。
