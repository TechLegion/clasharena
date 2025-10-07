#!/usr/bin/env python3
"""
Health check script for ClashArena services
"""

import requests
import sys
import time

SERVICES = {
    "ClashArena Backend": "http://localhost:8001/health"
}

def check_service(name, url):
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("status", "unknown")
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, str(e)

def main():
    """Main health check function"""
    print("ClashArena Services Health Check")
    print("================================")
    
    all_healthy = True
    
    for service_name, url in SERVICES.items():
        print(f"Checking {service_name}...", end=" ")
        is_healthy, status = check_service(service_name, url)
        
        if is_healthy:
            print(f"✅ Healthy ({status})")
        else:
            print(f"❌ Unhealthy ({status})")
            all_healthy = False
    
    print("\n" + "="*40)
    
    if all_healthy:
        print("🎉 All services are healthy!")
        sys.exit(0)
    else:
        print("⚠️  Some services are unhealthy!")
        sys.exit(1)

if __name__ == "__main__":
    main()
