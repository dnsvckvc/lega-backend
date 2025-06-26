from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, LawyerViewSet, MandateViewSet, TimeEntryViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'lawyers', LawyerViewSet)
router.register(r'mandates', MandateViewSet)
router.register(r'time-entries', TimeEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]