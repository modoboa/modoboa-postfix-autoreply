"""Autoreply viewsets."""

from rest_framework import mixins, permissions, viewsets

from modoboa.admin import models as admin_models

from . import models
from . import serializers


class ARMessageViewSet(
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet):
    """A viewset for ARmessage."""

    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.ARMessageSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        qset = models.ARmessage.objects.all()
        role = self.request.user.role
        if role == "SimpleUsers":
            qset = qset.filter(mbox=self.request.user.mailbox)
        elif role in ["DomainAdmins", "Resellers"]:
            mailboxes = admin_models.Mailbox.objects.get_for_admin(
                self.request.user)
            qset = qset.filter(mbox__in=mailboxes)
        return qset
