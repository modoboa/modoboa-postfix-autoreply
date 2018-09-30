"""Autoreply API urls."""

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"armessages", viewsets.ARMessageViewSet, base_name="armessage")
urlpatterns = router.urls
