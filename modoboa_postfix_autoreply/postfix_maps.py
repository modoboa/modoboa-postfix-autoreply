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


class AutoRepliesMap(object):

    """A map file to list all autoreply aliases."""

    filename = 'sql-autoreplies.cf'
    mysql = (
        "SELECT full_address, autoreply_address "
        "FROM postfix_autoreply_alias WHERE full_address='%s'"
    )
    postgres = (
        "SELECT full_address, autoreply_address "
        "FROM postfix_autoreply_alias WHERE full_address='%s'"
    )
    sqlite = (
        "SELECT full_address, autoreply_address "
        "FROM postfix_autoreply_alias WHERE full_address='%s'"
    )


registry.add_files([TransportMap, AutoRepliesMap])
