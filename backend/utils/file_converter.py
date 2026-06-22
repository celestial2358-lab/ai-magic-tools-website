"""
文件转换工具模块
=================
提供常见文件格式之间的转换功能。
包括 TXT、JSON、CSV、Markdown、HTML 等格式的互转。

所有转换在内存中完成，无需写入临时文件。
"""

import io
import json
import csv
import os
from typing import Optional


# ============================================
#  工具函数
# ============================================

def safe_return(success: bool, data: dict = None, message: str = "") -> dict:
    """统一返回值格式"""
    return {
        "success": success,
        "data": data if data is not None else {},
        "message": message
    }


# ============================================
#  JSON <-> CSV 互转
# ============================================

def json_to_csv(json_str: str) -> dict:
    """
    将 JSON 字符串转换为 CSV 格式。

    支持两种 JSON 结构：
    1. 对象数组：[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    2. 嵌套对象：{"rows": [{"a": 1, "b": 2}]}  —— 会尝试自动提取数组

    API: POST /api/convert/json-to-csv
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return safe_return(False, message=f"JSON 解析失败: {str(e)}")

    # 如果 data 本身就是列表且元素都是字典，直接处理
    if isinstance(data, list):
        records = data
    # 如果是字典，尝试找到包含列表的第一个值
    elif isinstance(data, dict):
        records = None
        for value in data.values():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                records = value
                break
        if records is None:
            return safe_return(False, message="未找到可转换的数组数据，请提供对象数组格式的 JSON")
    else:
        return safe_return(False, message="JSON 格式不正确，需要对象数组")

    if len(records) == 0:
        return safe_return(False, message="数据为空")

    # 收集所有列名（字段名）
    all_keys = []
    for record in records:
        if isinstance(record, dict):
            for key in record:
                if key not in all_keys:
                    all_keys.append(key)

    if not all_keys:
        return safe_return(False, message="未找到有效字段")

    # 生成 CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, extrasaction='ignore')
    writer.writeheader()
    for record in records:
        if isinstance(record, dict):
            writer.writerow(record)

    csv_content = output.getvalue()

    return safe_return(True, data={
        "csv": csv_content,
        "rows": len(records),
        "columns": all_keys
    }, message=f"已转换为 CSV，共 {len(records)} 行 {len(all_keys)} 列")


def csv_to_json(csv_str: str) -> dict:
    """
    将 CSV 字符串转换为 JSON 数组。

    API: POST /api/convert/csv-to-json
    """
    if not csv_str.strip():
        return safe_return(False, message="CSV 内容不能为空")

    try:
        reader = csv.DictReader(io.StringIO(csv_str))
        records = []
        for row in reader:
            # 尝试自动类型转换（数字）
            converted = {}
            for key, value in row.items():
                cleaned = value.strip() if value else ""
                # 尝试转为数字
                if cleaned:
                    try:
                        if '.' in cleaned:
                            converted[key] = float(cleaned)
                        else:
                            converted[key] = int(cleaned)
                    except ValueError:
                        converted[key] = cleaned
                else:
                    converted[key] = cleaned
            records.append(converted)

        if not records:
            return safe_return(False, message="CSV 中没有数据行")

        return safe_return(True, data={
            "json": json.dumps(records, ensure_ascii=False, indent=2),
            "records": records,
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else []
        }, message=f"已转换为 JSON，共 {len(records)} 行")

    except Exception as e:
        return safe_return(False, message=f"CSV 解析失败: {str(e)}")


# ============================================
#  Markdown <-> HTML 互转
# ============================================

def markdown_to_html(md_text: str) -> dict:
    """
    将 Markdown 文本转换为 HTML。

    API: POST /api/convert/markdown-to-html
    """
    if not md_text.strip():
        return safe_return(False, message="Markdown 内容不能为空")

    try:
        import markdown
        html = markdown.markdown(
            md_text,
            extensions=[
                'extra',           # 表格、代码块等扩展
                'codehilite',      # 代码高亮
                'toc',             # 目录
                'nl2br',           # 换行转 <br>
                'sane_lists',      # 更智能的列表处理
            ]
        )

        # 包装为完整的 HTML 文档
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown 转换结果</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.8;
            color: #333;
        }}
        pre {{ background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #f7f7f7; }}
        img {{ max-width: 100%; }}
        blockquote {{
            border-left: 4px solid #4299e1;
            padding-left: 16px;
            color: #666;
            margin-left: 0;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

        return safe_return(True, data={
            "html": full_html,
            "body_only": html
        }, message="Markdown 已转换为 HTML")

    except ImportError:
        return safe_return(False, message="缺少 markdown 库，请运行: pip install markdown")
    except Exception as e:
        return safe_return(False, message=f"转换失败: {str(e)}")


def html_to_markdown(html_text: str) -> dict:
    """
    将 HTML 转换为纯文本/Markdown 格式（提取文本内容）。

    API: POST /api/convert/html-to-text
    """
    if not html_text.strip():
        return safe_return(False, message="HTML 内容不能为空")

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')

        # 去除 script 和 style 标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # 获取纯文本
        text = soup.get_text()

        # 清理空白
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = '\n\n'.join(lines)

        return safe_return(True, data={
            "text": cleaned,
            "title": soup.title.string if soup.title else ""
        }, message="HTML 已转换为纯文本")

    except ImportError:
        return safe_return(False, message="缺少 beautifulsoup4 库，请运行: pip install beautifulsoup4")
    except Exception as e:
        return safe_return(False, message=f"转换失败: {str(e)}")


# ============================================
#  TXT -> JSON（键值对解析）
# ============================================

def txt_to_json(txt_text: str) -> dict:
    """
    解析键值对格式的文本（如配置文件），转为 JSON。

    支持的格式：
    key: value
    key = value

    API: POST /api/convert/txt-to-json
    """
    if not txt_text.strip():
        return safe_return(False, message="文本内容不能为空")

    result = {}
    lines = txt_text.strip().split('\n')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('//'):
            continue  # 跳过空行和注释

        # 尝试 : 分隔
        if ':' in stripped:
            key, value = stripped.split(':', 1)
        elif '=' in stripped:
            key, value = stripped.split('=', 1)
        else:
            continue

        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # 自动类型转换
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'null' or value.lower() == 'none':
            value = None
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass  # 保持为字符串

        result[key] = value

    if not result:
        return safe_return(False, message="未找到有效的键值对，请使用 'key: value' 或 'key = value' 格式")

    return safe_return(True, data={
        "json": json.dumps(result, ensure_ascii=False, indent=2),
        "records": result,
        "key_count": len(result)
    }, message=f"已转换为 JSON，包含 {len(result)} 个键值对")


# ============================================
#  JSON 美化 / 压缩
# ============================================

def format_json(json_str: str, mode: str = "pretty") -> dict:
    """
    JSON 格式化工具。

    参数:
        json_str : JSON 字符串
        mode     : pretty（美化）/ compact（压缩）/ validate（仅校验）

    API: POST /api/convert/json-format
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return safe_return(False, message=f"JSON 格式错误: {str(e)}")

    if mode == "pretty":
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        return safe_return(True, data={"result": formatted}, message="JSON 已美化")
    elif mode == "compact":
        formatted = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return safe_return(True, data={"result": formatted}, message="JSON 已压缩")
    elif mode == "validate":
        return safe_return(True, data={
            "valid": True,
            "type": type(data).__name__,
            "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
            "length": len(data) if isinstance(data, (list, dict)) else 1
        }, message="JSON 格式正确")
    else:
        return safe_return(False, message=f"不支持的模式: {mode}")


# ============================================
#  文本编码检测与转换
# ============================================

def detect_encoding(text_bytes: bytes) -> dict:
    """
    简单检测文本编码（UTF-8 / GBK / ASCII 等）。

    API: POST /api/convert/detect-encoding
    """
    if not text_bytes:
        return safe_return(False, message="内容不能为空")

    # 尝试按常见编码解码
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'ascii']
    results = []

    for enc in encodings_to_try:
        try:
            decoded = text_bytes.decode(enc)
            results.append({
                "encoding": enc,
                "success": True,
                "preview": decoded[:100]
            })
        except (UnicodeDecodeError, UnicodeError):
            results.append({
                "encoding": enc,
                "success": False
            })

    successful = [r for r in results if r["success"]]

    return safe_return(True, data={
        "detected": successful[0]["encoding"] if successful else "unknown",
        "compatible_encodings": [r["encoding"] for r in successful],
        "all_results": results
    }, message=f"编码检测完成，推荐使用 {successful[0]['encoding'] if successful else 'binary'}")
