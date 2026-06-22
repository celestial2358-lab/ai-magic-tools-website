"""
╔══════════════════════════════════════════════════════════════╗
║               AI Magic Tools — Flask 主程序                  ║
║                                                              ║
║  提供老照片修复、文本处理、图片处理、文件转换等 API 服务       ║
╚══════════════════════════════════════════════════════════════╝

启动方式:
    python app.py
    或
    flask run --host=0.0.0.0 --port=5000

生产环境（推荐）:
    gunicorn app:app --bind 0.0.0.0:$PORT
"""

import os
import sys
import logging
from datetime import datetime

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# 把 utils 文件夹加入 Python 搜索路径，确保导入不出错
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from utils.text_processor import (
    count_text,
    word_frequency,
    format_text,
    summarize,
    check_sensitive,
)
from utils.image_processor import (
    restore_photo,
    compress_image,
    convert_format,
    get_image_info,
)
from utils.file_converter import (
    json_to_csv,
    csv_to_json,
    markdown_to_html,
    html_to_markdown,
    txt_to_json,
    format_json,
    detect_encoding,
)


# ============================================
#  应用初始化
# ============================================

app = Flask(__name__)

# 允许跨域请求（让前端页面可以调用后端 API）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ----- 日志配置 -----
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("ai-magic")

# ----- 应用配置 -----
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 最大上传 16MB
    JSON_AS_ASCII=False,                   # JSON 返回中文时不转义
)


# ============================================
#  全局错误处理
# ============================================

@app.errorhandler(400)
def bad_request(error):
    """请求参数错误"""
    return jsonify({
        "success": False,
        "data": {},
        "message": "请求参数有误，请检查"
    }), 400


@app.errorhandler(404)
def not_found(error):
    """接口不存在"""
    return jsonify({
        "success": False,
        "data": {},
        "message": "接口不存在，请检查 API 路径"
    }), 404


@app.errorhandler(413)
def too_large(error):
    """上传文件过大"""
    return jsonify({
        "success": False,
        "data": {},
        "message": "文件过大，最大支持 16MB"
    }), 413


@app.errorhandler(500)
def server_error(error):
    """服务器内部错误"""
    logger.exception("服务器内部错误")
    return jsonify({
        "success": False,
        "data": {},
        "message": "服务器内部错误，请稍后重试"
    }), 500


# ============================================
#  通用路由
# ============================================

@app.route('/')
def home():
    """首页——API 服务信息"""
    return jsonify({
        "name": "AI Magic Tools API",
        "version": "1.0.0",
        "description": "AI 魔法工具箱 —— 提供文本处理、图片处理、文件转换等 API 服务",
        "endpoints": {
            "text": [
                {"method": "POST", "path": "/api/text/count", "desc": "文本字数统计"},
                {"method": "POST", "path": "/api/text/frequency", "desc": "词频分析"},
                {"method": "POST", "path": "/api/text/format", "desc": "文本格式化"},
                {"method": "POST", "path": "/api/text/summarize", "desc": "文本摘要"},
                {"method": "POST", "path": "/api/text/sensitive-check", "desc": "敏感词检测"},
            ],
            "image": [
                {"method": "POST", "path": "/api/image/restore", "desc": "老照片修复"},
                {"method": "POST", "path": "/api/image/compress", "desc": "图片压缩"},
                {"method": "POST", "path": "/api/image/convert", "desc": "图片格式转换"},
                {"method": "POST", "path": "/api/image/info", "desc": "图片信息提取"},
            ],
            "convert": [
                {"method": "POST", "path": "/api/convert/json-to-csv", "desc": "JSON 转 CSV"},
                {"method": "POST", "path": "/api/convert/csv-to-json", "desc": "CSV 转 JSON"},
                {"method": "POST", "path": "/api/convert/markdown-to-html", "desc": "Markdown 转 HTML"},
                {"method": "POST", "path": "/api/convert/html-to-text", "desc": "HTML 转纯文本"},
                {"method": "POST", "path": "/api/convert/txt-to-json", "desc": "键值对文本转 JSON"},
                {"method": "POST", "path": "/api/convert/json-format", "desc": "JSON 格式化/压缩"},
                {"method": "POST", "path": "/api/convert/detect-encoding", "desc": "文本编码检测"},
            ]
        },
        "status": "running",
        "server_time": datetime.now().isoformat()
    })


@app.route('/health')
def health():
    """健康检查接口（部署平台会定时访问此接口确认服务正常）"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


# ============================================
#  文本处理 API
# ============================================

@app.route('/api/text/count', methods=['POST'])
def api_text_count():
    """文本字数统计"""
    logger.info("→ 请求: 文本统计")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    result = count_text(data['text'])
    return jsonify(result)


@app.route('/api/text/frequency', methods=['POST'])
def api_text_frequency():
    """词频分析"""
    logger.info("→ 请求: 词频分析")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    top_n = data.get('top_n', 20)
    result = word_frequency(data['text'], top_n=int(top_n))
    return jsonify(result)


@app.route('/api/text/format', methods=['POST'])
def api_text_format():
    """文本格式化"""
    logger.info("→ 请求: 文本格式化")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    mode = data.get('mode', 'clean')
    result = format_text(data['text'], mode=mode)
    return jsonify(result)


@app.route('/api/text/summarize', methods=['POST'])
def api_text_summarize():
    """文本摘要"""
    logger.info("→ 请求: 文本摘要")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    sentence_count = data.get('sentence_count', 3)
    result = summarize(data['text'], sentence_count=int(sentence_count))
    return jsonify(result)


@app.route('/api/text/sensitive-check', methods=['POST'])
def api_text_sensitive_check():
    """敏感词检测"""
    logger.info("→ 请求: 敏感词检测")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    result = check_sensitive(data['text'])
    return jsonify(result)


# ============================================
#  图片处理 API
# ============================================

@app.route('/api/image/restore', methods=['POST'])
def api_image_restore():
    """老照片修复"""
    logger.info("→ 请求: 老照片修复")

    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "请上传图片文件（字段名为 file）"}), 400

    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"success": False, "message": "未选择文件"}), 400

    # 读取文件字节
    image_bytes = file.read()
    if len(image_bytes) == 0:
        return jsonify({"success": False, "message": "文件为空"}), 400

    # 读取参数（带默认值）
    sharpness = float(request.form.get('sharpness', 1.5))
    contrast = float(request.form.get('contrast', 1.2))
    brightness = float(request.form.get('brightness', 1.1))
    denoise = request.form.get('denoise', 'true').lower() == 'true'
    colorize = request.form.get('colorize', 'false').lower() == 'true'
    output_format = request.form.get('output_format', 'PNG').upper()

    result = restore_photo(
        image_bytes=image_bytes,
        sharpness=sharpness,
        contrast=contrast,
        brightness=brightness,
        denoise=denoise,
        colorize=colorize,
        output_format=output_format,
    )

    return jsonify(result)


@app.route('/api/image/compress', methods=['POST'])
def api_image_compress():
    """图片压缩"""
    logger.info("→ 请求: 图片压缩")

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "请上传图片文件"}), 400

    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"success": False, "message": "未选择文件"}), 400

    image_bytes = file.read()
    if len(image_bytes) == 0:
        return jsonify({"success": False, "message": "文件为空"}), 400

    quality = int(request.form.get('quality', 70))
    max_width = request.form.get('max_width')
    max_height = request.form.get('max_height')
    output_format = request.form.get('output_format', 'JPEG')

    result = compress_image(
        image_bytes=image_bytes,
        quality=quality,
        max_width=int(max_width) if max_width else None,
        max_height=int(max_height) if max_height else None,
        output_format=output_format,
    )

    return jsonify(result)


@app.route('/api/image/convert', methods=['POST'])
def api_image_convert():
    """图片格式转换"""
    logger.info("→ 请求: 图片格式转换")

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "请上传图片文件"}), 400

    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"success": False, "message": "未选择文件"}), 400

    image_bytes = file.read()
    target_format = request.form.get('target_format', 'PNG')

    result = convert_format(image_bytes, target_format=target_format)
    return jsonify(result)


@app.route('/api/image/info', methods=['POST'])
def api_image_info():
    """图片信息提取"""
    logger.info("→ 请求: 图片信息提取")

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "请上传图片文件"}), 400

    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({"success": False, "message": "未选择文件"}), 400

    image_bytes = file.read()
    result = get_image_info(image_bytes)
    return jsonify(result)


# ============================================
#  文件转换 API
# ============================================

@app.route('/api/convert/json-to-csv', methods=['POST'])
def api_json_to_csv():
    """JSON 转 CSV"""
    logger.info("→ 请求: JSON -> CSV")
    data = request.get_json(silent=True)
    if not data or 'json' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 json 字段"}), 400

    result = json_to_csv(data['json'])
    return jsonify(result)


@app.route('/api/convert/csv-to-json', methods=['POST'])
def api_csv_to_json():
    """CSV 转 JSON"""
    logger.info("→ 请求: CSV -> JSON")
    data = request.get_json(silent=True)
    if not data or 'csv' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 csv 字段"}), 400

    result = csv_to_json(data['csv'])
    return jsonify(result)


@app.route('/api/convert/markdown-to-html', methods=['POST'])
def api_markdown_to_html():
    """Markdown 转 HTML"""
    logger.info("→ 请求: Markdown -> HTML")
    data = request.get_json(silent=True)
    if not data or 'markdown' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 markdown 字段"}), 400

    result = markdown_to_html(data['markdown'])
    return jsonify(result)


@app.route('/api/convert/html-to-text', methods=['POST'])
def api_html_to_text():
    """HTML 转纯文本"""
    logger.info("→ 请求: HTML -> 纯文本")
    data = request.get_json(silent=True)
    if not data or 'html' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 html 字段"}), 400

    result = html_to_markdown(data['html'])
    return jsonify(result)


@app.route('/api/convert/txt-to-json', methods=['POST'])
def api_txt_to_json():
    """键值对文本转 JSON"""
    logger.info("→ 请求: TXT -> JSON")
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 text 字段"}), 400

    result = txt_to_json(data['text'])
    return jsonify(result)


@app.route('/api/convert/json-format', methods=['POST'])
def api_json_format():
    """JSON 格式化/压缩/校验"""
    logger.info("→ 请求: JSON 格式化")
    data = request.get_json(silent=True)
    if not data or 'json' not in data:
        return jsonify({"success": False, "message": "请在请求体中提供 json 字段"}), 400

    mode = data.get('mode', 'pretty')
    result = format_json(data['json'], mode=mode)
    return jsonify(result)


@app.route('/api/convert/detect-encoding', methods=['POST'])
def api_detect_encoding():
    """文本编码检测"""
    logger.info("→ 请求: 编码检测")

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "请上传文本文件"}), 400

    file = request.files['file']
    text_bytes = file.read()

    result = detect_encoding(text_bytes)
    return jsonify(result)


# ============================================
#  启动入口
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    logger.info("=" * 60)
    logger.info("  AI Magic Tools API 启动中...")
    logger.info(f"  地址: http://0.0.0.0:{port}")
    logger.info(f"  调试模式: {'开启' if debug else '关闭'}")
    logger.info(f"  最大上传: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    logger.info("=" * 60)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
    )
