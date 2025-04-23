"""A job to run executable programs."""

import logging
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
                "program in order."
            ),
            "arguments": [{"type": "string", "description": "Executable path"}],
            "example_arguments": (
                '["uv","run","--with","cowsay","python","-c","from cowsay import cow; cow(\\"hello, world\\")" \
                    ,"--mode","safe"]',
                '["/usr/local/my_app", "--file", "/tmp/abc", "--mode", "safe"]',
                '["ls", "-al"]',
            ),
        }

    def run(self, *args, **kwargs):
        logger.info("ShellJob.run() called.")
        logger.info(f"  Received *args: {args} (type: {type(args)}, len: {len(args)})")
        logger.info(f"  Received **kwargs: {kwargs} (type: {type(kwargs)})")
        print(f"run shell job: {args}")
        return {"command": args, "returncode": call(args)}


if __name__ == "__main__":
    # You can easily test this job here
    job = ShellJob.create_test_instance()
    job.run("ls", "-l")
