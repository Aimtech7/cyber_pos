import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "manager": {"username": "manager", "password": "manager123"},
    "attendant": {"username": "attendant", "password": "attendant123"}
}

TOKENS = {}

def log(message, status="INFO"):
    print(f"[{status}] {message}")

def login(role):
    url = f"{BASE_URL}/auth/login"
    creds = USERS[role]
    try:
        response = requests.post(url, json={
            "username": creds["username"],
            "password": creds["password"]
        })
        if response.status_code == 200:
            TOKENS[role] = response.json()["access_token"]
            log(f"Login successful for {role}", "PASS")
            return True
        else:
            log(f"Login failed for {role}: {response.text}", "FAIL")
            return False
    except Exception as e:
        log(f"Login exception for {role}: {e}", "FAIL")
        return False

def get_headers(role):
    return {"Authorization": f"Bearer {TOKENS.get(role)}"}

def check_auth_rbac():
    log("--- 1. Auth & RBAC ---", "SECTION")
    
    # 1.1 Attendant Login (Already checked in setup)
    if "attendant" in TOKENS:
        log("Attendant can login", "PASS")
    else:
        log("Attendant login failed", "FAIL")

    # 1.2/1.3 Attendant Access to /admin routes (Reports)
    try:
        if "attendant" in TOKENS:
            resp = requests.get(f"{BASE_URL}/reports/dashboard", headers=get_headers("attendant"))
            if resp.status_code == 403:
                log("Attendant blocked from /reports/dashboard", "PASS")
            else:
                log(f"Attendant accessed /reports/dashboard! Status: {resp.status_code}", "FAIL")
    except Exception as e:
        log(f"Attendant access check failed: {e}", "FAIL")

    # 1.4 Manager Access to Reports
    try:
        if "manager" in TOKENS:
            resp = requests.get(f"{BASE_URL}/reports/dashboard", headers=get_headers("manager"))
            if resp.status_code == 200:
                log("Manager accessed /reports/dashboard", "PASS")
            else:
                log(f"Manager blocked from /reports/dashboard! Status: {resp.status_code}", "FAIL")
    except Exception as e:
        log(f"Manager access check failed: {e}", "FAIL")

    # 1.5 Admin Manage Users (Assuming GET /users is admin only)
    try:
        if "admin" in TOKENS:
            resp = requests.get(f"{BASE_URL}/users", headers=get_headers("admin"))
            if resp.status_code == 200:
                log("Admin accessed /users", "PASS")
            else:
                log(f"Admin blocked from /users! Status: {resp.status_code}", "FAIL")
        
        # Manager should fail
        if "manager" in TOKENS:
            resp = requests.get(f"{BASE_URL}/users", headers=get_headers("manager"))
            if resp.status_code == 403:
                log("Manager blocked from /users", "PASS")
            else:
                log(f"Manager accessed /users! Status: {resp.status_code}", "FAIL")
    except Exception as e:
        log(f"User management check failed: {e}", "FAIL")


def check_financial_integrity():
    log("--- 2. Financial Integrity ---", "SECTION")
    
    # Need a service first
    service_id = None
    service_price = 0
    try:
        resp = requests.get(f"{BASE_URL}/services/categories", headers=get_headers("admin"))
        # This endpoint might not give individual services, let's try GET /services
        resp = requests.get(f"{BASE_URL}/services", headers=get_headers("admin"))
        if resp.status_code == 200:
            services = resp.json()
            if len(services) > 0:
                service = services[0]
                service_id = service["id"]
                service_price = float(service["base_price"])
                log(f"Found service: {service['name']} @ {service_price}", "INFO")
            else:
                log("No services found to test", "SKIP")
                return
        else:
            log(f"Failed to fetch services: {resp.status_code}", "FAIL")
            return
    except Exception as e:
        log(f"Service fetch failed: {e}", "FAIL")
        return

    # 2.1 Server-side price enforcement
    # Create transaction with tampered price
    # First, assume shift is open for admin (or open one)
    # Actually, let's open a shift for Admin just in case
    open_shift("admin")

    tx_data = {
        "items": [
            {
                "description": "Test Item",
                "quantity": 1,
                "unit_price": 1.00, # Fake low price
                "total_price": 1.00,
                "service_id": service_id
            }
        ],
        "payment_method": "cash",
        "discount_amount": 0,
        "total_amount": 1.00,
        "final_amount": 1.00
    }

    try:
        resp = requests.post(f"{BASE_URL}/transactions/", json=tx_data, headers=get_headers("admin"))
        if resp.status_code == 201:
            tx = resp.json()
            server_total = float(tx["final_amount"])
            if server_total == service_price:
                log(f"Server enforced price: Expected {service_price}, Got {server_total}", "PASS")
            else:
                log(f"Server accepted fake price! Expected {service_price}, Got {server_total}", "FAIL")
            
            # Cleanup: Void this transaction
            void_transaction(tx["id"], "admin")
        else:
            log(f"Transaction creation failed: {resp.text}", "FAIL")
    except Exception as e:
        log(f"Financial integrity test failed: {e}", "FAIL")

def open_shift(role):
    # Try to open a shift
    try:
        data = {"opening_cash": 1000}
        resp = requests.post(f"{BASE_URL}/shifts/open", json=data, headers=get_headers(role))
        if resp.status_code == 200:
            log(f"Shift opened for {role}", "INFO")
            return True
        elif resp.status_code == 400 and "already have an open shift" in resp.text:
            log(f"Shift already open for {role}", "INFO")
            return True
        else:
            log(f"Failed to open shift for {role}: {resp.text}", "FAIL")
            return False
    except Exception as e:
        log(f"Open shift failed: {e}", "FAIL")
        return False

def void_transaction(tx_id, role):
    try:
        data = {"reason": "Test Void"}
        resp = requests.post(f"{BASE_URL}/transactions/{tx_id}/void", json=data, headers=get_headers(role))
        if resp.status_code == 200:
            log(f"Transaction {tx_id} voided", "PASS")
        else:
            log(f"Failed to void transaction: {resp.text}", "FAIL")
    except Exception as e:
        log(f"Void failed: {e}", "FAIL")

def check_ops_reliability():
    log("--- 8. Ops & Reliability ---", "SECTION")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "healthy" and data.get("database") == "connected":
                log(f"Health check passed: {data}", "PASS")
            else:
                log(f"Health check operational but reported issues: {data}", "FAIL")
        else:
            log(f"Health check failed: {resp.status_code}", "FAIL")
    except Exception as e:
        log(f"Health check exception: {e}", "FAIL")

def main():
    log("Starting Production Check-Up...", "INFO")
    
    # Login all roles
    for role in USERS:
        login(role)
        
    check_auth_rbac()
    check_financial_integrity()
    check_ops_reliability()
    
    log("Check-Up Complete.", "INFO")

if __name__ == "__main__":
    main()
