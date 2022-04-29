modoboa-postfix-autoreply
=========================

|gha| |codecov|

Away message editor for Modoboa (postfix compatible).

Installation
------------

Install this extension system-wide or inside a virtual environment by
running the following command::

  $ pip install modoboa-postfix-autoreply

Edit the settings.py file of your modoboa instance and add
``modoboa_postfix_autoreply`` inside the ``MODOBOA_APPS`` variable like this::

    MODOBOA_APPS = (
      'modoboa',
      'modoboa.core',
      'modoboa.lib',
      'modoboa.admin',
      'modoboa.relaydomains',
      'modoboa.limits',
      'modoboa.parameters',
      # Extensions here
      'modoboa_postfix_autoreply',
    )

Run the following commands to setup the database tables::

  $ cd <modoboa_instance_dir>
  $ python manage.py migrate modoboa_postfix_autoreply
  $ python manage.py collectstatic
  $ python manage.py load_initial_data

Finally, restart the python process running modoboa (uwsgi, gunicorn,
apache, whatever).

Setup
-----

`Online documentation <https://modoboa-postfix-autoreply.readthedocs.io/en/latest/>`_.

.. |gha| image:: https://github.com/modoboa/modoboa-postfix-autoreply/actions/workflows/plugin.yml/badge.svg
   :target: https://github.com/modoboa/modoboa-postfix-autoreply/actions/workflows/plugin.yml

.. |codecov| image:: http://codecov.io/github/modoboa/modoboa-postfix-autoreply/coverage.svg?branch=master
   :target: http://codecov.io/github/modoboa/modoboa-postfix-autoreply?branch=master
