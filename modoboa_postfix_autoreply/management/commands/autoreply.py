#!/usr/bin/env python
# coding: utf-8
import sys
import datetime
import logging
from logging.handlers import SysLogHandler
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modoboa.core.management.commands import CloseConnectionMixin
from modoboa.lib import parameters
from modoboa.lib.email_utils import split_mailbox, sendmail_simple

from modoboa_admin.models import Mailbox

from ...models import ARmessage, ARhistoric
from ...modo_extension import PostfixAutoreply

logger = logging.getLogger()
logger.addHandler(SysLogHandler(address="/dev/log"))
logger.setLevel(logging.ERROR)


def send_autoreply(sender, mailbox, armessage):
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
                "no autoreply message sent because delta (%s) < timetout (%s)"
                % (delta, timeout)
            )
            sys.exit(0)

    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    logger.debug(
        "autoreply message sent to %s" % mailbox.user.encoded_address)
    sendmail_simple(mailbox.user.encoded_address, sender, armessage.subject,
                    armessage.content.encode("utf-8"))

    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand, CloseConnectionMixin):
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
            logger.debug("autoreply %s" % " ".join(args))

            raise CommandError(
                "usage: ./manage.py autoreply <sender> <recipient ...>")

        logger.debug(
            "autoreply sender=%s recipient=%s" % (args[0], ",".join(args[1:]))
        )

        PostfixAutoreply().load()
        sender = args[0]
        for fulladdress in args[1:]:
            address, domain = split_mailbox(fulladdress)
            try:
                mbox = Mailbox.objects.get(
                    address=address, domain__name=domain)
            except Mailbox.DoesNotExist:
                msg = "Unknown recipient %s" % (fulladdress)
                logger.debug("autoreply %s" % msg)
                continue
            try:
                armessage = ARmessage.objects.get(mbox=mbox.id, enabled=True)
                logger.debug("autoreply message found")
            except ARmessage.DoesNotExist:
                logger.debug("autoreply message not found")
                continue

            send_autoreply(sender, mbox, armessage)
