#####
Setup
#####

The user that executes the autoreply script needs to access
:file:`settings.py`. You must apply proper permissions on this file. For
example, if :file:`settings.py` belongs to ``www-data:www-data``, you can add
the ``vmail`` user to the ``www-data`` group and set the read permission
for the group.

To make Postfix use this feature, you need to update your
configuration files as follows:

In ``/etc/postfix//sql-aliases.cf``, append at the end of query line ::

  query = .... UNION (SELECT concat(full_address, ',', autoreply_address) FROM postfix_autoreply_alias WHERE full_address='%s')


``/etc/postfix/main.cf``::

  transport_maps = <driver>:/etc/postfix/sql-autoreplies-transport.cf


``/etc/postfix/master.cf``::

  autoreply unix        -       n       n       -       -       pipe
            flags= user=vmail:<group> argv=python <modoboa_site>/manage.py autoreply $sender $mailbox

Replace ``<driver>`` by the name of the database you
use. ``<modoboa_site>`` is the path of your Modoboa instance.

Then, create the requested map files::

  $ modoboa-admin.py postfix_maps mapfiles --extensions postfix-autoreply

``mapfiles`` is the directory where the files will be stored. Answer the
few questions and you're done.

.. note::

   Auto-reply messages are just sent once per sender for a
   pre-defined time period. By default, this period is equal to 1 day
   (86400s), you can adjust this value by modifying the **Automatic
   reply timeout** parameter available in the online panel.
