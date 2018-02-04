# -*- coding: utf-8 -*-

"""Map file definitions for postfix."""

from __future__ import unicode_literals


class TransportMap(object):

    """A transport map for autoreply aliases."""

    filename = "sql-autoreplies-transport.cf"
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = (
        "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    )
    sqlite = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
