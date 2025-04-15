"""Settings to override default settings."""

import logging

#
# Override settings
#
DEBUG = True

HTTP_PORT = 8888
HTTP_ADDRESS = "0.0.0.0"

#
# Set logging level
#
logging.getLogger().setLevel(logging.DEBUG)

# Specify the package that contains job classes
JOB_CLASS_PACKAGES = ["simple_scheduler.jobs"]

# Exclude specific jobs that require additional dependencies
JOB_CLASS_EXCLUDE_PACKAGES = ["apns_job"]
TIMEZONE = "Asia/Taipei"
