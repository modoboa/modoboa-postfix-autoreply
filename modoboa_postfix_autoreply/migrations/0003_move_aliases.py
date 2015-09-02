# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def move_aliases(apps, schema_editor):
    """Move exising aliases to the main table."""
    OldAlias = apps.get_model("modoboa_postfix_autoreply", "Alias")
    Alias = apps.get_model("modoboa_admin", "Alias")
    AliasRecipient = apps.get_model("modoboa_admin", "AliasRecipient")
    to_create = []
    for old_alias in OldAlias.objects.all():
        alias, created = Alias.objects.get_or_create(
            address=old_alias.full_address, internal=True)
        to_create.append(AliasRecipient(
            address=old_alias.autoreply_address, alias=alias))
    AliasRecipient.objects.bulk_create(to_create)


class Migration(migrations.Migration):

    dependencies = [
        ('modoboa_postfix_autoreply', '0002_auto_20150728_1236'),
        ('modoboa_admin', '0007_auto_20150801_2101'),
    ]

    operations = [
        migrations.RunPython(move_aliases)
    ]
