"""A sample job that prints string."""

import logging
from ndscheduler.corescheduler import job

logger = logging.getLogger(__name__)


class AwesomeJob(job.JobBase):

    @classmethod
    def meta_info(cls):
        return {
            "job_class_string": "%s.%s" % (cls.__module__, cls.__name__),
            "notes": "This will print a string in your shell. Check it out!",
            "arguments": [
                # argument1
                {"type": "string", "description": "First argument"},
                # argument2
                {"type": "string", "description": "Second argument"},
            ],
            "example_arguments": '["first argument AAA", "second argument BBB"]',
        }

    def run(self, *args, **kwargs):
        logger.info("AwesomeJob.run() called.")
        logger.info(f"  Received *args: {args} (type: {type(args)}, len: {len(args)})")
        logger.info(f"  Received **kwargs: {kwargs} (type: {type(kwargs)})")

        # --- 從 *args 中提取實際的 pub_args ---
        actual_pub_args = args
        # 檢查 args 是否意外包含了 db_config 和 db_tablenames
        if (
            len(args) >= 2
            and isinstance(args[0], dict)
            and "file_path" in args[0]  # 簡易判斷 db_config
            and isinstance(args[1], dict)
            and "jobs_tablename" in args[1]
        ):  # 簡易判斷 db_tablenames
            logger.warning(
                "Detected unexpected db_config and db_tablenames in *args. Extracting pub_args from index 2."
            )
            actual_pub_args = args[2:]  # 真正的 pub_args 從第3個元素開始
        else:
            logger.info("Assuming *args contains only pub_args.")

        # --- 從提取出的 actual_pub_args 中獲取參數 ---
        argument1 = actual_pub_args[0] if len(actual_pub_args) > 0 else None
        argument2 = actual_pub_args[1] if len(actual_pub_args) > 1 else None
        # --- 結束獲取參數 ---

        # 如果參數未傳入，設定為空字串
        argument1 = argument1 if argument1 is not None else ""
        argument2 = argument2 if argument2 is not None else ""

        print("Hello from AwesomeJob! Argument1: %s, Argument2: %s" % (argument1, argument2))
        return [argument1, argument2]


if __name__ == "__main__":
    # You can easily test this job here
    job = AwesomeJob.create_test_instance()
    # 測試不同的參數組合
    print("測試1：無參數")
    job.run()
    print("\n測試2：一個參數")
    job.run("自定義參數1")
    print("\n測試3：兩個參數")
    job.run("自定義參數123", "自定義參數456")
