#!/usr/bin/env python3
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy_management.settings')
django.setup()

from pharmacy.models import Patient, Medicine, Purchase, Visit, Sale
from django.utils import timezone

def create_sample_data():
    print("Creating sample data...")
    
    # Create Patients
    patients_data = [
        {'name': 'আব্দুল করিম', 'phone': '01711111111', 'address': 'ঢাকা'},
        {'name': 'ফাতেমা খাতুন', 'phone': '01722222222', 'address': 'চট্টগ্রাম'},
        {'name': 'মোহাম্মদ রহিম', 'phone': '01733333333', 'address': 'সিলেট'},
        {'name': 'রাশিদা বেগম', 'phone': '01744444444', 'address': 'রাজশাহী'},
        {'name': 'আহমেদ হাসান', 'phone': '01755555555', 'address': 'খুলনা'},
    ]
    
    patients = []
    for data in patients_data:
        patient, created = Patient.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        patients.append(patient)
        if created:
            print(f"Created patient: {patient.name}")
    
    # Create Medicines
    medicines_data = [
        {'name': 'প্যারাসিটামল ৫০০mg', 'company': 'স্কয়ার', 'unit_price': Decimal('2.50'), 'stock_quantity': 100},
        {'name': 'অ্যামোক্সিসিলিন ২৫০mg', 'company': 'বেক্সিমকো', 'unit_price': Decimal('8.00'), 'stock_quantity': 50},
        {'name': 'ওমিপ্রাজল ২০mg', 'company': 'ইনসেপ্টা', 'unit_price': Decimal('5.50'), 'stock_quantity': 3},  # Low stock
        {'name': 'মেটফরমিন ৫০০mg', 'company': 'এসিআই', 'unit_price': Decimal('3.00'), 'stock_quantity': 80},
        {'name': 'আইবুপ্রোফেন ৪০০mg', 'company': 'রেনাটা', 'unit_price': Decimal('4.00'), 'stock_quantity': 2},  # Low stock
        {'name': 'সিপ্রোফ্লক্সাসিন ৫০০mg', 'company': 'জুলফার', 'unit_price': Decimal('12.00'), 'stock_quantity': 60},
        {'name': 'লসার্টান ৫০mg', 'company': 'স্কয়ার', 'unit_price': Decimal('6.50'), 'stock_quantity': 40},
        {'name': 'ক্লোরফেনিরামিন ৪mg', 'company': 'বেক্সিমকো', 'unit_price': Decimal('1.50'), 'stock_quantity': 1},  # Low stock
    ]
    
    medicines = []
    for data in medicines_data:
        medicine, created = Medicine.objects.get_or_create(
            name=data['name'],
            company=data['company'],
            defaults=data
        )
        medicines.append(medicine)
        if created:
            print(f"Created medicine: {medicine.name}")
    
    # Create Purchases (for the last month)
    print("Creating purchase records...")
    for i in range(5):
        date = timezone.now() - timedelta(days=i*5)
        medicine = medicines[i % len(medicines)]
        
        purchase = Purchase.objects.create(
            medicine=medicine,
            quantity=20 + (i * 10),
            unit_cost=medicine.unit_price * Decimal('0.8'),  # 20% less than selling price
            purchase_date=date,
            supplier=f"সরবরাহকারী {i+1}"
        )
        print(f"Created purchase: {purchase}")
    
    # Create Visits and Sales (for the last week)
    print("Creating visits and sales...")
    for i in range(7):  # Last 7 days
        date = timezone.now() - timedelta(days=i)
        
        # Create 2-3 visits per day
        for j in range(2 + (i % 2)):
            patient = patients[j % len(patients)]
            
            visit = Visit.objects.create(
                patient=patient,
                visit_date=date - timedelta(hours=j*2),
                prescription=f"রোগীর সমস্যা: জ্বর, মাথাব্যথা। ওষুধ: প্যারাসিটামল ১+০+১"
            )
            
            # Create 1-3 sales per visit
            for k in range(1 + (j % 3)):
                medicine = medicines[k % len(medicines)]
                quantity = 5 + (k % 10)
                payment_type = 'cash' if (i + j + k) % 3 != 0 else 'credit'
                
                sale = Sale.objects.create(
                    visit=visit,
                    medicine=medicine,
                    quantity=quantity,
                    unit_price=medicine.unit_price,
                    payment_type=payment_type,
                    sale_date=visit.visit_date
                )
                print(f"Created sale: {sale}")
    
    print("Sample data created successfully!")
    print(f"Total Patients: {Patient.objects.count()}")
    print(f"Total Medicines: {Medicine.objects.count()}")
    print(f"Total Purchases: {Purchase.objects.count()}")
    print(f"Total Visits: {Visit.objects.count()}")
    print(f"Total Sales: {Sale.objects.count()}")

if __name__ == '__main__':
    create_sample_data()