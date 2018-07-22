from .base import *  # flake8: noqa

ALLOWED_HOSTS = ['staging.hq.pyconuk.org']

# A custom setting for creating full URLs in links in emails
DOMAIN = f'http://{ALLOWED_HOSTS[0]}'

# SSL
SECURE_SSL_REDIRECT = False
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Misc. security settings
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
X_FRAME_OPTIONS = 'DENY'

# Slack
SLACK_USERNAME = 'ironcage-log-bot-staging'

# Email address to send error mails from
SERVER_EMAIL = f'PyCon UK 2018 <noreply@{ALLOWED_HOSTS[0]}>'
EMAIL_FROM_ADDR = f'PyCon UK 2018 <noreply@{ALLOWED_HOSTS[0]}>'
EMAIL_REPLY_TO_ADDR = 'PyCon UK 2018 <pyconuk-committee@uk.python.org>'
