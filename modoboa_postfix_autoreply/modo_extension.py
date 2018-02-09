# -*- coding: utf-8 -*-

"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy

from modoboa.admin import models as admin_models
from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.parameters import tools as param_tools
from . import __version__, forms, models


class PostfixAutoreply(ModoExtension):
    """Auto-reply (vacation) functionality using Postfix."""

    name = "modoboa_postfix_autoreply"
    label = "Postfix autoreply"
    version = __version__
    description = ugettext_lazy(
        "Auto-reply (vacation) functionality using Postfix")

    def load(self):
        param_tools.registry.add(
            "global", forms.ParametersForm, ugettext_lazy("Automatic replies"))

    def load_initial_data(self):
        """Create records for existing domains."""
        for dom in admin_models.Domain.objects.all():
            trans, created = models.Transport.objects.get_or_create(
                domain="autoreply.{}".format(dom.name),
                method="autoreply:")


exts_pool.register_extension(PostfixAutoreply)
