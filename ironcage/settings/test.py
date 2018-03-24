from .base import *  # flake8: noqa

# Disable sending Slack messaages in tests
SLACK_BACKEND = 'django_slack.backends.TestBackend'

# Admins for mailing errors to
ADMINS = ['admin@example.com']
