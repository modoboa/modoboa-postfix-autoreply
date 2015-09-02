"""Event callbacks."""

from django.utils.translation import ugettext_lazy, ugettext as _

from modoboa.lib import events, parameters

from modoboa_admin.models import Mailbox

from .forms import ARmessageForm
from .models import Transport, Alias


@events.observe("ExtraUprefsJS")
def extra_js(user):
    return ["""function autoreply_cb() {
    $('.datefield').datetimepicker({
        format: 'YYYY-MM-DD HH:mm:ss',
        language: '%(lang)s'
    });
}
""" % {'lang': parameters.get_user(user, "LANG", app="core")}
    ]


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "uprefs_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "autoreply",
         "class": "ajaxnav",
         "url": "autoreply/",
         "label": ugettext_lazy("Auto-reply message")}
    ]


@events.observe("DomainCreated")
def onDomainCreated(user, domain):
    """Create a Transport record for the created domain."""
    Transport.objects.get_or_create(
        domain="autoreply.{}".format(domain.name), method="autoreply:"
    )


@events.observe("DomainModified")
def onDomainModified(domain):
    if domain.oldname == domain.name:
        return
    Transport.objects.filter(domain="autoreply.%s" % domain.oldname) \
        .update(domain="autoreply.%s" % domain.name)
    for al in Alias.objects.filter(
            full_address__contains="@%s" % domain.oldname):
        new_address = al.full_address.replace(
            "@%s" % domain.oldname,
            "@%s" % domain.name)
        al.full_address = new_address
        al.autoreply_address = "%s@autoreply.%s" % (new_address, domain.name)
        al.save()


@events.observe("DomainDeleted")
def onDomainDeleted(domain):
    Transport.objects.filter(domain="autoreply.%s" % domain.name).delete()


@events.observe("MailboxCreated")
def onMailboxCreated(user, mailbox):
    alias = Alias()
    alias.full_address = mailbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()


@events.observe("MailboxDeleted")
def onMailboxDeleted(mailboxes):
    if isinstance(mailboxes, Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        try:
            alias = Alias.objects.get(full_address=mailbox.full_address)
        except Alias.DoesNotExist:
            pass
        else:
            alias.delete()


@events.observe("MailboxModified")
def onMailboxModified(mailbox):
    if not hasattr(mailbox, 'old_full_address'):
        return
    if mailbox.full_address == mailbox.old_full_address:
        return
    alias = Alias.objects.get(full_address=mailbox.old_full_address)
    alias.full_address = mailbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()


@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
    """Add autoreply form to the account edition form."""
    result = []
    if user.group in ("SuperAdmins", "DomainAdmins"):
        extraform = {
            "id": "auto_reply_message",
            "title": _("Auto reply"),
            "cls": ARmessageForm,
        }
        if account.mailbox_set.first():
            extraform["new_args"] = [account.mailbox_set.first()]
        result.append(extraform)
    return result


@events.observe("FillAccountInstances")
def fill_account_tab(user, account, instances):
    if user.group in ("SuperAdmins", "DomainAdmins"):
        mailbox = account.mailbox_set.first()
        instances["auto_reply_message"] = mailbox.armessage_set.first()
