"""A job to execute Python code from files or strings."""

import logging
import os
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

from ndscheduler.corescheduler import job

logger = logging.getLogger(__name__)


class PythonJob(job.JobBase):
    @classmethod
    def meta_info(cls):
        return {
            "job_class_string": "%s.%s" % (cls.__module__, cls.__name__),
            "notes": (
                "This job can execute Python code from files or strings. "
                "It supports dependency checking and can run Python scripts "
                "with optional arguments. Use 'file' mode to execute .py files "
                "or 'str' mode to execute Python code strings directly. "
                "Use --pythonexe to specify a custom Python executable (e.g., virtual environment)."
            ),
            "arguments": [
                {"type": "string", "description": "Execution mode: 'file' or 'str'"},
                {
                    "type": "string",
                    "description": "Python file path (for 'file' mode) or Python code string (for 'str' mode)",
                },
            ],
            "example_arguments": (
                '["file", "test_python_job.py", "--arg1", "value1"]',
                '["file", "path/to/script.py"]',
                '["file", "path/to/script.py", "--pythonexe", "/path/to/venv/bin/python"]',
                '["str", "import datetime; print(datetime.datetime.now())", "--pythonexe", "D:/_Code/project/.venv/Scripts/python.exe"]',
                '["str", "import sys; print(f\\"Python version: {sys.version}\\")"]',
            ),
        }

    def _check_dependencies(self, code_content: str) -> Dict[str, Any]:
        """檢查程式碼中的依賴套件"""
        dependencies = {"imports": [], "missing_packages": [], "available_packages": []}

        try:
            # 解析 import 語句
            import ast

            tree = ast.parse(code_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies["imports"].append(node.module)

            # 檢查套件是否可用
            for package in dependencies["imports"]:
                # 處理子模組 (例如 os.path -> os)
                root_package = package.split(".")[0]
                try:
                    importlib.util.find_spec(root_package)
                    dependencies["available_packages"].append(root_package)
                except (ImportError, ModuleNotFoundError, ValueError):
                    dependencies["missing_packages"].append(root_package)

        except SyntaxError as e:
            logger.warning(f"語法錯誤，無法解析依賴: {e}")
        except Exception as e:
            logger.warning(f"依賴檢查失敗: {e}")

        return dependencies

    def _execute_python_file(self, file_path: str, args: List[str] = None) -> Dict[str, Any]:
        """執行 Python 檔案"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Python 檔案不存在: {file_path}")

        if not file_path.endswith(".py"):
            raise ValueError(f"檔案必須是 .py 格式: {file_path}")

        # 讀取檔案內容進行依賴檢查
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()

        dependencies = self._check_dependencies(code_content)

        # 解析參數，檢查是否有自訂 Python 執行檔
        python_executable = sys.executable
        script_args = []

        if args:
            # 尋找 --pythonexe 參數
            i = 0
            while i < len(args):
                if args[i] == "--pythonexe" and i + 1 < len(args):
                    python_executable = args[i + 1]
                    # 驗證 Python 執行檔是否存在
                    if not os.path.exists(python_executable):
                        raise FileNotFoundError(f"指定的 Python 執行檔不存在: {python_executable}")
                    i += 2  # 跳過 --pythonexe 和其值
                else:
                    script_args.append(args[i])
                    i += 1

        # 準備執行命令
        cmd = [python_executable, file_path]
        if script_args:
            cmd.extend(script_args)

        logger.info(f"執行 Python 檔案: {' '.join(cmd)}")

        try:
            # 執行 Python 檔案
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分鐘超時
                cwd=os.path.dirname(os.path.abspath(file_path)) if os.path.dirname(file_path) else None,
            )

            return {
                # "python_executable": python_executable,
                # "file_path": file_path,
                "command": cmd,
                "script_args": script_args,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "dependencies": dependencies,
            }

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Python 檔案執行超時: {file_path}")
        except Exception as e:
            raise RuntimeError(f"執行 Python 檔案失敗: {e}")

    def _execute_python_string(self, code_string: str, python_executable: str = None) -> Dict[str, Any]:
        """執行 Python 字串程式碼"""
        dependencies = self._check_dependencies(code_string)

        # 使用指定的 Python 執行檔或預設值
        if python_executable is None:
            python_executable = sys.executable

        # 驗證 Python 執行檔是否存在
        if not os.path.exists(python_executable):
            raise FileNotFoundError(f"指定的 Python 執行檔不存在: {python_executable}")

        # 建立臨時檔案
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code_string)
            temp_file_path = temp_file.name

        try:
            logger.info(f"執行 Python 字串程式碼 (臨時檔案: {temp_file_path})")
            logger.info(f"使用 Python 執行檔: {python_executable}")

            # 執行臨時檔案
            result = subprocess.run(
                [python_executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 分鐘超時
            )

            cmd = [python_executable, temp_file_path]
            return {
                "code_string": code_string[:200] + "..." if len(code_string) > 200 else code_string,
                # "python_executable": python_executable,
                # "temp_file": temp_file_path,
                "command": cmd,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "dependencies": dependencies,
            }

        except subprocess.TimeoutExpired:
            raise TimeoutError("Python 字串程式碼執行超時")
        except Exception as e:
            raise RuntimeError(f"執行 Python 字串程式碼失敗: {e}")
        finally:
            # 清理臨時檔案
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"清理臨時檔案失敗: {e}")

    def run(self, mode: str, content: str, *args, **kwargs) -> Dict[str, Any]:
        """執行 Python 作業

        Args:
            mode: 執行模式 ('file' 或 'str')
            content: Python 檔案路徑或程式碼字串
            *args: 額外參數 (僅用於 file 模式)
            **kwargs: 關鍵字參數

        Returns:
            Dict: 執行結果
        """
        logger.info("PythonJob.run() called.")
        logger.info(f"  Received mode: {mode}")
        logger.info(f"  Received content: {content[:100]}{'...' if len(content) > 100 else ''}")
        logger.info(f"  Received *args: {args} (type: {type(args)}, len: {len(args)})")
        logger.info(f"  Received **kwargs: {kwargs} (type: {type(kwargs)})")

        if mode not in ["file", "str"]:
            raise ValueError(f"不支援的執行模式: {mode}. 請使用 'file' 或 'str'")

        try:
            if mode == "file":
                return self._execute_python_file(content, list(args) if args else None)
            elif mode == "str":
                # 檢查字串模式是否有 --pythonexe 參數
                python_executable = None
                if args:
                    args_list = list(args)
                    i = 0
                    while i < len(args_list):
                        if args_list[i] == "--pythonexe" and i + 1 < len(args_list):
                            python_executable = args_list[i + 1]
                            break
                        i += 1

                    if python_executable is None:
                        logger.warning("字串模式僅支援 --pythonexe 參數，其他參數將被忽略")

                return self._execute_python_string(content, python_executable)

        except Exception as e:
            logger.error(f"PythonJob 執行失敗: {e}")
            return {
                "mode": mode,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "error": str(e),
                "returncode": -1,
                "dependencies": {"imports": [], "missing_packages": [], "available_packages": []},
            }


if __name__ == "__main__":
    # 測試用例
    job = PythonJob.create_test_instance()

    # 測試字串模式
    print("=== 測試字串模式 ===")
    result1 = job.run(
        "str", "import os; print(f'Current TZ: {os.getenv(\"TZ\", \"Not set\")}'); print('Hello from Python!')"
    )
    print(f"結果: {result1}")

    # 測試檔案模式 (如果存在測試檔案)
    print("\n=== 測試檔案模式 ===")
    test_script = """
import sys
import datetime
print(f"Python version: {sys.version}")
print(f"Current time: {datetime.datetime.now()}")
print("Test script executed successfully!")
"""

    # 建立測試檔案
    test_file_path = "test_python_job.py"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_script)

    try:
        result2 = job.run("file", test_file_path)
        print(f"結果: {result2}")
    finally:
        # 清理測試檔案
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
