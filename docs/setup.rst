#####
Setup
#####

The user that executes the autoreply script needs to access
:file:`settings.py`. You must apply proper permissions on this file. For
example, if :file:`settings.py` belongs to ``www-data:www-data``, you can add
the ``vmail`` user to the ``www-data`` group and set the read permission
for the group.

To make Postfix use this feature, you need to update your
configuration file as follows:

``/etc/postfix/master.cf``::

  autoreply unix        -       n       n       -       -       pipe
            flags= user=vmail:<group> argv=python <modoboa_site>/manage.py autoreply $sender $mailbox

Replace ``<driver>`` by the name of the database you
use. ``<modoboa_site>`` is the path of your Modoboa instance.

.. note::

   Auto-reply messages are just sent once per sender for a
   pre-defined time period. By default, this period is equal to 1 day
   (86400s), you can adjust this value by modifying the **Automatic
   reply timeout** parameter available in the online panel.
