"""Django signal handlers for modoboa_postfix_autoreply."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.core import signals as core_signals

from . import models
from . import postfix_maps


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_transport_entry(sender, instance, **kwargs):
    """Create or update a transport entry for this domain."""
    if kwargs.get("created"):
        models.Transport.objects.get_or_create(
            domain=u"autoreply.{}".format(instance), method="autoreply:"
        )
        return
    oldname = getattr(instance, "oldname", "None")
    if oldname is None or oldname == instance.name:
        return
    models.Transport.objects.filter(
        domain=u"autoreply.{}".format(oldname)).update(
            domain=u"autoreply.{}".format(instance.name))
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
        address__contains=u"{}@autoreply".format(old_address)).update(
            address=u"{}@autoreply.{}".format(
                instance.full_address, instance.domain))


@receiver(signals.post_delete, sender=admin_models.Mailbox)
def delete_autoreply_alias(sender, instance, **kwargs):
    """Delete alias."""
    try:
        alr = admin_models.AliasRecipient.objects.get(
            address=u"{}@autoreply.{}".format(
                instance.full_address, instance.domain))
    except admin_models.AliasRecipient.DoesNotExist:
        return
    alias = alr.alias
    alr.delete()
    if not alias.recipients_count:
        alias.delete()


@receiver(signals.post_save, sender=models.ARmessage)
def manage_autoreply_alias(sender, instance, **kwargs):
    """Create or delete the alias."""
    ar_alias_address = u"{}@autoreply.{}".format(
        instance.mbox.full_address, instance.mbox.domain)
    alias, created = admin_models.Alias.objects.get_or_create(
        address=instance.mbox.full_address, domain=instance.mbox.domain,
        internal=True)
    if instance.enabled:
        admin_models.AliasRecipient.objects.get_or_create(
            alias=alias, address=ar_alias_address)
    else:
        admin_models.AliasRecipient.objects.filter(
            address=ar_alias_address).delete()
        if not alias.recipients_count:
            alias.delete()


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register postfix maps."""
    return [
        postfix_maps.TransportMap,
    ]
