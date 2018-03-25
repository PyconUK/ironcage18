from .base import *  # flake8: noqa

DEBUG = bool(os.environ.get('DEBUG'))

# Write emails to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Write Slack messages to the console
SLACK_BACKEND = 'django_slack.backends.ConsoleBackend'

# Don't log Slack error reports to the console
LOGGING['loggers']['django']['handlers'].remove('slack')
