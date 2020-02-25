"""Autoreply API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"armessages", viewsets.ARMessageViewSet, basename="armessage")
urlpatterns = router.urls
