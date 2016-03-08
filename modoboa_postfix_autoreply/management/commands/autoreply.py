#!/usr/bin/env python
# coding: utf-8

import datetime
import email
from email.mime.text import MIMEText
import fileinput
import logging
from logging.handlers import SysLogHandler
from optparse import make_option
import StringIO
import smtplib
import sys

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modoboa.lib import parameters
from modoboa.lib.email_utils import split_mailbox, set_email_headers

from modoboa.admin.models import Mailbox

from ...models import ARmessage, ARhistoric
from ...modo_extension import PostfixAutoreply

logger = logging.getLogger()
logger.addHandler(SysLogHandler(address="/dev/log"))
logger.setLevel(logging.ERROR)


def send_autoreply(sender, mailbox, armessage, original_msg):
    """Send an autoreply message."""
    if armessage.fromdate > timezone.now():
        return

    if armessage.untildate is not None \
            and armessage.untildate < timezone.now():
        armessage.enabled = False
        armessage.save()
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        timeout = parameters.get_admin("AUTOREPLIES_TIMEOUT",
                                       app="modoboa_postfix_autoreply")
        delta = datetime.timedelta(seconds=int(timeout))
        now = timezone.make_aware(datetime.datetime.now(),
                                  timezone.get_default_timezone())
        if lastar.last_sent + delta > now:
            logger.debug(
                "no autoreply message sent because delta (%s) < timetout (%s)",
                delta, timeout
            )
            sys.exit(0)

    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    msg = MIMEText(armessage.content.encode("utf-8"), _charset="utf-8")
    set_email_headers(
        msg,
        u"Auto: {} Re: {}".format(armessage.subject, original_msg["Subject"]),
        mailbox.user.encoded_address, sender
    )
    msg["Auto-Submitted"] = "auto-replied"
    msg["Precedence"] = "bulk"
    message_id = original_msg.get("Message-ID")
    if message_id:
        msg["In-Reply-To"] = message_id
        msg["References"] = message_id

    try:
        s = smtplib.SMTP("localhost")
        s.sendmail(mailbox.user.encoded_address, [sender], msg.as_string())
        s.quit()
    except smtplib.SMTPException as exp:
        logger.error("Failed to send autoreply message: %s", exp)
        sys.exit(1)

    logger.debug(
        "autoreply message sent to %s" % mailbox.user.encoded_address)

    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand):
    args = "<sender> <recipient ...>"
    help = "Send autoreply emails"

    option_list = BaseCommand.option_list + (
        make_option(
            "--debug", "-d", action="store_true", dest="debug", default=False
        ),
    )

    def handle(self, *args, **options):
        if options["debug"]:
            logger.setLevel(logging.DEBUG)

        if len(args) < 2:
            logger.debug("autoreply %s", " ".join(args))

            raise CommandError(
                "usage: ./manage.py autoreply <sender> <recipient ...>")

        logger.debug(
            "autoreply sender=%s recipient=%s", args[0], ",".join(args[1:])
        )

        # Mailing list filter based on
        # https://tools.ietf.org/html/rfc5230#page-7
        sender = args[0]

        sender_localpart = split_mailbox(sender.lower())[0]
        if (
            (sender_localpart in ('mailer-daemon', 'listserv', 'majordomo')) or
            (sender_localpart.startswith('owner-')) or
            (sender_localpart.endswith('-request'))
        ):
            logger.debug("Skip auto reply, this mail comes from mailing list")
            sys.exit(0)

        content = StringIO.StringIO()
        for line in fileinput.input([]):
            content.write(line)
        content.seek(0)

        original_msg = email.message_from_file(content)
        ml_known_headers = [
            "List-Id", "List-Help", "List-Subscribe", "List-Unsubscribe",
            "List-Post", "List-Owner", "List-Archive"
        ]
        from_ml = False
        for header in ml_known_headers:
            if header in original_msg:
                from_ml = True
                break
        conditions = (
            original_msg.get("Precedence") == "bulk",
            original_msg.get("X-Mailer") == "PHPMailer",
            from_ml
        )
        if any(conditions):
            logger.debug(
                "Skip auto reply, this mail comes from mailing list")
            sys.exit(0)

        PostfixAutoreply().load()
        for fulladdress in args[1:]:
            address, domain = split_mailbox(fulladdress)
            try:
                mbox = Mailbox.objects.get(
                    address=address, domain__name=domain)
            except Mailbox.DoesNotExist:
                msg = "Unknown recipient %s" % (fulladdress)
                logger.debug("autoreply %s", msg)
                continue
            try:
                armessage = ARmessage.objects.get(mbox=mbox.id, enabled=True)
                logger.debug("autoreply message found")
            except ARmessage.DoesNotExist:
                logger.debug("autoreply message not found")
                continue

            send_autoreply(sender, mbox, armessage, original_msg)
