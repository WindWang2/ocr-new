"""
通用仪器读数识别脚本
支持任意仪器图片的读数识别
"""

import os
import sys
import logging
from pathlib import Path
from instrument_reader import InstrumentReader
from visualizer import InstrumentVisualizer

# 全局可视化器实例，避免重复初始化
_visualizer = None
def get_visualizer():
    global _visualizer
    if _visualizer is None:
        _visualizer = InstrumentVisualizer(font_size=26)
    return _visualizer


def read_single_image(image_path: str, output_json: str = None, verbose: bool = True,
                      reader: 'InstrumentReader' = None, no_visual: bool = False):
    """
    读取单张仪器图片的读数

    Args:
        image_path: 图片路径（支持绝对路径和相对路径）
        output_json: 输出JSON文件路径（可选）
        verbose: 是否显示详细信息
        reader: 可复用的InstrumentReader实例（可选，避免重复初始化）
        no_visual: 是否跳过可视化

    Returns:
        识别结果字典
    """
    image_path = Path(image_path)

    if not image_path.exists():
        print(f"[FAIL] 错误: 图片文件不存在: {image_path}")
        return None

    if verbose:
        print(f"\n处理图片: {image_path}")
        print("="*60)

    try:
        if reader is None:
            reader = InstrumentReader()

        result = reader.read_instrument(str(image_path))

        if result.get("success"):
            if verbose:
                print(f"\n[OK] 识别成功")
                print(f"  仪器类型: {result.get('instrument_name', '未知')}")
                print(f"  识别方法: {result.get('method', 'unknown')}")
                print(f"  类型置信度: {result.get('type_confidence', 0):.2f}")

                readings = result.get("readings", {})
                if readings:
                    print(f"\n  读数:")
                    from instrument_reader import DynamicInstrumentLibrary
                    instrument_type = result.get("instrument_type", "")
                    template = DynamicInstrumentLibrary.get_template(instrument_type)
                    unit_map = {}
                    if template:
                        unit_map = {f.get("name"): f.get("unit", "") for f in template.get("fields", [])}
                    for attr, value in readings.items():
                        if value is not None:
                            unit = unit_map.get(attr, "")
                            if unit:
                                print(f"    {attr}: {value} {unit}")
                            else:
                                print(f"    {attr}: {value}")
        else:
            if verbose:
                print(f"\n[FAIL] 识别失败: {result.get('error', '未知错误')}")

        # 保存JSON
        if output_json:
            import json
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if verbose:
                print(f"\n[OK] 结果已保存到: {output_json}")

        # 保存可视化标注图片
        if not no_visual:
            if output_json:
                # 如果指定了output_json，将图片保存到同目录
                output_path = Path(output_json).parent / f"annotated_{image_path.name}"
            else:
                # 否则保存到output目录
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"annotated_{image_path.name}"

            visualizer = get_visualizer()
            visualizer.visualize_result(
                str(image_path),
                result,
                str(output_path)
            )
            if verbose:
                print(f"[OK] 标注图片已保存到: {output_path}")

        return result

    except Exception as e:
        if verbose:
            print(f"\n[FAIL] 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
        return None


def batch_read_images(image_paths: list, output_dir: str = "output", no_visual: bool = False):
    """
    批量读取多张图片

    Args:
        image_paths: 图片路径列表
        output_dir: 输出目录
        no_visual: 是否跳过可视化

    Returns:
        识别结果列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"\n批量处理 {len(image_paths)} 张图片")
    print("="*60)

    reader = InstrumentReader()
    results = []

    for i, image_path in enumerate(image_paths, 1):
        image_path = Path(image_path)

        if not image_path.exists():
            print(f"\n[{i}/{len(image_paths)}] [FAIL] 跳过: {image_path} (文件不存在)")
            continue

        print(f"\n[{i}/{len(image_paths)}] 处理: {image_path.name}")
        print("-"*60)

        try:
            result = reader.read_instrument(str(image_path))
            result["image_file"] = str(image_path)
            results.append(result)

            if result.get("success"):
                print(f"[OK] 仪器: {result.get('instrument_name', '未知')}")
                readings = result.get("readings", {})
                for attr, value in readings.items():
                    if value is not None:
                        print(f"  {attr}: {value}")
            else:
                print(f"[FAIL] 失败: {result.get('error', '未知')}")

            # 保存JSON
            json_path = output_dir / f"{image_path.stem}_result.json"
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 保存可视化标注图片
            if not no_visual:
                output_image_path = output_dir / f"annotated_{image_path.name}"
                visualizer = get_visualizer()
                visualizer.visualize_result(
                    str(image_path),
                    result,
                    str(output_image_path)
                )
                print(f"[OK] 标注图片已保存到: {output_image_path}")

        except Exception as e:
            print(f"[FAIL] 异常: {str(e)}")
            results.append({
                "success": False,
                "error": str(e),
                "image_file": str(image_path)
            })

    print("\n" + "="*60)
    print(f"完成！成功: {sum(1 for r in results if r.get('success'))}/{len(results)}")
    print(f"结果已保存到: {output_dir.absolute()}")

    return results


def read_directory(directory: str, output_dir: str = "output", no_visual: bool = False):
    """
    读取目录中的所有图片

    Args:
        directory: 图片目录
        output_dir: 输出目录
        no_visual: 是否跳过可视化

    Returns:
        识别结果列表
    """
    directory = Path(directory)

    if not directory.exists():
        print(f"[FAIL] 错误: 目录不存在: {directory}")
        return []

    # 查找所有图片（使用集合去重，避免Windows大小写不敏感导致重复）
    image_files = set()
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        image_files.update(directory.glob(f"*{ext}"))
        image_files.update(directory.glob(f"*{ext.upper()}"))

    if not image_files:
        print(f"[FAIL] 错误: 目录中没有找到图片: {directory}")
        return []

    # 转为列表并排序
    image_files = sorted(image_files, key=lambda x: x.name.lower())
    print(f"找到 {len(image_files)} 张图片")

    return batch_read_images([str(f) for f in image_files], output_dir, no_visual=no_visual)


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("仪器读数识别系统 - 交互式模式")
    print("="*60)

    while True:
        print("\n选择操作:")
        print("1. 读取单张图片")
        print("2. 批量读取多张图片")
        print("3. 读取整个文件夹")
        print("4. 退出")

        choice = input("\n请选择 (1/2/3/4): ").strip()

        if choice == "1":
            image_path = input("请输入图片路径: ").strip()
            if not image_path:
                print("[FAIL] 路径不能为空")
                continue

            output_json = input("输出JSON文件路径 (直接回车跳过): ").strip()
            if not output_json:
                output_json = None

            read_single_image(image_path, output_json)

        elif choice == "2":
            print("\n输入图片路径（每行一个，空行结束）:")
            image_paths = []
            while True:
                path = input().strip()
                if not path:
                    break
                image_paths.append(path)

            if not image_paths:
                print("[FAIL] 未输入任何路径")
                continue

            output_dir = input("输出目录 (直接回车使用 'output'): ").strip()
            if not output_dir:
                output_dir = "output"

            batch_read_images(image_paths, output_dir)

        elif choice == "3":
            directory = input("请输入目录路径: ").strip()
            if not directory:
                print("[FAIL] 路径不能为空")
                continue

            output_dir = input("输出目录 (直接回车使用 'output'): ").strip()
            if not output_dir:
                output_dir = "output"

            read_directory(directory, output_dir)

        elif choice == "4":
            print("\n退出")
            break
        else:
            print("[FAIL] 无效选择")


def main():
    """主函数"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="仪器读数识别系统 - 支持任意仪器图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 读取单张图片
  python read_instrument.py image.jpg

  # 读取并保存JSON
  python read_instrument.py image.jpg -o result.json

  # 批量读取
  python read_instrument.py img1.jpg img2.jpg img3.jpg

  # 读取整个文件夹
  python read_instrument.py --dir ./images

  # 交互式模式
  python read_instrument.py -i
        """
    )

    parser.add_argument('images', nargs='*', help='图片文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径（单图）或输出目录（批量）')
    parser.add_argument('-d', '--dir', help='读取整个文件夹')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互式模式')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')
    parser.add_argument('--no-visual', action='store_true',
                        help='关闭可视化，不生成标注图片（默认生成）')

    args = parser.parse_args()

    # 交互式模式
    if args.interactive:
        interactive_mode()
        return

    # 读取文件夹
    if args.dir:
        output_dir = args.output or "output"
        read_directory(args.dir, output_dir, no_visual=args.no_visual)
        return

    # 读取图片
    if args.images:
        if len(args.images) == 1:
            # 单张图片
            output_json = args.output
            read_single_image(args.images[0], output_json, verbose=not args.quiet, no_visual=args.no_visual)
        else:
            # 多张图片
            output_dir = args.output or "output"
            batch_read_images(args.images, output_dir, no_visual=args.no_visual)
        return

    # 没有参数，显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
