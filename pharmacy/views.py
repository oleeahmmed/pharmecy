from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .models import Patient, Medicine, Purchase, Visit, Sale


class DashboardView(View):
    """ফার্মেসি ড্যাশবোর্ড ভিউ"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        
        # মোট পরিসংখ্যান
        total_patients = Patient.objects.count()
        total_medicines = Medicine.objects.count()
        low_stock_medicines = Medicine.objects.filter(stock_quantity__lte=5)
        low_stock_count = low_stock_medicines.count()
        
        # আজকের পরিসংখ্যান
        today_patients = Patient.objects.filter(created_at__date=today).count()
        today_sales = Sale.objects.filter(sale_date__date=today)
        today_revenue = today_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        today_cash = today_sales.filter(payment_type='cash').aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        today_credit = today_sales.filter(payment_type='credit').aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        
        # এই মাসের পরিসংখ্যান
        month_start = today.replace(day=1)
        month_sales = Sale.objects.filter(sale_date__date__gte=month_start)
        month_revenue = month_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        month_purchases = Purchase.objects.filter(purchase_date__date__gte=month_start)
        month_purchase = month_purchases.aggregate(Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')
        month_profit = month_revenue - month_purchase
        
        # সাম্প্রতিক ভিজিট
        recent_visits = Visit.objects.select_related('patient').order_by('-visit_date')[:5]
        
        # সাপ্তাহিক বিক্রয় ডেটা (গত ৭ দিন)
        weekly_sales = []
        weekly_labels = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            daily_sales = Sale.objects.filter(sale_date__date=date).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
            weekly_sales.append(float(daily_sales))
            
            # বাংলা দিনের নাম
            day_names = ['সোমবার', 'মঙ্গলবার', 'বুধবার', 'বৃহস্পতিবার', 'শুক্রবার', 'শনিবার', 'রবিবার']
            day_name = day_names[date.weekday()]
            weekly_labels.append(day_name)
        
        context = {
            **admin.site.each_context(request),
            'title': 'ফার্মেসি ড্যাশবোর্ড',
            'subtitle': 'সম্পূর্ণ ফার্মেসি ব্যবস্থাপনা ওভারভিউ',
            'total_patients': total_patients,
            'total_medicines': total_medicines,
            'low_stock_count': low_stock_count,
            'low_stock_medicines': low_stock_medicines[:5],
            'today_patients': today_patients,
            'today_revenue': today_revenue,
            'today_cash': today_cash,
            'today_credit': today_credit,
            'month_revenue': month_revenue,
            'month_purchase': month_purchase,
            'month_profit': month_profit,
            'recent_visits': recent_visits,
            'weekly_sales': json.dumps(weekly_sales),
            'weekly_labels': json.dumps(weekly_labels),
        }
        
        return render(request, 'admin/pharmacy/dashboard.html', context)



@staff_member_required
def get_medicine_price(request):
    """AJAX endpoint to get medicine price"""
    from django.http import JsonResponse
    
    medicine_id = request.GET.get('medicine_id')
    if medicine_id:
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            return JsonResponse({'price': float(medicine.unit_price)})
        except Medicine.DoesNotExist:
            pass
    
    return JsonResponse({'price': None})

class PurchaseReportView(View):
    """ক্রয় রিপোর্ট ভিউ"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        purchases = Purchase.objects.select_related('medicine').order_by('-purchase_date')
        
        if from_date and to_date:
            purchases = purchases.filter(
                purchase_date__date__gte=from_date,
                purchase_date__date__lte=to_date
            )
        
        # Calculate totals
        total_quantity = purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_cost = purchases.aggregate(Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')
        
        context = {
            **admin.site.each_context(request),
            'title': 'ক্রয় রিপোর্ট',
            'subtitle': 'নির্দিষ্ট সময়ের ক্রয় রেকর্ড দেখুন',
            'purchases': purchases[:200],  # Limit to 200 records
            'from_date': from_date,
            'to_date': to_date,
            'total_quantity': total_quantity,
            'total_cost': total_cost,
        }
        
        return render(request, 'admin/pharmacy/purchase_report.html', context)

class SaleReportView(View):
    """বিক্রয় রিপোর্ট ভিউ"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        sales = Sale.objects.select_related('medicine', 'visit', 'visit__patient').order_by('-sale_date')
        
        if from_date and to_date:
            sales = sales.filter(
                sale_date__date__gte=from_date,
                sale_date__date__lte=to_date
            )
        
        # Calculate totals
        total_quantity = sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_amount = sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        cash_sales = sales.filter(payment_type='cash').aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        credit_sales = sales.filter(payment_type='credit').aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        
        context = {
            **admin.site.each_context(request),
            'title': 'বিক্রয় রিপোর্ট',
            'subtitle': 'নির্দিষ্ট সময়ের বিক্রয় রেকর্ড দেখুন',
            'sales': sales[:200],  # Limit to 200 records
            'from_date': from_date,
            'to_date': to_date,
            'total_quantity': total_quantity,
            'total_amount': total_amount,
            'cash_sales': cash_sales,
            'credit_sales': credit_sales,
        }
        
        return render(request, 'admin/pharmacy/sale_report.html', context)

class VisitReportView(View):
    """ভিজিট রিপোর্ট ভিউ"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        patient_id = request.GET.get('patient_id')
        
        visits = Visit.objects.select_related('patient').prefetch_related('sale_set__medicine').order_by('-visit_date')
        
        # Filter by date range
        if from_date and to_date:
            visits = visits.filter(
                visit_date__date__gte=from_date,
                visit_date__date__lte=to_date
            )
        
        # Filter by patient if selected
        if patient_id:
            visits = visits.filter(patient_id=patient_id)
        
        # Get all patients for dropdown
        all_patients = Patient.objects.all().order_by('name')
        selected_patient = None
        if patient_id:
            try:
                selected_patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                pass
        
        # Calculate totals
        total_visits = visits.count()
        total_patients = visits.values('patient').distinct().count()
        
        # Calculate total sales amount for these visits
        visit_sales = Sale.objects.filter(visit__in=visits)
        total_sales_amount = visit_sales.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        total_medicine_quantity = visit_sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        context = {
            **admin.site.each_context(request),
            'title': 'ভিজিট রিপোর্ট',
            'subtitle': 'নির্দিষ্ট সময়ের ভিজিট রেকর্ড দেখুন',
            'visits': visits[:200],  # Limit to 200 records
            'from_date': from_date,
            'to_date': to_date,
            'patient_id': patient_id,
            'all_patients': all_patients,
            'selected_patient': selected_patient,
            'total_visits': total_visits,
            'total_patients': total_patients,
            'total_sales_amount': total_sales_amount,
            'total_medicine_quantity': total_medicine_quantity,
        }
        
        return render(request, 'admin/pharmacy/visit_report.html', context)

