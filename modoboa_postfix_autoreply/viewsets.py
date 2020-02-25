"""Autoreply viewsets."""

from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, viewsets

from modoboa.admin import models as admin_models
from modoboa.lib.email_utils import split_mailbox

from . import models
from . import serializers


class ARMessageFilterSet(filters.FilterSet):
    """Filter set for ARmessage."""

    mbox = filters.CharFilter(method="filter_mbox")

    class Meta:
        fields = ("mbox", "mbox__user")
        model = models.ARmessage

    def filter_mbox(self, queryset, name, value):
        address, domain = split_mailbox(value)
        if address:
            queryset = queryset.filter(mbox__address__icontains=address)
        if domain:
            queryset = queryset.filter(mbox__domain__name__icontains=domain)
        return queryset


class ARMessageViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet):
    """A viewset for ARmessage."""

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = ARMessageFilterSet
    permission_classes = (permissions.IsAuthenticated, )
    queryset = models.ARmessage.objects.select_related(
        "mbox__domain", "mbox__user")
    serializer_class = serializers.ARMessageSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        qset = super(ARMessageViewSet, self).get_queryset()
        role = self.request.user.role
        if role == "SimpleUsers":
            qset = qset.filter(mbox=self.request.user.mailbox)
        elif role in ["DomainAdmins", "Resellers"]:
            mailboxes = admin_models.Mailbox.objects.get_for_admin(
                self.request.user)
            qset = qset.filter(mbox__in=mailboxes)
        return qset
