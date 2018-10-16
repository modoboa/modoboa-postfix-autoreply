"""Autoreply viewsets."""

from django_filters import rest_framework as filters
from rest_framework import mixins, permissions, viewsets

from modoboa.admin import models as admin_models

from . import models
from . import serializers


class ARMessageFilterSet(filters.FilterSet):
    """Filter set for ARmessage."""

    class Meta:
        fields = ("mbox", "mbox__user")
        model = models.ARmessage


class ARMessageViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet):
    """A viewset for ARmessage."""

    filter_backends = (filters.DjangoFilterBackend, )
    filter_class = ARMessageFilterSet
    permission_classes = (permissions.IsAuthenticated, )
    queryset = models.ARmessage.objects.all()
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
