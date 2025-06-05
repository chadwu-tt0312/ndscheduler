"""A job to run executable programs."""

import logging
import platform
from subprocess import call

from ndscheduler.corescheduler import job

logger = logging.getLogger(__name__)


class ShellJob(job.JobBase):
    @classmethod
    def meta_info(cls):
        return {
            "job_class_string": "%s.%s" % (cls.__module__, cls.__name__),
            "notes": (
                "This will run an executable program. You can specify as many "
                "arguments as you want. This job will pass these arguments to the "
                "program in order. On Windows, built-in commands like 'dir' are supported."
            ),
            "arguments": [{"type": "string", "description": "Executable path"}],
            "example_arguments": (
                '["uv","run","--with","cowsay","python","-c","from cowsay import cow; cow(\\"hello, world\\")" \
                    ,"--mode","safe"]',
                '["/usr/local/my_app", "--file", "/tmp/abc", "--mode", "safe"]',
                '["ls", "-al"]',
                '["dir"]',
            ),
        }

    def run(self, *args, **kwargs):
        logger.info("ShellJob.run() called.")
        logger.info(f"  Received *args: {args} (type: {type(args)}, len: {len(args)})")
        logger.info(f"  Received **kwargs: {kwargs} (type: {type(kwargs)})")
        print(f"run shell job: {args}")

        # 檢測是否為 Windows 系統
        is_windows = platform.system().lower() == "windows"

        # Windows 內建命令列表
        windows_builtin_commands = {
            "dir",
            "cd",
            "copy",
            "del",
            "type",
            "echo",
            "cls",
            "md",
            "mkdir",
            "rd",
            "rmdir",
            "ren",
            "rename",
            "move",
            "attrib",
            "find",
            "findstr",
            "sort",
            "more",
            "tree",
            "vol",
            "date",
            "time",
            "ver",
            "set",
            "path",
        }

        try:
            # 如果是 Windows 且第一個參數是內建命令，使用 shell=True
            if is_windows and len(args) > 0 and args[0].lower() in windows_builtin_commands:
                logger.info(f"Executing Windows built-in command: {args[0]}")
                # 將參數組合成字串以便在 shell 中執行
                command_str = " ".join(args)
                returncode = call(command_str, shell=True)
            else:
                # 對於其他情況，使用原來的方式
                returncode = call(args)

            return {"command": args, "returncode": returncode}

        except Exception as e:
            logger.error(f"Error executing command {args}: {e}")
            # 如果第一次嘗試失敗且在 Windows 上，嘗試使用 shell=True
            if is_windows:
                try:
                    logger.info("Retrying with shell=True")
                    command_str = " ".join(args)
                    returncode = call(command_str, shell=True)
                    return {"command": args, "returncode": returncode}
                except Exception as e2:
                    logger.error(f"Second attempt also failed: {e2}")
                    raise e2
            else:
                raise e


if __name__ == "__main__":
    # You can easily test this job here
    job = ShellJob.create_test_instance()
    if platform.system().lower() == "windows":
        job.run("dir")
    else:
        job.run("ls", "-l")
