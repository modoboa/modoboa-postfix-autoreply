# -*- coding: utf-8 -*-

"""Django signal handlers for modoboa_postfix_autoreply."""

from __future__ import unicode_literals

from django.conf.urls import url
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models, signals as admin_signals
from modoboa.core import signals as core_signals
from . import forms, models, postfix_maps


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_transport_entry(sender, instance, **kwargs):
    """Create or update a transport entry for this domain."""
    if kwargs.get("created"):
        models.Transport.objects.get_or_create(
            domain="autoreply.{}".format(instance), method="autoreply:"
        )
        return
    oldname = getattr(instance, "oldname", "None")
    if oldname is None or oldname == instance.name:
        return
    models.Transport.objects.filter(
        domain="autoreply.{}".format(oldname)).update(
            domain="autoreply.{}".format(instance.name))
    qset = (
        admin_models.AliasRecipient.objects
        .select_related("alias", "r_mailbox")
        .filter(
            alias__domain=instance, alias__internal=True,
            address__contains="@autoreply")
    )
    for alr in qset:
        alr.address = alr.address.replace(oldname, instance.name)
        alr.save()


@receiver(signals.post_delete, sender=admin_models.Domain)
def delete_transport_entry(sender, instance, **kwargs):
    """Delete a transport entry."""
    models.Transport.objects.filter(
        domain="autoreply.{}".format(instance)).delete()


@receiver(signals.post_save, sender=admin_models.Mailbox)
def rename_autoreply_alias(sender, instance, **kwargs):
    """Rename AR alias if needed."""
    old_address = getattr(instance, "old_full_address", None)
    if old_address is None or old_address == instance.full_address:
        return
    admin_models.AliasRecipient.objects.filter(
        address__contains="{}@autoreply".format(old_address)).update(
            address="{}@autoreply.{}".format(
                instance.full_address, instance.domain))


@receiver(signals.post_delete, sender=admin_models.Mailbox)
def delete_autoreply_alias(sender, instance, **kwargs):
    """Delete alias."""
    admin_models.AliasRecipient.objects.filter(
        address="{}@autoreply.{}".format(
            instance.full_address, instance.domain)).delete()


@receiver(signals.post_save, sender=models.ARmessage)
def manage_autoreply_alias(sender, instance, **kwargs):
    """Create or delete the alias."""
    ar_alias_address = "{}@autoreply.{}".format(
        instance.mbox.full_address, instance.mbox.domain)
    admin_models.Alias.objects.get(
        address=instance.mbox.full_address, domain=instance.mbox.domain,
        internal=True)
    alias, created = admin_models.Alias.objects.get_or_create(
        address=instance.mbox.full_address, domain=instance.mbox.domain,
        internal=True)
    if instance.enabled:
        admin_models.AliasRecipient.objects.get_or_create(
            alias=alias, address=ar_alias_address)
    else:
        admin_models.AliasRecipient.objects.filter(
            address=ar_alias_address).delete()


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register postfix maps."""
    return [
        postfix_maps.TransportMap,
    ]


@receiver(core_signals.extra_uprefs_routes)
def extra_routes(sender, **kwargs):
    """Add extra routes."""
    from . import views
    return [
        url(r'^user/autoreply/$', views.autoreply, name="autoreply")
    ]


@receiver(core_signals.extra_static_content)
def extra_js(sender, caller, st_type, user, **kwargs):
    """Add static content."""
    if caller != "user_index" or st_type != "js":
        return ""
    return """function autoreply_cb() {
    $('.datefield').datetimepicker({
        format: 'YYYY-MM-DD HH:mm:ss',
        language: '%(lang)s'
    });
}
""" % {"lang": user.language}


@receiver(core_signals.extra_user_menu_entries)
def menu(sender, location, user, **kwargs):
    """Inject new menu entries."""
    if location != "uprefs_menu" or not hasattr(user, "mailbox"):
        return []
    return [
        {"name": "autoreply",
         "class": "ajaxnav",
         "url": "autoreply/",
         "label": _("Auto-reply message")}
    ]


@receiver(admin_signals.extra_account_forms)
def extra_account_form(sender, user, account, **kwargs):
    """Add autoreply form to the account edition form."""
    result = []
    if user.role in ("SuperAdmins", "DomainAdmins"):
        if hasattr(account, "mailbox"):
            extraform = {
                "id": "auto_reply_message",
                "title": _("Auto reply"),
                "cls": forms.ARmessageForm,
                "new_args": [account.mailbox]
            }
            result.append(extraform)
    return result


@receiver(admin_signals.get_account_form_instances)
def fill_account_tab(sender, user, account, **kwargs):
    """Return form instance."""
    condition = (
        user.role not in ("SuperAdmins", "DomainAdmins") or
        not hasattr(account, "mailbox"))
    if condition:
        return {}
    return {"auto_reply_message": account.mailbox.armessage_set.first()}
