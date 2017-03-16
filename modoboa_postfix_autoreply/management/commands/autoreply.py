#!/usr/bin/env python
# coding: utf-8

import datetime
import email
import fileinput
import logging
from logging.handlers import SysLogHandler
import StringIO
import smtplib
import sys

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from modoboa.admin.models import Mailbox
from modoboa.lib.email_utils import split_mailbox
from modoboa.parameters import tools as param_tools

from ...models import ARmessage, ARhistoric
from ...modo_extension import PostfixAutoreply

logger = logging.getLogger()
logger.addHandler(SysLogHandler(address="/dev/log"))
logger.setLevel(logging.ERROR)


def send_autoreply(sender, mailbox, armessage, original_msg):
    """Send an autoreply message."""
    if armessage.fromdate > timezone.now():
        # Too soon, come back later
        return

    condition = (
        armessage.untildate is not None and
        armessage.untildate < timezone.now())
    if condition:
        # ARmessage has expired, disable it
        armessage.enabled = False
        armessage.save(update_fields=["enabled"])
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        timeout = param_tools.get_global_parameter(
            "autoreplies_timeout", app="modoboa_postfix_autoreply")
        delta = datetime.timedelta(seconds=int(timeout))
        now = timezone.make_aware(datetime.datetime.now(),
                                  timezone.get_default_timezone())
        if lastar.last_sent + delta > now:
            logger.debug(
                "no autoreply message sent because delta (%s) < timetout (%s)",
                delta, timeout
            )
            return

    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    headers = {
        "Auto-Submitted": "auto-replied",
        "Precedence": "bulk"
    }
    message_id = original_msg.get("Message-ID")
    if message_id:
        headers.update({"In-Reply-To": message_id, "References": message_id})
    msg = EmailMessage(
        u"Auto: {} Re: {}".format(armessage.subject, original_msg["Subject"]),
        armessage.content.encode("utf-8"),
        mailbox.user.encoded_address,
        [sender],
        headers=headers
    )
    try:
        msg.send()
    except smtplib.SMTPException as exp:
        logger.error("Failed to send autoreply message: %s", exp)
        sys.exit(1)

    logger.debug(
        "autoreply message sent to %s", mailbox.user.encoded_address)

    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand):
    """Command definition."""

    help = "Send autoreply emails"

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--debug", action="store_true", dest="debug", default=False
        )
        parser.add_argument("sender", type=unicode)
        parser.add_argument("recipient", type=unicode, nargs="+")

    def handle(self, *args, **options):
        if options["debug"]:
            logger.setLevel(logging.DEBUG)

        logger.debug(
            "autoreply sender=%s recipient=%s",
            options["sender"], ",".join(options["recipient"])
        )

        sender = options["sender"]

        sender_localpart = split_mailbox(sender.lower())[0]
        if (
            (sender_localpart in ('mailer-daemon', 'listserv', 'majordomo')) or
            (sender_localpart.startswith('owner-')) or
            (sender_localpart.endswith('-request'))
        ):
            logger.debug(
                "Skip auto reply, this mail comes from a mailing list")
            return

        content = StringIO.StringIO()
        for line in fileinput.input([]):
            content.write(line)
        content.seek(0)

        original_msg = email.message_from_file(content)

        # Mailing list filter based on
        # https://tools.ietf.org/html/rfc5230#page-7
        ml_known_headers = [
            "List-Id", "List-Help", "List-Subscribe", "List-Unsubscribe",
            "List-Post", "List-Owner", "List-Archive"
        ]
        from_ml = False
        for header in ml_known_headers:
            if header in original_msg:
                from_ml = True
                break
        condition = (
            original_msg.get("Precedence") == "bulk" or
            original_msg.get("X-Mailer") == "PHPMailer" or
            from_ml
        )
        if condition:
            logger.debug(
                "Skip auto reply, this mail comes from a mailing list")
            return

        PostfixAutoreply().load()
        for fulladdress in options["recipient"]:
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
