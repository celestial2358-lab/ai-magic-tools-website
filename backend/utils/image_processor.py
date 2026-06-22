"""
图片处理工具模块
=================
提供图片增强、修复、格式转换、压缩等功能。
使用 Pillow（PIL）库进行图片处理。

模拟 AI 修复功能：通过传统图像处理算法（锐化、降噪、对比度增强等）
来改善老照片的质量。真正的 AI 模型可以在此基础上替换核心算法。
"""

import os
import io
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from typing import Optional, Tuple


# 允许的图片格式
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


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


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_size(file_bytes: bytes) -> int:
    """获取文件字节大小"""
    return len(file_bytes)


# ============================================
#  老照片修复（核心功能）
# ============================================

def restore_photo(
    image_bytes: bytes,
    sharpness: float = 1.5,
    contrast: float = 1.2,
    brightness: float = 1.1,
    denoise: bool = True,
    colorize: bool = False,
    output_format: str = "PNG"
) -> dict:
    """
    老照片修复主流程——使用传统图像处理算法模拟 AI 修复效果。

    处理步骤：
    1. 加载图片 -> 2. 转灰度（可选彩色化）-> 3. 降噪 ->
    4. 增强对比度 -> 5. 锐化 -> 6. 调整亮度 -> 7. 输出

    参数:
        image_bytes   : 原始图片的字节数据
        sharpness     : 锐化强度 (0.0 ~ 3.0, 默认 1.5)
        contrast      : 对比度增强 (0.0 ~ 3.0, 默认 1.2)
        brightness    : 亮度调整 (0.0 ~ 3.0, 默认 1.1)
        denoise       : 是否启用降噪
        colorize      : 是否尝试彩色化（实验性）
        output_format : 输出格式 (PNG / JPEG / WEBP)

    API: POST /api/image/restore
    """
    try:
        # 第 1 步：加载图片
        image = Image.open(io.BytesIO(image_bytes))

        # 保存原始图片信息
        original_size = image.size
        original_mode = image.mode

        # 如果原图是 RGBA，先转为 RGB（便于后续处理）
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Alpha 通道作为遮罩
            image = background
        elif image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # 第 2 步：降噪处理
        if denoise:
            # 使用中值滤波去除椒盐噪声（老照片常见）
            image = image.filter(ImageFilter.MedianFilter(size=3))
            # 轻微高斯模糊以平滑噪点
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        # 第 3 步：增强对比度
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)

        # 第 4 步：锐化（让模糊的老照片恢复清晰度）
        if sharpness != 1.0:
            # UnsharpMask 比普通 SHARPEN 效果更好
            image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=int(sharpness * 100), threshold=3))

        # 第 5 步：亮度调整
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)

        # 第 6 步：实验性彩色化（模拟：对灰度图应用暖色调 sepia）
        if colorize and image.mode != "RGBA":
            # 转灰度
            gray = ImageOps.grayscale(image)
            # 应用 sepia 滤镜（棕褐色做旧风格的反向——相当于"去旧"）
            image = apply_sepia(gray.convert("RGB")) if image.mode == "L" else image
            # 如果原图就是灰度图，尝试添加自然色调
            if original_mode == "L":
                image = auto_tone(gray)

        # 第 7 步：编码输出
        output_buffer = io.BytesIO()
        save_format = output_format.upper()
        if save_format == "JPG":
            save_format = "JPEG"

        save_kwargs = {"format": save_format}
        if save_format == "JPEG":
            save_kwargs["quality"] = 92
            save_kwargs["optimize"] = True
        elif save_format == "PNG":
            save_kwargs["optimize"] = True

        image.save(output_buffer, **save_kwargs)
        output_bytes = output_buffer.getvalue()

        return safe_return(True, data={
            "original_size": list(original_size),
            "processed_size": list(image.size),
            "original_mode": original_mode,
            "output_format": save_format,
            "output_size_bytes": len(output_bytes),
        }, message="照片修复完成")

    except Exception as e:
        return safe_return(False, message=f"照片修复失败: {str(e)}")


# ============================================
#  辅助函数
# ============================================

def apply_sepia(image: Image.Image) -> Image.Image:
    """应用棕褐色 sepia 滤镜"""
    width, height = image.size
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            pixels[x, y] = (
                min(tr, 255),
                min(tg, 255),
                min(tb, 255)
            )
    return image


def auto_tone(gray_image: Image.Image) -> Image.Image:
    """自动色调映射：为灰度图添加轻微暖色调"""
    rgb_image = gray_image.convert("RGB")
    enhancer = ImageEnhance.Color(rgb_image)
    # 轻微上色（灰度图 Color 增强后呈现暖色调）
    return enhancer.enhance(1.3)


# ============================================
#  图片压缩
# ============================================

def compress_image(
    image_bytes: bytes,
    quality: int = 70,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    output_format: str = "JPEG"
) -> dict:
    """
    压缩图片：减小文件体积，可选缩放。

    参数:
        image_bytes    : 原始图片字节
        quality        : 压缩质量 (1-100, 默认 70)
        max_width      : 最大宽度（保持宽高比）
        max_height     : 最大高度（保持宽高比）
        output_format  : 输出格式

    API: POST /api/image/compress
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background

        original_size = image.size
        original_bytes = len(image_bytes)

        # 缩放
        if max_width and max_height:
            image.thumbnail((max_width, max_height), Image.LANCZOS)
        elif max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)
        elif max_height:
            ratio = max_height / image.height
            new_width = int(image.width * ratio)
            image = image.resize((new_width, max_height), Image.LANCZOS)

        # 输出
        output_buffer = io.BytesIO()
        fmt = "JPEG" if output_format.upper() == "JPG" else output_format.upper()
        image.save(output_buffer, format=fmt, quality=quality, optimize=True)
        output_bytes = output_buffer.getvalue()

        return safe_return(True, data={
            "original_size": list(original_size),
            "compressed_size": list(image.size),
            "original_bytes": original_bytes,
            "compressed_bytes": len(output_bytes),
            "compression_ratio": f"{len(output_bytes) / original_bytes * 100:.1f}%"
        }, message="图片压缩完成")

    except Exception as e:
        return safe_return(False, message=f"压缩失败: {str(e)}")


# ============================================
#  图片格式转换
# ============================================

def convert_format(image_bytes: bytes, target_format: str) -> dict:
    """
    将图片转换为指定格式。

    参数:
        image_bytes    : 原始图片字节
        target_format  : 目标格式 (png / jpg / webp / bmp)

    API: POST /api/image/convert
    """
    if target_format.lower() not in ALLOWED_EXTENSIONS:
        return safe_return(False, message=f"不支持的目标格式: {target_format}")

    try:
        image = Image.open(io.BytesIO(image_bytes))

        # RGBA 转 RGB（JPEG 不支持透明通道）
        if target_format.lower() in ("jpg", "jpeg") and image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background

        output_buffer = io.BytesIO()
        fmt = "JPEG" if target_format.upper() == "JPG" else target_format.upper()
        image.save(output_buffer, format=fmt)
        output_bytes = output_buffer.getvalue()

        return safe_return(True, data={
            "original_format": image.format or "unknown",
            "target_format": target_format.upper(),
            "output_size_bytes": len(output_bytes)
        }, message=f"已转换为 {target_format.upper()}")

    except Exception as e:
        return safe_return(False, message=f"格式转换失败: {str(e)}")


# ============================================
#  图片信息提取
# ============================================

def get_image_info(image_bytes: bytes) -> dict:
    """
    提取图片的基本信息：尺寸、格式、模式、DPI 等。

    API: POST /api/image/info
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        info = {
            "format": image.format or "unknown",
            "mode": image.mode,
            "size": list(image.size),
            "width": image.width,
            "height": image.height,
        }

        # DPI 信息（如果有）
        dpi = image.info.get("dpi")
        if dpi:
            info["dpi"] = list(dpi)

        # EXIF 信息（如果有）
        exif_data = image.getexif()
        if exif_data:
            info["has_exif"] = True
            # 提取常见的 EXIF 标签
            for tag_id, value in exif_data.items():
                if tag_id == 271:   # Make（相机制造商）
                    info["camera_make"] = str(value)
                elif tag_id == 272:  # Model（相机型号）
                    info["camera_model"] = str(value)
                elif tag_id == 306:  # DateTime（拍摄时间）
                    info["datetime"] = str(value)

        return safe_return(True, data=info, message="图片信息提取完成")

    except Exception as e:
        return safe_return(False, message=f"信息提取失败: {str(e)}")
