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

        argument1 = args[0] if len(args) > 0 else None
        argument2 = args[1] if len(args) > 1 else None

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
