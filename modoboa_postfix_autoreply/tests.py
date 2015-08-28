"""modoboa-postfix-autoreply unit tests."""

from django.core.urlresolvers import reverse
from django.test import TestCase

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.lib.test_utils import MapFilesTestCaseMixin

from modoboa_admin import factories
from modoboa_admin.models import (
    Domain
)

from .models import Transport, Alias, ARmessage


class EventsTestCase(ModoTestCase):

    def setUp(self):
        super(EventsTestCase, self).setUp()
        factories.populate_database()

    def test_domain_created_event(self):
        values = {
            "name": "domain.tld", "quota": 100, "create_dom_admin": "no",
            "stepid": 'step3', "type": "domain"
        }
        self.ajax_post(
            reverse("modoboa_admin:domain_add"), values
        )
        self.assertTrue(
            Transport.objects.filter(domain='autoreply.domain.tld').exists()
        )

    def test_domain_deleted_event(self):
        dom = Domain.objects.get(name="test.com")
        trans = Transport.objects.get(domain='autoreply.test.com')
        self.ajax_post(
            reverse("modoboa_admin:domain_delete", args=[dom.id]),
            {}
        )
        with self.assertRaises(Transport.DoesNotExist):
            Transport.objects.get(domain='autoreply.test.com')

    def test_domain_modified_event(self):
        values = {
            "name": "test.fr", "quota": 100, "enabled": True,
            "type": "domain"
        }
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(
            reverse("modoboa_admin:domain_change", args=[dom.id]),
            values
        )
        trans = Transport.objects.get(domain='autoreply.test.fr')
        self.assertEqual(
            Alias.objects.filter(full_address__contains='@test.fr').count(), 2
        )
        for al in Alias.objects.filter(full_address__contains='@test.fr'):
            self.assertIn('autoreply.test.fr', al.autoreply_address)

    def test_mailbox_created_event(self):
        values = {
            'username': "tester@test.com",
            'first_name': 'Tester',
            'last_name': 'Toto',
            'password1': 'aiL9oodi',
            'password2': 'aiL9oodi',
            'role': 'SimpleUsers',
            'quota_act': True,
            'is_active': True,
            'email': 'tester@test.com',
            'stepid': 'step2',
            'autoreply': 'no'
        }
        self.ajax_post(
            reverse("modoboa_admin:account_add"), values
        )
        al = Alias.objects.get(full_address='tester@test.com')
        self.assertEqual(
            al.autoreply_address, 'tester@test.com@autoreply.test.com')
        arm = ARmessage.objects.get(mbox__address='tester')

    def test_mailbox_deleted_event(self):
        account = User.objects.get(username="user@test.com")
        self.ajax_post(
            reverse("modoboa_admin:account_delete", args=[account.id]),
            {}
        )
        with self.assertRaises(Alias.DoesNotExist):
            Alias.objects.get(full_address='user@test.com')
        with self.assertRaises(ARmessage.DoesNotExist):
            ARmessage.objects.get(
                mbox__address='user', mbox__domain__name='test.com')

    def test_modify_mailbox_event(self):
        values = {
            'username': "leon@test.com",
            'first_name': 'Tester', 'last_name': 'Toto',
            'role': 'SimpleUsers', 'quota_act': True,
            'is_active': True, 'email': 'leon@test.com',
            'autoreply': 'no', 'subject': 'test',
            'content': 'test'
        }
        account = User.objects.get(username="user@test.com")
        self.ajax_post(
            reverse("modoboa_admin:account_change", args=[account.id]),
            values
        )
        with self.assertRaises(Alias.DoesNotExist):
            Alias.objects.get(full_address='user@test.com')
        al = Alias.objects.get(full_address='leon@test.com')


class FormTestCase(ModoTestCase):

    def setUp(self):
        super(FormTestCase, self).setUp()
        factories.populate_database()
        self.clt.logout()
        self.clt.login(username="user@test.com", password="toto")

    def test_set_autoreply(self):
        values = {
            'subject': 'test', 'content': "I'm off", "enabled": True
        }
        self.ajax_post(reverse('autoreply'), values)
        account = User.objects.get(username="user@test.com")
        arm = ARmessage.objects.get(mbox=account.mailbox_set.first())
        self.assertEqual(arm.subject, 'test')
        self.assertTrue(arm.enabled)
        self.assertFalse(arm.untildate)
        self.assertTrue(arm.fromdate)

    def test_set_autoreply_in_past(self):
        """Create an autoreply with from date expired."""
        values = {
            'subject': 'test', 'content': "I'm off", "enabled": True,
            "fromdate": "2014-01-01 00:00:00"
        }
        self.ajax_post(reverse('autoreply'), values)


class MapFilesTestCase(MapFilesTestCaseMixin, TestCase):

    """Test case for modoboa_postfix_autoreply."""

    extension = "modoboa_postfix_autoreply"

    MAP_FILES = [
        "sql-autoreplies-transport.cf",
        "sql-autoreplies.cf"
    ]
