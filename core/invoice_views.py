from rest_framework import status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse
from django.db.models import Sum, Q, Count
from datetime import date, datetime
from decimal import Decimal

from .models import Invoice, InvoiceLineItem, Client, Mandate, TimeEntry
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceStatusUpdateSerializer,
    InvoiceGenerationSerializer, InvoiceSummarySerializer, InvoiceLineItemSerializer
)
from .services import InvoiceGeneratorService, InvoiceStatusService
from .pdf_generator import InvoicePDFGenerator, InvoiceSummaryPDFGenerator
from authentication.permissions import IsLawyer, IsAdminLawyer


class InvoiceViewSet(ModelViewSet):
    """ViewSet for managing invoices"""
    
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsLawyer]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'client', 'mandate']
    search_fields = ['invoice_number', 'client__name', 'mandate__name']
    ordering_fields = ['created_at', 'issue_date', 'due_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date ranges if provided
        issue_date_from = self.request.query_params.get('issue_date_from')
        issue_date_to = self.request.query_params.get('issue_date_to')
        due_date_from = self.request.query_params.get('due_date_from')
        due_date_to = self.request.query_params.get('due_date_to')
        
        if issue_date_from:
            queryset = queryset.filter(issue_date__gte=issue_date_from)
        if issue_date_to:
            queryset = queryset.filter(issue_date__lte=issue_date_to)
        if due_date_from:
            queryset = queryset.filter(due_date__gte=due_date_from)
        if due_date_to:
            queryset = queryset.filter(due_date__lte=due_date_to)
        
        # Filter overdue invoices
        if self.request.query_params.get('overdue') == 'true':
            queryset = queryset.filter(status='sent', due_date__lt=date.today())
        
        return queryset.select_related('client', 'mandate').prefetch_related('line_items')
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update invoice status"""
        invoice = self.get_object()
        serializer = InvoiceStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            paid_date = serializer.validated_data.get('paid_date')
            
            if new_status == 'sent':
                InvoiceStatusService.mark_as_sent(invoice)
            elif new_status == 'paid':
                InvoiceStatusService.mark_as_paid(invoice, paid_date)
            elif new_status == 'overdue':
                InvoiceStatusService.mark_as_overdue(invoice)
            elif new_status == 'cancelled':
                InvoiceStatusService.cancel_invoice(invoice)
            else:
                invoice.status = new_status
                invoice.save()
            
            return Response(InvoiceSerializer(invoice).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download invoice as PDF"""
        invoice = self.get_object()
        pdf_generator = InvoicePDFGenerator()
        
        pdf_buffer = pdf_generator.generate_invoice_pdf(invoice)
        filename = pdf_generator.generate_invoice_filename(invoice)
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['post'])
    def generate_from_time_entries(self, request):
        """Generate invoice from time entries"""
        serializer = InvoiceGenerationSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                client = Client.objects.get(id=data['client_id'])
                mandate = None
                if data.get('mandate_id'):
                    mandate = Mandate.objects.get(id=data['mandate_id'])
                
                generator = InvoiceGeneratorService(tax_rate=data['tax_rate'])
                invoice = generator.generate_invoice_for_client_period(
                    client=client,
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    mandate=mandate
                )
                
                if not invoice:
                    return Response(
                        {'error': 'No billable time entries found for the specified period.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Update notes and due date
                if data.get('notes'):
                    invoice.notes = data['notes']
                
                from datetime import timedelta
                invoice.due_date = invoice.issue_date + timedelta(days=data['due_days'])
                invoice.save()
                
                return Response(
                    InvoiceSerializer(invoice).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Client.DoesNotExist:
                return Response(
                    {'error': 'Client not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Mandate.DoesNotExist:
                return Response(
                    {'error': 'Mandate not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get invoice summary statistics"""
        queryset = self.get_queryset()
        
        summary_data = {
            'total_invoices': queryset.count(),
            'total_amount': queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
            'paid_amount': queryset.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
            'overdue_count': queryset.filter(status='sent', due_date__lt=date.today()).count(),
            'overdue_amount': queryset.filter(status='sent', due_date__lt=date.today()).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        }
        
        summary_data['outstanding_amount'] = summary_data['total_amount'] - summary_data['paid_amount']
        
        serializer = InvoiceSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary_pdf(self, request):
        """Download invoice summary as PDF"""
        queryset = self.get_queryset()
        
        pdf_generator = InvoiceSummaryPDFGenerator()
        title = f"Invoice Summary Report - {date.today().strftime('%B %Y')}"
        
        pdf_buffer = pdf_generator.generate_invoice_summary_pdf(queryset, title)
        filename = f"Invoice_Summary_{date.today().strftime('%Y%m%d')}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminLawyer])
    def update_overdue_statuses(self, request):
        """Update all overdue invoice statuses (admin only)"""
        count = InvoiceStatusService.update_overdue_statuses()
        return Response({'updated_count': count})


class InvoiceLineItemViewSet(ModelViewSet):
    """ViewSet for managing invoice line items"""
    
    queryset = InvoiceLineItem.objects.all()
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsLawyer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']
    
    def get_queryset(self):
        return super().get_queryset().select_related('invoice', 'time_entry')


class ClientInvoiceHistoryView(generics.ListAPIView):
    """View for getting a client's invoice history"""
    
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsLawyer]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'issue_date', 'due_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return Invoice.objects.filter(client_id=client_id).select_related('client', 'mandate').prefetch_related('line_items')


class MandateInvoiceListView(generics.ListAPIView):
    """View for getting invoices for a specific mandate"""
    
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsLawyer]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'issue_date', 'due_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        mandate_id = self.kwargs['mandate_id']
        return Invoice.objects.filter(mandate_id=mandate_id).select_related('client', 'mandate').prefetch_related('line_items')


class UnbilledTimeEntriesView(generics.ListAPIView):
    """View for getting unbilled time entries for invoice generation"""
    
    serializer_class = 'core.serializers.TimeEntrySerializer'  # Import would be circular
    permission_classes = [permissions.IsAuthenticated, IsLawyer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['mandate', 'lawyer']
    ordering = ['-date']
    
    def get_serializer_class(self):
        from .serializers import TimeEntrySerializer
        return TimeEntrySerializer
    
    def get_queryset(self):
        queryset = TimeEntry.objects.filter(
            is_billable=True,
            is_invoiced=False
        ).select_related('mandate', 'lawyer', 'mandate__client')
        
        # Filter by client if provided
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(mandate__client_id=client_id)
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset


class MonthlyInvoiceGenerationView(generics.CreateAPIView):
    """View for generating monthly invoices for all clients"""
    
    permission_classes = [permissions.IsAuthenticated, IsAdminLawyer]
    serializer_class = InvoiceGenerationSerializer
    
    def post(self, request):
        year = request.data.get('year', date.today().year)
        month = request.data.get('month', date.today().month)
        
        try:
            year = int(year)
            month = int(month)
            
            if not (1 <= month <= 12):
                return Response(
                    {'error': 'Month must be between 1 and 12.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            generator = InvoiceGeneratorService()
            generated_invoices = []
            
            # Get all clients with unbilled time entries for the month
            from calendar import monthrange
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
            
            clients_with_entries = Client.objects.filter(
                mandates__time_entries__date__gte=start_date,
                mandates__time_entries__date__lte=end_date,
                mandates__time_entries__is_billable=True,
                mandates__time_entries__is_invoiced=False
            ).distinct()
            
            for client in clients_with_entries:
                invoices = generator.generate_monthly_invoices_for_client(client, year, month)
                generated_invoices.extend(invoices)
            
            response_data = {
                'generated_count': len(generated_invoices),
                'invoices': [InvoiceSerializer(invoice).data for invoice in generated_invoices]
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError:
            return Response(
                {'error': 'Invalid year or month format.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )