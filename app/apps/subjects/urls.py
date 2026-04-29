from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RelationshipViewSet, SubjectViewSet

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("relationships", RelationshipViewSet, basename="relationship")

urlpatterns = [
    path("", include(router.urls)),
]
