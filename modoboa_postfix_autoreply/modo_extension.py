# coding: utf-8
"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters

from modoboa_admin import models as admin_models

from .models import Transport


class PostfixAutoreply(ModoExtension):

    """
    Auto-reply (vacation) functionality using Postfix.

    """
    name = "modoboa_postfix_autoreply"
    label = "Postfix autoreply"
    version = "1.1.1"
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
                domain="autoreply.{}".format(dom.name))
            if not created:
                continue
            for mb in dom.mailbox_set.all():
                alias, created = admin_models.Alias.objects.get_or_create(
                    address=mb.full_address, domain=mb.domain,
                    internal=True)
                admin_models.AliasRecipient.objects.create(
                    alias=alias,
                    address="{}@autoreply.{}".format(
                        mb.full_address, mb.domain))

exts_pool.register_extension(PostfixAutoreply)


@events.observe("ExtraUprefsRoutes")
def extra_routes():
    from django.conf.urls import url

    return [
        url(r'^user/autoreply/$',
            'modoboa_postfix_autoreply.views.autoreply',
            name="autoreply")
    ]
