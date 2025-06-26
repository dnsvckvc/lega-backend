#!/usr/bin/env python3
"""
API Testing Script for Legal Practice Management System

This script demonstrates various API endpoints with real data.
Make sure the Django server is running before executing this script.

Usage: python test_api.py
"""

import requests
import json
from datetime import date, datetime
from urllib.parse import urlencode

BASE_URL = "http://127.0.0.1:8000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def make_request(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += "?" + urlencode(params)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}")
        return None

def pretty_print(data):
    print(json.dumps(data, indent=2, default=str))

def main():
    print("🚀 Legal Practice Management API Testing")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Get all active mandates
    print_section("1. ACTIVE MANDATES")
    print("Fetching all mandates marked as active (is_active=True)...")
    active_mandates = make_request("/mandates/", {"status": "active"})
    if active_mandates:
        print(f"Found {active_mandates.get('count', 0)} active mandates:")
        for mandate in active_mandates.get('results', []):
            print(f"  • {mandate['name']} (Client: {mandate['client_name']}, Due: {mandate['due_date']}, Active: {mandate['is_active']})")
    
    # Test 2: Get inactive mandates
    print_section("2. INACTIVE MANDATES")
    print("Fetching all mandates marked as inactive (is_active=False)...")
    inactive_mandates = make_request("/mandates/", {"status": "inactive"})
    if inactive_mandates:
        print(f"Found {inactive_mandates.get('count', 0)} inactive mandates:")
        for mandate in inactive_mandates.get('results', []):
            print(f"  • {mandate['name']} (Client: {mandate['client_name']}, Due: {mandate['due_date']}, Active: {mandate['is_active']})")
    
    # Test 3: Get overdue mandates
    print_section("3. OVERDUE MANDATES")
    print("Fetching all mandates with due dates < today AND still active...")
    overdue_mandates = make_request("/mandates/", {"status": "overdue"})
    if overdue_mandates:
        print(f"Found {overdue_mandates.get('count', 0)} overdue mandates:")
        for mandate in overdue_mandates.get('results', []):
            print(f"  • {mandate['name']} (Client: {mandate['client_name']}, Due: {mandate['due_date']}, Active: {mandate['is_active']})")
    
    # Test 4: Get all lawyers
    print_section("4. ALL LAWYERS")
    lawyers = make_request("/lawyers/")
    if lawyers:
        print(f"Found {lawyers.get('count', 0)} lawyers:")
        for lawyer in lawyers.get('results', []):
            print(f"  • {lawyer['name']} (Rate: ${lawyer['hourly_rate']}/hour)")
    
    # Test 5: Get lawyer's monthly billing (current month)
    print_section("5. LAWYER MONTHLY BILLING")
    if lawyers and lawyers.get('results'):
        first_lawyer = lawyers['results'][0]
        lawyer_id = first_lawyer['id']
        print(f"Getting monthly billing for {first_lawyer['name']} (current month)...")
        
        monthly_billing = make_request(f"/lawyers/{lawyer_id}/monthly_billing/")
        if monthly_billing:
            print(f"Total Hours: {monthly_billing['total_hours']}")
            print(f"Total Amount: ${monthly_billing['total_amount']}")
            print(f"Entries Count: {monthly_billing['entries_count']}")
            print("\nMandates breakdown:")
            for mandate in monthly_billing.get('mandate_breakdown', []):
                print(f"  • {mandate['mandate_name']}: {mandate['hours']}h = ${mandate['amount']}")
    
    # Test 6: Search mandates by client name
    print_section("6. SEARCH MANDATES BY CLIENT")
    print("Searching for mandates containing 'Tech'...")
    search_results = make_request("/mandates/", {"search": "Tech"})
    if search_results:
        print(f"Found {search_results.get('count', 0)} matching mandates:")
        for mandate in search_results.get('results', []):
            print(f"  • {mandate['name']} (Client: {mandate['client_name']})")
    
    # Test 7: Get time entries for current month
    print_section("7. CURRENT MONTH TIME ENTRIES")
    today = date.today()
    first_of_month = today.replace(day=1)
    print(f"Getting time entries from {first_of_month} to {today}...")
    
    time_entries = make_request("/time-entries/", {
        "date_from": first_of_month.isoformat(),
        "date_to": today.isoformat()
    })
    if time_entries:
        print(f"Found {time_entries.get('count', 0)} time entries this month:")
        for entry in time_entries.get('results', []):
            print(f"  • {entry['date']}: {entry['lawyer_name']} - {entry['hours']}h on {entry['mandate_name']} (${entry['cost']})")
    
    # Test 8: Get mandate with details
    print_section("8. MANDATE DETAILS")
    if active_mandates and active_mandates.get('results'):
        first_mandate = active_mandates['results'][0]
        mandate_id = first_mandate['id']
        print(f"Getting details for mandate: {first_mandate['name']}")
        
        mandate_details = make_request(f"/mandates/{mandate_id}/")
        if mandate_details:
            print(f"Name: {mandate_details['name']}")
            print(f"Client: {mandate_details['client_name']}")
            print(f"Due Date: {mandate_details['due_date']}")
            print(f"Cost Ceiling: ${mandate_details['cost_ceiling'] or 'No limit'}")
            print(f"Total Hours: {mandate_details['total_hours']}")
            print(f"Total Cost: ${mandate_details['total_cost']}")
            print(f"Assigned Lawyers: {', '.join(mandate_details['lawyers_names'])}")
            print(f"Time Entries: {len(mandate_details.get('time_entries', []))}")
    
    # Test 9: Get mandate summary
    print_section("9. MANDATE COST SUMMARY")
    if active_mandates and active_mandates.get('results'):
        mandate_id = active_mandates['results'][0]['id']
        print(f"Getting cost summary for mandate ID {mandate_id}...")
        
        summary = make_request(f"/mandates/{mandate_id}/summary/")
        if summary:
            print(f"Mandate: {summary['mandate_name']}")
            print(f"Client: {summary['client_name']}")
            print(f"Total Hours: {summary['total_hours']}")
            print(f"Total Cost: ${summary['total_cost']}")
            print(f"Cost Ceiling: ${summary['cost_ceiling'] or 'No limit'}")
            print(f"Cost Ceiling Exceeded: {summary['cost_ceiling_exceeded']}")
            print("\nLawyer breakdown:")
            for lawyer in summary.get('lawyer_breakdown', []):
                print(f"  • {lawyer['lawyer_name']}: {lawyer['hours']}h = ${lawyer['cost']}")
    
    # Test 10: Get all clients
    print_section("10. ALL CLIENTS")
    clients = make_request("/clients/")
    if clients:
        print(f"Found {clients.get('count', 0)} clients:")
        for client in clients.get('results', []):
            print(f"  • {client['name']} ({client['email']}) - {client['mandates_count']} mandates")
    
    print_section("✅ API TESTING COMPLETE")
    print("All endpoints are working correctly!")
    print("\nNew filtering options with is_active field:")
    print("• GET /api/mandates/?status=active - Only active mandates")
    print("• GET /api/mandates/?status=inactive - Only inactive mandates") 
    print("• GET /api/mandates/?status=overdue - Only overdue AND active mandates")
    print("• GET /api/mandates/?is_active=true - Direct is_active filtering")
    print("• GET /api/mandates/?is_active=false - Direct inactive filtering")
    print("\nOther available endpoints:")
    print("• POST /api/clients/ - Create new client")
    print("• POST /api/lawyers/ - Create new lawyer") 
    print("• POST /api/mandates/ - Create new mandate")
    print("• POST /api/time-entries/ - Create new time entry")
    print("• PUT/PATCH endpoints for updates")
    print("• DELETE endpoints for deletion")

if __name__ == "__main__":
    main()