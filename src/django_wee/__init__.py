"""django-wee — URL shortener Django application."""

import logging

# Set up logging to ``/dev/null`` like a library is supposed to.
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("django_wee").addHandler(logging.NullHandler())
