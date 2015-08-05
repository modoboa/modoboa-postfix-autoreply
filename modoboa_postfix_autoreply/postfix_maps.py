"""Map file definitions for postfix."""

from modoboa.core.commands.postfix_maps import registry


class TransportMap(object):

    """A transport map for autoreply aliases."""

    filename = "sql-autoreplies-transport.cf"
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = (
        "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    )
    sqlite = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"


registry.add_files([TransportMap])
