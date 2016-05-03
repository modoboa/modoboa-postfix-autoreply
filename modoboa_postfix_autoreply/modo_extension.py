# coding: utf-8
"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters

from modoboa.admin import models as admin_models

from . import __version__
from .models import Transport


class PostfixAutoreply(ModoExtension):

    """
    Auto-reply (vacation) functionality using Postfix.

    """
    name = "modoboa_postfix_autoreply"
    label = "Postfix autoreply"
    version = __version__  # FIXME: handle this automatically
    description = ugettext_lazy(
        "Auto-reply (vacation) functionality using Postfix")

    def load(self):
        from .app_settings import ParametersForm
        parameters.register(
            ParametersForm, ugettext_lazy("Automatic replies"))
        from . import general_callbacks

    def load_initial_data(self):
        """Create records for existing domains."""
        for dom in admin_models.Domain.objects.all():
            trans, created = Transport.objects.get_or_create(
                domain="autoreply.{}".format(dom.name),
                method="autoreply:")

exts_pool.register_extension(PostfixAutoreply)


@events.observe("ExtraUprefsRoutes")
def extra_routes():
    from django.conf.urls import url

    return [
        url(r'^user/autoreply/$',
            'modoboa_postfix_autoreply.views.autoreply',
            name="autoreply")
    ]
