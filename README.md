# 🪄 AI Magic Tools — AI 魔法工具箱

一个基于 Web 的 AI 工具集合平台，提供老照片修复、文本智能处理、图片处理、文件格式转换等实用功能。

---

## ✨ 功能列表

### 🖼️ 图片处理
| 功能 | 说明 |
|------|------|
| **老照片修复** | 通过图像增强算法改善模糊、褪色、有噪点的老照片 |
| **图片压缩** | 减小图片文件体积，支持自定义质量和尺寸限制 |
| **格式转换** | PNG / JPG / WebP / BMP 等常见格式互转 |
| **信息提取** | 获取图片尺寸、格式、EXIF 信息、DPI 等元数据 |

### 📝 文本处理
| 功能 | 说明 |
|------|------|
| **字数统计** | 中文字数、英文单词数、行数、段落数等 |
| **词频分析** | 分析文本中的高频词汇（支持中英文） |
| **文本格式化** | 空白清理、纯文本提取、Markdown 结构化 |
| **智能摘要** | 基于关键词权重自动提取文本摘要 |
| **敏感词检测** | 检测广告类、违规类敏感词汇 |

### 🔄 文件转换
| 功能 | 说明 |
|------|------|
| **JSON ↔ CSV** | JSON 数组和 CSV 表格互转 |
| **Markdown → HTML** | 将 Markdown 转为美观的 HTML 页面 |
| **HTML → 纯文本** | 从网页中提取纯净文本内容 |
| **键值对 → JSON** | 将配置文件格式转为 JSON |
| **JSON 美化/压缩** | JSON 格式校验与美化排版 |
| **编码检测** | 自动检测文本文件的字符编码 |

---

## 🚀 本地运行

### 前置条件

- **Python 3.10+** — [下载安装](https://www.python.org/downloads/)
- **Git**（可选）— [下载安装](https://git-scm.com/)

### 第 1 步：克隆项目

```bash
git clone https://github.com/your-github-username/ai-magic-tools-website.git
cd ai-magic-tools-website
```

### 第 2 步：创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 第 3 步：安装依赖

```bash
cd backend
pip install -r requirements.txt
```

> 💡 如果安装速度慢，可以使用国内镜像：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 第 4 步：启动服务

```bash
# 方式一：直接运行
python app.py

# 方式二：使用 Flask CLI
flask run --host=0.0.0.0 --port=5000

# 方式三：生产模式（安装 gunicorn 后）
gunicorn app:app --bind 0.0.0.0:5000
```

### 第 5 步：打开浏览器

访问 http://localhost:5000 即可看到 API 服务信息页面。

---

## 📡 API 接口文档

所有接口均返回 JSON 格式。统一响应结构：

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

---

### 图片处理 API

#### `POST /api/image/restore` — 老照片修复

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | File | ✅ | - | 图片文件 |
| `sharpness` | float | ❌ | 1.5 | 锐化强度 (0.0 ~ 3.0) |
| `contrast` | float | ❌ | 1.2 | 对比度增强 (0.0 ~ 3.0) |
| `brightness` | float | ❌ | 1.1 | 亮度调整 (0.0 ~ 3.0) |
| `denoise` | bool | ❌ | true | 是否降噪 |
| `colorize` | bool | ❌ | false | 是否尝试彩色化 |
| `output_format` | string | ❌ | PNG | 输出格式 (PNG / JPEG / WEBP) |

**示例（JavaScript fetch）：**
```js
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('sharpness', '1.5');
formData.append('denoise', 'true');

fetch('http://localhost:5000/api/image/restore', {
    method: 'POST',
    body: formData,
})
.then(res => res.json())
.then(data => console.log(data));
```

#### `POST /api/image/compress` — 图片压缩

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | File | ✅ | - | 图片文件 |
| `quality` | int | ❌ | 70 | 压缩质量 (1-100) |
| `max_width` | int | ❌ | - | 最大宽度（保持宽高比） |
| `max_height` | int | ❌ | - | 最大高度（保持宽高比） |
| `output_format` | string | ❌ | JPEG | 输出格式 |

#### `POST /api/image/convert` — 图片格式转换

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | File | ✅ | - | 图片文件 |
| `target_format` | string | ✅ | PNG | 目标格式 (png / jpg / webp / bmp) |

#### `POST /api/image/info` — 图片信息提取

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | ✅ | 图片文件 |

---

### 文本处理 API

#### `POST /api/text/count` — 字数统计

```json
{
  "text": "你的文本内容..."
}
```

#### `POST /api/text/frequency` — 词频分析

```json
{
  "text": "你的文本内容...",
  "top_n": 20
}
```

#### `POST /api/text/format` — 文本格式化

```json
{
  "text": "你的文本内容...",
  "mode": "clean"
}
```
> `mode` 可选值：`clean`（清理空白）/ `markdown`（Markdown 结构化）/ `plain`（去除标记）

#### `POST /api/text/summarize` — 文本摘要

```json
{
  "text": "你的长文本内容...",
  "sentence_count": 3
}
```

#### `POST /api/text/sensitive-check` — 敏感词检测

```json
{
  "text": "你的文本内容..."
}
```

---

### 文件转换 API

#### `POST /api/convert/json-to-csv` — JSON 转 CSV

```json
{
  "json": "[{\"name\": \"张三\", \"age\": 25}]"
}
```

#### `POST /api/convert/csv-to-json` — CSV 转 JSON

```json
{
  "csv": "name,age\n张三,25\n李四,30"
}
```

#### `POST /api/convert/markdown-to-html` — Markdown 转 HTML

```json
{
  "markdown": "# 标题\n\n这是**粗体**文字"
}
```

#### `POST /api/convert/html-to-text` — HTML 转纯文本

```json
{
  "html": "<h1>标题</h1><p>段落内容</p>"
}
```

#### `POST /api/convert/txt-to-json` — 键值对文本转 JSON

```json
{
  "text": "name: 张三\nage: 25\ncity: 北京"
}
```

#### `POST /api/convert/json-format` — JSON 格式化

```json
{
  "json": "{\"name\":\"张三\"}",
  "mode": "pretty"
}
```
> `mode` 可选值：`pretty`（美化）/ `compact`（压缩）/ `validate`（仅校验）

#### `POST /api/convert/detect-encoding` — 编码检测

使用 `multipart/form-data` 上传文本文件（字段名 `file`）。

---

## ☁️ 部署到云平台

### 方式一：Render（推荐新手）

[Render](https://render.com) 提供免费额度，部署简单。

1. **注册/登录** [render.com](https://render.com)
2. 点击 **New + → Web Service**
3. 连接你的 GitHub 仓库 `ai-magic-tools-website`
4. 填写以下配置：
   | 配置项 | 值 |
   |--------|-----|
   | **Name** | `ai-magic-tools` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r backend/requirements.txt` |
   | **Start Command** | `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT` |
   | **Root Directory** | （留空） |

5. 点击 **Create Web Service**，等待部署完成
6. 几分钟后，你的 API 就上线了！🎉

### 方式二：Railway

[Railway](https://railway.app) 也是一个对新手友好的平台。

1. **注册/登录** [railway.app](https://railway.app)
2. 点击 **New Project → Deploy from GitHub Repo**
3. 选择 `ai-magic-tools-website` 仓库
4. Railway 会自动检测 Python 项目并部署
5. 在 Settings 中确认 Start Command 为：
   ```
   cd backend && gunicorn app:app --bind 0.0.0.0:$PORT
   ```
6. 可以在 **Settings → Domains** 中生成公开访问链接

---

## 📁 项目结构

```
ai-magic-tools-website/
├── .gitignore                  # Git 忽略文件配置
├── README.md                   # 项目说明文档（本文件）
│
├── backend/                    # 后端（Flask API 服务）
│   ├── app.py                  # Flask 主程序，定义所有 API 路由
│   ├── requirements.txt        # Python 依赖列表
│   └── utils/                  # 工具函数模块
│       ├── __init__.py         # 包初始化文件
│       ├── text_processor.py   # 文本处理工具
│       ├── image_processor.py  # 图片处理工具
│       └── file_converter.py   # 文件转换工具
│
└── frontend/                   # 前端（静态页面）
    ├── index.html              # 主页面
    └── static/
        ├── css/
        │   └── style.css       # 样式文件
        └── js/
            └── script.js       # 交互逻辑
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Flask 3.x | 轻量级 Python Web 框架 |
| **跨域支持** | Flask-CORS | 允许前端跨域请求 API |
| **图片处理** | Pillow (PIL) | Python 图像处理标准库 |
| **文件转换** | markdown, beautifulsoup4, openpyxl | Markdown/HTML/CSV 处理 |
| **部署** | Gunicorn | Python WSGI 生产级服务器 |

---

## 💡 常见问题

**Q: 照片修复功能真的用了 AI 吗？**

目前核心使用的是传统图像处理算法（锐化、降噪、对比度增强），这些技术对老照片修复已经非常有效。AI 模型集成留好了接口，后续可以接入真实的深度学习模型来获得更好的效果。

**Q: 为什么上传图片后没有收到图片文件？**

当前 API 返回的是处理后的 JSON 信息（包含处理参数和原始/处理后的大小对比）。如需直接返回处理后的图片文件，可以在 API 中开启 `download` 模式（后续版本会支持）。

**Q: 如何添加新的工具？**

1. 在 `backend/utils/` 中创建新的模块文件
2. 在 `app.py` 中导入并添加路由
3. 在前端页面添加对应的 UI

---

## 📄 许可证

MIT License — 可自由使用、修改和分发。

---

> 🤖 本项目由 AI 辅助生成。如有问题或建议，欢迎提 Issue！
