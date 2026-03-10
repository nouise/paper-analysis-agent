import base64
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

if __name__ == "__main__":
    import typer
    from loguru import logger
else:
    from src.utils import logger


class PaddleXLayoutParser:
    """PaddleX 版面解析服务客户端"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/layout-parsing"

    def encode_file_to_base64(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("utf-8")
            return encoded

    def _process_file_input(self, file_input: str) -> str:
        # 检查是否为本地文件路径
        if os.path.exists(file_input):
            logger.info(f"[文件] 检测到本地文件: {file_input}")
            logger.info(f"[大小] 文件大小: {os.path.getsize(file_input) / 1024 / 1024:.2f} MB")

            try:
                # 将本地文件编码为Base64
                encoded_content = self.encode_file_to_base64(file_input)
                logger.info(f"[完成] 文件已编码为Base64，长度: {len(encoded_content)} 字符")
                return encoded_content
            except Exception as e:
                logger.error(f"[错误] 文件编码失败: {e}")
                raise

        # 检查是否为URL
        elif file_input.startswith(("http://", "https://")):
            logger.info(f"[网络] 检测到URL: {file_input}")
            return file_input

        # 否则假设为Base64编码内容
        else:
            logger.info(f"[编辑] 假设为Base64编码内容，长度: {len(file_input)} 字符")
            return file_input

    def layout_parsing(
        self,
        file_input: str,
        file_type: int | None = None,
        use_textline_orientation: bool | None = None,
        use_seal_recognition: bool | None = None,
        use_table_recognition: bool | None = None,
        use_formula_recognition: bool | None = None,
        use_chart_recognition: bool | None = None,
        use_region_detection: bool | None = None,
        layout_threshold: float | None = None,
        layout_nms: bool | None = None,
        use_doc_orientation_classify: bool = True,
        use_doc_unwarping: bool | None = False,
        use_wired_table_cells_trans_to_html: bool = True,  # 启用则直接基于有线表单元格检测结果的几何关系构建HTML。
        **kwargs,
    ) -> dict[str, Any]:
        """
        调用版面解析API：https://paddlepaddle.github.io/PaddleX/latest/pipeline_usage/tutorials/ocr_pipelines/PP-StructureV3.html#22-python
        """
        # 处理文件输入：检测是否为本地文件路径
        processed_file_input = self._process_file_input(file_input)
        payload = {"file": processed_file_input}

        # 添加可选参数
        optional_params = {
            "fileType": file_type,
            "useDocOrientationClassify": use_doc_orientation_classify,
            "useDocUnwarping": use_doc_unwarping,
            "useTextlineOrientation": use_textline_orientation,
            "useSealRecognition": use_seal_recognition,
            "useTableRecognition": use_table_recognition,
            "useFormulaRecognition": use_formula_recognition,
            "useChartRecognition": use_chart_recognition,
            "useRegionDetection": use_region_detection,
            "layoutThreshold": layout_threshold,
            "layoutNms": layout_nms,
            "useWiredTableCellsTransToHtml": use_wired_table_cells_trans_to_html,
        }

        # 添加非空参数
        for key, value in optional_params.items():
            if value is not None:
                payload[key] = value

        # 添加其他kwargs参数
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        try:
            response = requests.post(
                self.endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("[完成] 请求成功!")
                return result
            else:
                logger.error(f"[错误] 请求失败! {self.endpoint}")
                try:
                    error_result = response.json()
                    logger.error(f"错误信息: {json.dumps(error_result, indent=2, ensure_ascii=False)}")
                    return error_result
                except Exception as e:
                    logger.error(f"响应内容: {response.text}")
                    return {"error": f"{e}: {response.text}", "status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            health_check_response = requests.get(f"{self.base_url}/health", timeout=5)
            logger.error(f"[错误] 网络请求异常: {e}: {health_check_response.json()}")
            return {"error": str(e)}

        except Exception as e:
            logger.error(f"[错误] 其他异常: {e}")
            return {"error": str(e)}


def _parse_recognition_result(api_result: dict[str, Any], file_path: str) -> dict[str, Any]:
    # 基本信息
    parsed_result = {
        "success": True,
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "log_id": api_result.get("logId"),
        "total_pages": 0,
        "pages": [],
        "full_text": "",
        "summary": {},
    }

    result_data = api_result.get("result", {})
    layout_results = result_data.get("layoutParsingResults", [])
    data_info = result_data.get("dataInfo", {})

    # 数据信息
    parsed_result["total_pages"] = len(layout_results)
    parsed_result["document_info"] = {
        "type": data_info.get("type", "unknown"),
        "total_pages": data_info.get("numPages", len(layout_results)),
        "page_dimensions": data_info.get("pages", []),
    }

    # 统计信息
    total_elements = 0
    total_tables = 0
    total_formulas = 0
    total_charts = 0
    total_seals = 0
    all_text_content = []

    # 解析每页结果
    for page_index, page_result in enumerate(layout_results):
        page_info = {"page_number": page_index + 1, "content": {}, "statistics": {}}

        # Markdown内容
        if "markdown" in page_result:
            markdown = page_result["markdown"]
            page_info["content"]["markdown_text"] = markdown.get("text", "")
            page_info["content"]["images"] = list(markdown.get("images", {}).keys())
            page_info["content"]["is_paragraph_start"] = markdown.get("isStart", False)
            page_info["content"]["is_paragraph_end"] = markdown.get("isEnd", False)

            # 收集文本内容
            if markdown.get("text"):
                all_text_content.append(markdown["text"])

        # 详细识别结果
        if "prunedResult" in page_result:
            pruned = page_result["prunedResult"]

            # 版面检测
            layout_detection = pruned.get("layout_detection", [])
            page_info["statistics"]["layout_elements"] = len(layout_detection)
            total_elements += len(layout_detection)

            # OCR结果
            ocr_result = pruned.get("ocr_result", [])
            page_info["statistics"]["ocr_elements"] = len(ocr_result)

            # 表格识别
            table_result = pruned.get("table_result", [])
            page_info["statistics"]["tables"] = len(table_result)
            total_tables += len(table_result)

            # 公式识别
            formula_result = pruned.get("formula_result", [])
            page_info["statistics"]["formulas"] = len(formula_result)
            total_formulas += len(formula_result)

            # 图表识别
            chart_result = pruned.get("chart_result", [])
            page_info["statistics"]["charts"] = len(chart_result)
            total_charts += len(chart_result)

            # 印章识别
            seal_result = pruned.get("seal_result", [])
            page_info["statistics"]["seals"] = len(seal_result)
            total_seals += len(seal_result)

            # 详细元素信息
            page_info["content"]["layout_elements"] = layout_detection
            page_info["content"]["ocr_elements"] = ocr_result
            page_info["content"]["tables"] = table_result
            page_info["content"]["formulas"] = formula_result
            page_info["content"]["charts"] = chart_result
            page_info["content"]["seals"] = seal_result

        parsed_result["pages"].append(page_info)

    # 汇总全文内容
    parsed_result["full_text"] = "\n\n".join(all_text_content)

    # 汇总统计信息
    parsed_result["summary"] = {
        "total_elements": total_elements,
        "total_tables": total_tables,
        "total_formulas": total_formulas,
        "total_charts": total_charts,
        "total_seals": total_seals,
        "total_characters": len(parsed_result["full_text"]),
        "average_elements_per_page": round(total_elements / max(1, len(layout_results)), 2),
    }

    return parsed_result


def analyze_document(file_path: str, base_url: str = "http://localhost:8080") -> dict[str, Any]:
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}", "file_path": file_path}

    # 初始化客户端
    client = PaddleXLayoutParser(base_url=base_url)

    # 判断文件类型
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == ".pdf":
        file_type = 0
    elif file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
        file_type = 1
    else:
        return {"success": False, "error": f"不支持的文件类型: {file_ext}", "file_path": file_path}

    logger.info(f"[文档] 开始分析文档: {os.path.basename(file_path)}")
    logger.info(f"[大小] 文件大小: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")
    logger.info(f"[类型] 文件类型: {'PDF' if file_type == 0 else '图片'}")

    try:
        # 调用API进行识别
        result = client.layout_parsing(file_input=file_path, file_type=file_type)

        # 检查API调用是否成功
        if result.get("errorCode") != 0:
            return {
                "success": False,
                "error": result.get("errorMsg", "API调用失败"),
                "file_path": file_path,
                "raw_result": result,
            }

        # 解析结果
        analysis_result = _parse_recognition_result(result, file_path)
        return analysis_result

    except Exception as e:
        return {"success": False, "error": f"处理异常: {str(e)}", "file_path": file_path}


def check_paddlex_health(base_url: str = "http://localhost:8080") -> bool:
    return requests.get(f"{base_url}/health", timeout=5)


def analyze_folder(input_dir: str, output_dir: str, base_url: str = "http://localhost:8080"):
    """分析文件夹中的所有支持文件，保存为txt格式"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"[错误] 输入目录不存在：{input_dir}")
        return

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有支持的文件
    supported_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    files = []
    for root, dirs, filenames in os.walk(input_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            if file_path.suffix.lower() in supported_extensions:
                files.append(file_path)

    if not files:
        print("[警告] 没有找到支持的文件")
        return

    print(f"[文件] 找到 {len(files)} 个文件")

    success_count = 0
    for i, file_path in enumerate(files, 1):
        print(f"[处理] [{i}/{len(files)}] {file_path.name}")

        try:
            # 分析文档
            result = analyze_document(str(file_path), base_url)

            if result.get("success"):
                # 保持目录结构
                relative_path = file_path.relative_to(input_path)
                output_file = output_path / relative_path.with_suffix(".txt")
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # 写入文本内容
                text_content = (
                    result.get("full_text", "未提取到内容")
                    if result.get("success")
                    else f"分析失败：{result.get('error', '未知错误')}"
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text_content)

                success_count += 1
                print(f"[完成] {output_file.name}")
            else:
                print(f"[错误] 失败: {result.get('error')}")

        except Exception as e:
            print(f"[错误] 异常: {str(e)}")

        time.sleep(0.5)

    print(f"\n[统计] 完成！成功: {success_count}, 总计: {len(files)}")


if __name__ == "__main__":
    app = typer.Typer(help="PaddleX 文档分析工具")

    @app.command()
    def single(file_path: str, base_url: str = "http://172.19.13.5:8080"):
        """分析单个文件"""
        result = analyze_document(file_path, base_url)
        if result["success"]:
            print(f"[完成] 成功提取 {len(result['full_text'])} 个字符")
        else:
            print(f"[错误] 失败: {result.get('error')}")

    @app.command()
    def folder(input_dir: str, output_dir: str, base_url: str = "http://172.19.13.5:8080"):
        """批量分析文件夹"""
        analyze_folder(input_dir, output_dir, base_url)

    app()
