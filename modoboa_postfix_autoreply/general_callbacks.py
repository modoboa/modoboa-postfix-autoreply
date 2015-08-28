"""Event callbacks."""

from django.utils import timezone
from django.utils.translation import ugettext_lazy

from modoboa.lib import events, parameters
from modoboa.lib.form_utils import YesNoField

from .models import ARmessage


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


@events.observe("ExtraFormFields")
def extra_mailform_fields(form_name, mailbox=None):
    """Define extra fields to include in mail forms.

    For now, only the auto-reply state can be modified.

    :param str form_name: form name (must be 'mailform')
    :param Mailbox mailbox: mailbox
    """
    if form_name != "mailform":
        return []
    status = False
    if mailbox is not None and mailbox.armessage_set.count():
        status = mailbox.armessage_set.all()[0].enabled
    return [
        ('autoreply', YesNoField(
            label=ugettext_lazy("Enable auto-reply"),
            initial="yes" if status else "no",
            required=False,
            help_text=ugettext_lazy("Enable or disable Postfix auto-reply")
        ))
    ]


@events.observe("SaveExtraFormFields")
def save_extra_mailform_fields(form_name, mailbox, values):
    """Set the auto-reply status for a mailbox.

    If a corresponding auto-reply message exists, we update its
    status. Otherwise, we create a message using default values.

    :param str form_name: form name (must be 'mailform')
    :param Mailbox mailbox: mailbox
    :param dict values: form values
    """
    if form_name != 'mailform':
        return
    if mailbox.armessage_set.count():
        arm = mailbox.armessage_set.first()
    else:
        arm = ARmessage(mbox=mailbox)
        arm.subject = parameters.get_admin("DEFAULT_SUBJECT")
        arm.content = parameters.get_admin("DEFAULT_CONTENT") \
            % {'name': mailbox.user.fullname}
        arm.fromdate = timezone.now()
    arm.enabled = True if values['autoreply'] == 'yes' else False
    arm.save()
