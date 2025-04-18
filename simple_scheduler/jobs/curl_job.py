"""A job to send a HTTP (GET or DELETE) periodically."""

import logging
import requests

from ndscheduler.corescheduler import job

logger = logging.getLogger(__name__)


class CurlJob(job.JobBase):
    TIMEOUT = 10

    @classmethod
    def meta_info(cls):
        return {
            "job_class_string": "%s.%s" % (cls.__module__, cls.__name__),
            "notes": "This sends a HTTP request to a particular URL",
            "arguments": [
                # url
                {
                    "type": "string",
                    "description": "What URL you want to make a GET call?",
                },
                # Request Type
                {
                    "type": "string",
                    "description": "What request type do you want? " "(currently supported: GET/DELETE)",
                },
            ],
            "example_arguments": (
                '["http://localhost:5678/api/v1/health","GET"]',
                '["http://localhost:5678/api/v1/jsonrpc","POST", \
                  "{"jsonrpc": "2.0","method":"apiinfo.version","params":{},"id":1}"]',
                '["http://localhost:8888/api/v1/jobs", "GET"]',
                '["http://localhost:8888/api/v1/jobs/ba12e", "DELETE"]',
            ),
        }

    def run(self, url, request_type, *args, **kwargs):
        logger.info("CurlJob.run() called.")
        logger.info(f"  Received argument1: {url} (type: {type(url)})")
        logger.info(f"  Received argument2: {request_type} (type: {type(request_type)})")
        logger.info(f"  Received *args: {args} (type: {type(args)}, len: {len(args)})")
        logger.info(f"  Received **kwargs: {kwargs} (type: {type(kwargs)})")
        # logger.info("Calling %s on url: %s, data=%s" % (request_type, url, args))
        param = args[0] if args else None

        try:
            session = requests.Session()
            result = session.request(
                request_type,
                url,
                data=param,
                timeout=self.TIMEOUT,
                headers=None,
            )
            return result.text
        except ConnectionRefusedError:
            error_msg = "服務未啟動或端口未開啟，請確認服務狀態"
            logger.warning(f"{error_msg} - URL: {url}")
            return error_msg
        except Exception as e:
            logger.error(f"請求失敗 - URL: {url}, 錯誤: {str(e)}")
            raise


if __name__ == "__main__":
    job = CurlJob.create_test_instance()
    job.run("http://localhost:8888/api/v1/jobs")
