"""
文本处理工具模块
=================
提供文本分析、统计、格式化、摘要提取等功能。
所有函数都返回统一的字典格式，便于 API 返回 JSON。
"""

import re
import json
from collections import Counter
from typing import Any


# ============================================
#  工具函数
# ============================================

def safe_return(success: bool, data: Any = None, message: str = "") -> dict:
    """统一返回值格式，减少重复代码"""
    return {
        "success": success,
        "data": data if data is not None else {},
        "message": message
    }


# ============================================
#  文本统计
# ============================================

def count_text(text: str) -> dict:
    """
    统计文本的各项指标：
    - 总字符数
    - 中文字数
    - 英文单词数
    - 行数
    - 段落数

    API: POST /api/text/count
    """
    if not text or not text.strip():
        return safe_return(False, message="文本不能为空")

    # 中文字符（Unicode 范围：基本汉字 + 扩展区）
    chinese_chars = re.findall(r'[一-鿿]', text)

    # 英文单词（连续的字母序列）
    english_words = re.findall(r'[a-zA-Z]+', text)

    # 行数
    lines = text.split('\n')
    lines = [line for line in lines if line.strip()]  # 过滤空行

    # 段落（以连续空行分隔）
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return safe_return(True, data={
        "total_chars": len(text),
        "chinese_chars": len(chinese_chars),
        "english_words": len(english_words),
        "non_empty_lines": len(lines),
        "paragraphs": len(paragraphs)
    }, message="文本统计完成")


# ============================================
#  词频分析
# ============================================

def word_frequency(text: str, top_n: int = 20) -> dict:
    """
    分析文本中词语的出现频率。
    支持中文（简单分词：按常见词表匹配）和英文。

    API: POST /api/text/frequency
    """
    if not text or not text.strip():
        return safe_return(False, message="文本不能为空")

    # 英文词频（提取所有英文单词，转小写后统计）
    english_words = re.findall(r'[a-zA-Z]+', text)
    english_counter = Counter(w.lower() for w in english_words)

    # 中文词频（提取所有中文连续片段作为"词"）
    chinese_segments = re.findall(r'[一-鿿]{1,4}', text)
    chinese_counter = Counter(chinese_segments)

    # 合并并排序，取前 top_n
    all_counter = english_counter + chinese_counter
    top_words = all_counter.most_common(top_n)

    return safe_return(True, data={
        "top_words": [{"word": w, "count": c} for w, c in top_words],
        "unique_words": len(all_counter)
    }, message=f"词频分析完成，共 {len(all_counter)} 个独立词")


# ============================================
#  文本格式化
# ============================================

def format_text(text: str, mode: str = "clean") -> dict:
    """
    对文本进行格式化处理。

    支持的模式：
    - clean     : 清除多余空白、统一换行
    - markdown  : 将纯文本转为 Markdown 基本格式
    - plain     : 将 Markdown/HTML 转为纯文本（去除标记）

    API: POST /api/text/format
    """
    if not text or not text.strip():
        return safe_return(False, message="文本不能为空")

    if mode == "clean":
        # 合并多个空格为一个
        cleaned = re.sub(r'[ \t]+', ' ', text)
        # 合并多个换行为双换行（段落分隔）
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        # 去除每行的首尾空白
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
        return safe_return(True, data={"formatted": cleaned}, message="空白清理完成")

    elif mode == "plain":
        # 简单去除 Markdown 标记
        plain = text
        # 去除标题 # 号
        plain = re.sub(r'^#{1,6}\s+', '', plain, flags=re.MULTILINE)
        # 去除粗体/斜体标记
        plain = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', plain)
        plain = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', plain)
        # 去除链接 [text](url) -> text
        plain = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain)
        # 去除图片 ![alt](url) -> alt
        plain = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', plain)
        # 去除行内代码
        plain = re.sub(r'`(.*?)`', r'\1', plain)
        return safe_return(True, data={"formatted": plain}, message="已转为纯文本")

    elif mode == "markdown":
        # 简单地将纯文本结构化（按段落加空行）
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                formatted_lines.append(stripped)
            else:
                formatted_lines.append('')
        return safe_return(True, data={"formatted": '\n\n'.join(formatted_lines)}, message="已转为 Markdown 格式")

    else:
        return safe_return(False, message=f"不支持的模式: {mode}，可选值为 clean / markdown / plain")


# ============================================
#  文本摘要（基于规则）
# ============================================

def summarize(text: str, sentence_count: int = 3) -> dict:
    """
    基于规则的简单文本摘要：
    1. 将文本拆分为句子
    2. 按关键词权重评分
    3. 返回得分最高的若干个句子

    API: POST /api/text/summarize
    """
    if not text or not text.strip():
        return safe_return(False, message="文本不能为空")

    # 拆分句子（中英文标点）
    sentences = re.split(r'(?<=[。！？.!?\n])\s*', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) <= sentence_count:
        return safe_return(True, data={
            "summary": ' '.join(sentences),
            "sentence_count": len(sentences)
        }, message="文本较短，无需摘要")

    # 关键词（实词特征词，可根据需要扩充）
    keywords = [
        # 中文关键词
        '重要', '关键', '核心', '主要', '结论', '因此', '所以', '建议', '必须',
            '发现', '表明', '实现', '成功', '失败', '增长', '下降', '优势', '风险',
        # 英文关键词
        'important', 'key', 'critical', 'therefore', 'conclusion', 'result',
            'significant', 'essential', 'must', 'should', 'however'
    ]

    # 对每个句子评分
    scored = []
    for sentence in sentences:
        score = 0
        lower_s = sentence.lower()
        for kw in keywords:
            score += lower_s.count(kw)
        # 句子长度适中的额外加分
        if 20 < len(sentence) < 200:
            score += 1
        # 句子在开头或结尾的额外加分
        scored.append((sentence, score))

    # 按位置加权：开头和结尾的句子更可能是总结句
    if len(scored) > 0:
        scored[0] = (scored[0][0], scored[0][1] + 2)   # 开头句加分
        scored[-1] = (scored[-1][0], scored[-1][1] + 3)  # 结尾句加分

    # 按分数排序，取前 N 句
    scored.sort(key=lambda x: x[1], reverse=True)
    top_sentences = [s for s, _ in scored[:sentence_count]]

    # 按原文顺序重排
    ordered = [s for s in sentences if s in top_sentences]

    return safe_return(True, data={
        "summary": '。'.join(ordered) + '。',
        "sentence_count": len(ordered)
    }, message=f"已生成摘要，包含 {len(ordered)} 个句子")


# ============================================
#  敏感词检测
# ============================================

# 示例敏感词列表（实际项目中应放到数据库或配置文件中）
_SENSITIVE_WORDS = {
    "广告类": ["加微信", "扫码关注", "免费领取", "点击购买", "限时优惠", "立即下单"],
    "违规类": ["赌博", "毒品", "色情", "暴力", "诈骗"],
}

def check_sensitive(text: str) -> dict:
    """
    检测文本中的敏感词，返回检测结果。

    API: POST /api/text/sensitive-check
    """
    if not text or not text.strip():
        return safe_return(False, message="文本不能为空")

    found = []
    for category, words in _SENSITIVE_WORDS.items():
        for word in words:
            if word in text:
                found.append({
                    "word": word,
                    "category": category,
                    "positions": [m.start() for m in re.finditer(re.escape(word), text)]
                })

    return safe_return(True, data={
        "has_sensitive": len(found) > 0,
        "sensitive_count": len(found),
        "details": found
    }, message=f"检测到 {len(found)} 个敏感词" if found else "未检测到敏感词")
