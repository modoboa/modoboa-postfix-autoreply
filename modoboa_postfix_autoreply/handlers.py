"""Django signal handlers for modoboa_postfix_autoreply."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa_admin import models as admin_models

from . import models


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
        domain="autoreply.%s" % oldname).update(
            domain="autoreply.%s" % instance.name)
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
def manage_autoreply_alias(sender, instance, **kwargs):
    """Create an alias for routing."""
    if kwargs.get("created"):
        alias, created = admin_models.Alias.objects.get_or_create(
            address=instance.full_address, domain=instance.domain,
            internal=True)
        admin_models.AliasRecipient.objects.create(
            alias=alias,
            address="{}@autoreply.{}".format(
                instance.full_address, instance.domain))
        return
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
    try:
        alr = admin_models.AliasRecipient.objects.get(
            address="{}@autoreply.{}".format(
                instance.full_address, instance.domain))
    except admin_models.AliasRecipient.DoesNotExist:
        return
    alias = alr.alias
    alr.delete()
    if not alias.recipients_count:
        alias.delete()
