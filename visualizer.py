"""
可视化模块
在仪器图片上标注识别结果和读数，简洁清晰风格
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from instrument_reader import InstrumentReader, InstrumentLibrary


class InstrumentVisualizer:
    """仪器识别结果可视化器 - 简洁清晰风格"""

    def __init__(self, font_size: int = 20):
        """
        初始化可视化器
        Args:
            font_size: 主字体大小
        """
        self.font_size = font_size
        self.small_font_size = int(font_size * 0.75)
        self.title_font_size = int(font_size * 1.1)

        # 加载不同大小的字体
        self.font = self._load_chinese_font(font_size)
        self.small_font = self._load_chinese_font(self.small_font_size)
        self.title_font = self._load_chinese_font(self.title_font_size)

        # 简洁配色方案
        self.colors = {
            # 主文本色
            'text_white': (255, 255, 255, 255),
            'text_black': (0, 0, 0, 255),
            'text_green': (76, 175, 80, 255),   # 成功绿
            'text_orange': (255, 111, 0, 255),  # 活力橙
            'text_blue': (33, 150, 243, 255),   # 蓝色

            # 背景色（低透明度，不遮挡原图）
            'bg_black': (0, 0, 0, 180),    # 黑色半透明
            'bg_green': (76, 175, 80, 160),
            'bg_orange': (255, 111, 0, 160),
            'bg_red': (244, 67, 54, 180),
        }

    def _load_chinese_font(self, size: int):
        """加载中文字体（跨平台支持 Windows / Mac / Linux）"""
        import platform
        system = platform.system()

        font_paths = []

        if system == "Windows":
            # Windows 字体路径 - 全面覆盖
            windir = Path(os.environ.get("WINDIR", "C:/Windows"))
            fonts_dir = windir / "Fonts"
            font_paths = [
                str(fonts_dir / "msyh.ttc"),       # 微软雅黑
                str(fonts_dir / "msyhbd.ttc"),     # 微软雅黑粗体
                str(fonts_dir / "simhei.ttf"),     # 黑体
                str(fonts_dir / "simsun.ttc"),     # 宋体
                str(fonts_dir / "simkai.ttf"),     # 楷体
                str(fonts_dir / "simfang.ttf"),    # 仿宋
                str(fonts_dir / "msjhl.ttc"),      # 微软雅黑亮黑
            ]
        elif system == "Darwin":
            # macOS 字体路径
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",          # 苹方
                "/System/Library/Fonts/STHeiti Medium.ttc",    # 黑体
                "/System/Library/Fonts/STSong.ttc",            # 宋体
                "/System/Library/Fonts/Kai.ttc",               # 楷体
                "/Library/Fonts/Arial Unicode MS.ttf",         # Arial Unicode
                "/System/Library/Fonts/HelveticaNeue.ttc",      # Helvetica
            ]
        else:
            # Linux 字体路径（包括 WSL2 常见路径）
            font_paths = [
                # WSL2 / Debian / Ubuntu 文泉驿字体
                "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc",
                "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
                # 传统 truetype 路径
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                # Noto CJK 字体
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                # Droid 回退字体
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                # AR PL 字体
                "/usr/share/fonts/truetype/arphic/uming.ttc",
                "/usr/share/fonts/truetype/arphic/ukai.ttc",
            ]

        # 尝试加载指定字体
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    print(f"✅ 加载字体成功: {os.path.basename(font_path)}")
                    return font
            except (IOError, OSError) as e:
                continue

        # 尝试加载默认字体
        try:
            return ImageFont.truetype("arial.ttf", size)
        except (IOError, OSError):
            try:
                return ImageFont.load_default(size=size)
            except:
                print("⚠️  无法加载中文字体，中文可能显示为方框，请安装中文字体包")
                return ImageFont.load_default()

    def visualize_result(self,
                        image_path: str,
                        result: Dict[str, Any],
                        output_path: str = None,
                        show_confidence: bool = True) -> np.ndarray:
        """
        在图片上可视化识别结果（简洁风格）
        Args:
            image_path: 输入图片路径
            result: 识别结果字典
            output_path: 输出图片路径（可选）
            show_confidence: 是否显示置信度
        Returns:
            标注后的图片（numpy数组）
        """
        # 使用 numpy + cv2.imdecode 读取图片，避免 cv2.imread 不支持非ASCII路径的问题
        image = cv2.imdecode(
            np.fromfile(str(image_path), dtype=np.uint8),
            cv2.IMREAD_COLOR
        )
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # 创建带alpha通道的图层
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if result.get("success"):
            # 准备标注文本
            data = self._prepare_annotation_texts(result, show_confidence)

            # 绘制精简标注 - 左上角位置
            self._draw_simple_annotations(draw, data, pil_image.size)
        else:
            # 绘制错误信息
            error_text = f"识别失败: {result.get('error', '未知错误')}"
            self._draw_simple_error(draw, error_text, pil_image.size)

        # 合并图层
        combined = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
        image_annotated = cv2.cvtColor(np.array(combined), cv2.COLOR_RGBA2BGR)

        if output_path:
            # 使用 cv2.imencode + tofile 保存，避免 cv2.imwrite 不支持非ASCII路径
            ext = Path(output_path).suffix
            success, buf = cv2.imencode(ext, image_annotated)
            if success:
                buf.tofile(str(output_path))
            print(f"✓ 已保存标注图片: {output_path}")

        return image_annotated

    def _prepare_annotation_texts(self, result: Dict[str, Any], show_confidence: bool) -> Dict[str, Any]:
        """准备标注文本数据"""
        instrument_type = result.get("instrument_type", "unknown")
        instrument_name = result.get("instrument_name", "未知仪器")
        method = result.get("method", "unknown")
        confidence = result.get("confidence", 0)

        # 获取读数
        readings = []
        readings_data = result.get("readings", {})
        if readings_data:
            instrument_info = InstrumentLibrary.INSTRUMENTS.get(instrument_type, {})
            units = instrument_info.get("unit", {})

            for attr, value in readings_data.items():
                if value is not None:
                    unit = units.get(attr, "")
                    readings.append({
                        "label": attr,
                        "value": str(value),
                        "unit": unit
                    })

        return {
            "instrument_name": instrument_name,
            "method": method,
            "confidence": confidence,
            "readings": readings,
            "show_confidence": show_confidence
        }

    def _draw_simple_annotations(self, draw: ImageDraw.Draw, data: Dict[str, Any], image_size: Tuple[int, int]):
        """绘制精简风格的标注，左上角位置，不遮挡重要内容"""
        width, height = image_size

        padding = 12
        line_height = self.font_size + 6
        small_line_height = self.small_font_size + 5

        # 左上角位置 - 不会遮挡仪器读数区域
        x = padding
        y = padding

        current_y = y

        # 仪器名称标题 - 带小背景
        title_text = f"📊 {data['instrument_name']}"
        bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
        title_width = bbox[2] - bbox[0]
        title_height = bbox[3] - bbox[1]

        draw.rectangle(
            [(x - 6, current_y - 3), (x + title_width + 6, current_y + title_height + 3)],
            fill=self.colors['bg_green']
        )
        draw.text((x, current_y), title_text, font=self.title_font, fill=self.colors['text_white'])
        current_y += line_height + 6

        # 置信度
        if data["show_confidence"]:
            conf = data["confidence"]
            conf_text = f"置信度: {conf:.2f}"
            draw.text((x, current_y), conf_text, font=self.small_font, fill=self.colors['text_blue'])
            current_y += small_line_height + 3

        # 读数
        if data["readings"]:
            # 读数标题
            draw.text((x, current_y), "📈 读数:", font=self.font, fill=self.colors['text_orange'])
            current_y += small_line_height + 3

            # 读数列表
            for reading in data["readings"]:
                value_text = f"• {reading['label']}: {reading['value']} {reading['unit']}".strip()
                draw.text((x + 10, current_y), value_text, font=self.font, fill=self.colors['text_orange'])
                current_y += small_line_height

    def _draw_simple_error(self, draw: ImageDraw.Draw, error_text: str, image_size: Tuple[int, int]):
        """绘制精简风格的错误提示"""
        width, height = image_size

        padding = 12
        line_height = self.font_size + 6

        # 左上角位置
        x = padding
        y = padding

        # 错误标题
        title_text = "❌ 识别失败"
        bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
        title_width = bbox[2] - bbox[0]
        title_height = bbox[3] - bbox[1]

        draw.rectangle(
            [(x - 6, y - 3), (x + title_width + 6, y + title_height + 3)],
            fill=self.colors['bg_red']
        )
        draw.text((x, y), title_text, font=self.title_font, fill=self.colors['text_white'])
        y += line_height + 6

        # 错误信息
        draw.text((x, y), error_text, font=self.font, fill=self.colors['text_black'])

    def visualize_batch(self, image_dir: str, output_dir: str = "output") -> List[str]:
        """
        批量可视化图片
        Args:
            image_dir: 输入图片目录
            output_dir: 输出目录
        Returns:
            输出图片路径列表
        """
        image_dir = Path(image_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        reader = InstrumentReader()

        image_files = []
        for ext in ['*.jpg', '*.png', '*.jpeg', '*.bmp']:
            image_files.extend(image_dir.glob(ext))
            image_files.extend(image_dir.glob(ext.upper()))

        if not image_files:
            print(f"未找到图片文件: {image_dir}")
            return []

        print(f"\n处理 {len(image_files)} 张图片...")
        print("="*60)

        output_paths = []

        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 处理: {image_file.name}")

            try:
                result = reader.read_instrument(str(image_file))
                output_path = output_dir / f"annotated_{image_file.name}"

                self.visualize_result(
                    str(image_file),
                    result,
                    str(output_path),
                    show_confidence=True
                )

                output_paths.append(str(output_path))

                if result.get("success"):
                    print(f"  ✓ 仪器: {result.get('instrument_name', 'unknown')}")
                    readings = result.get("readings", {})
                    for attr, value in readings.items():
                        if value is not None:
                            print(f"    {attr}: {value}")

            except Exception as e:
                print(f"  ✗ 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()

        print("\n" + "="*60)
        print(f"完成！共处理 {len(output_paths)} 张图片")
        print(f"输出目录: {output_dir.absolute()}")

        return output_paths


def visualize_single_image(image_path: str, output_path: str = None, show: bool = True):
    """
    快速可视化单张图片
    Args:
        image_path: 图片路径
        output_path: 输出路径（可选）
        show: 是否显示图片
    """
    print(f"\n处理图片: {image_path}")
    print("="*60)

    reader = InstrumentReader()
    result = reader.read_instrument(image_path)

    visualizer = InstrumentVisualizer(font_size=22)

    if output_path is None:
        input_path = Path(image_path)
        output_path = str(input_path.parent / f"annotated_{input_path.name}")

    annotated_image = visualizer.visualize_result(
        image_path,
        result,
        output_path,
        show_confidence=True
    )

    if result.get("success"):
        print(f"\n✓ 识别成功")
        print(f"  仪器: {result.get('instrument_name', 'unknown')}")
        print(f"  读数:")
        for attr, value in result.get("readings", {}).items():
            if value is not None:
                print(f"    {attr}: {value}")
    else:
        print(f"\n✗ 识别失败: {result.get('error', 'unknown')}")

    if show:
        cv2.imshow("Instrument Reading", annotated_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return result


def main():
    """主函数"""
    import sys

    print("\n" + "="*60)
    print("🎨 仪器识别可视化工具")
    print("="*60)

    print("\n选择模式:")
    print("1. 可视化单张图片")
    print("2. 批量可视化demo文件夹")
    print("3. 退出")

    choice = input("\n请选择 (1/2/3): ")

    if choice == "1":
        image_path = input("\n请输入图片路径 (直接回车使用demo/im009.jpg): ").strip()
        if not image_path:
            image_path = "demo/im009.jpg"

        output_path = input("请输入输出路径 (直接回车自动生成): ").strip()
        if not output_path:
            output_path = None

        visualize_single_image(image_path, output_path, show=False)

    elif choice == "2":
        image_dir = input("\n请输入图片目录 (直接回车使用demo): ").strip()
        if not image_dir:
            image_dir = "demo"

        output_dir = input("请输入输出目录 (直接回车使用output): ").strip()
        if not output_dir:
            output_dir = "output"

        visualizer = InstrumentVisualizer(font_size=20)
        visualizer.visualize_batch(image_dir, output_dir)

    else:
        print("\n退出")
        return

    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)


if __name__ == "__main__":
    main()
