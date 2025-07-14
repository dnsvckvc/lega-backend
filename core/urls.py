from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, LawyerViewSet, MandateViewSet, TimeEntryViewSet
from .invoice_views import (
    InvoiceViewSet, InvoiceLineItemViewSet, ClientInvoiceHistoryView,
    MandateInvoiceListView, UnbilledTimeEntriesView, MonthlyInvoiceGenerationView
)
from .change_log_views import ChangeLogViewSet
from .api_docs import api_schema, api_examples

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'lawyers', LawyerViewSet)
router.register(r'mandates', MandateViewSet)
router.register(r'time-entries', TimeEntryViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'invoice-line-items', InvoiceLineItemViewSet)
router.register(r'change-logs', ChangeLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('clients/<int:client_id>/invoices/', ClientInvoiceHistoryView.as_view(), name='client-invoices'),
    path('mandates/<int:mandate_id>/invoices/', MandateInvoiceListView.as_view(), name='mandate-invoices'),
    path('unbilled-time-entries/', UnbilledTimeEntriesView.as_view(), name='unbilled-time-entries'),
    path('generate-monthly-invoices/', MonthlyInvoiceGenerationView.as_view(), name='generate-monthly-invoices'),
    path('docs/schema/', api_schema, name='api-schema'),
    path('docs/examples/', api_examples, name='api-examples'),
]