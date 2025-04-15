"""A sample job that prints string."""

from ndscheduler.corescheduler import job


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

    def run(self, argument1=None, argument2=None, *args, **kwargs):
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
