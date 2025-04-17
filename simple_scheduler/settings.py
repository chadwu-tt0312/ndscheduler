"""Settings to override default settings."""

#
# Override settings
#
DEBUG = True

HTTP_PORT = 8888
HTTP_ADDRESS = "0.0.0.0"


# Specify the package that contains job classes
JOB_CLASS_PACKAGES = ["simple_scheduler.jobs"]

# Exclude specific jobs that require additional dependencies
JOB_CLASS_EXCLUDE_PACKAGES = ["apns_job"]
TIMEZONE = "Asia/Taipei"
