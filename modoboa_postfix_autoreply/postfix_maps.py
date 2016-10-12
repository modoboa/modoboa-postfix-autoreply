"""Map file definitions for postfix."""


class TransportMap(object):

    """A transport map for autoreply aliases."""

    filename = "sql-autoreplies-transport.cf"
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = (
        "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    )
    sqlite = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
