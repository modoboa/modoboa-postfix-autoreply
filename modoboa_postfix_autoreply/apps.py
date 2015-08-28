"""AppConfig for modoboa_postfix_autoreply."""

from django.apps import AppConfig


class PostfixAutoreplyConfig(AppConfig):

    """App configuration."""

    name = "modoboa_postfix_autoreply"
    verbose_name = "Auto-reply functionality using Postfix"

    def ready(self):
        from . import handlers
