#!/usr/bin/env python3
"""
Health monitoring script for ClashArena services
"""

import os
import sys
import time
import requests
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_monitor.log'),
        logging.StreamHandler()
    ]
)

class HealthMonitor:
    def __init__(self):
        self.services = {
            "Backend API": {
                "url": os.getenv('BACKEND_URL', 'http://localhost:8001/health'),
                "timeout": 10,
                "critical": True
            },
            "Database": {
                "url": os.getenv('DB_HEALTH_URL', 'http://localhost:8001/health/db'),
                "timeout": 5,
                "critical": True
            },
            "Redis": {
                "url": os.getenv('REDIS_HEALTH_URL', 'http://localhost:8001/health/redis'),
                "timeout": 5,
                "critical": True
            },
            "Celery Worker": {
                "url": os.getenv('CELERY_HEALTH_URL', 'http://localhost:8001/health/celery'),
                "timeout": 5,
                "critical": False
            }
        }
        
        self.email_config = {
            "smtp_server": os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            "smtp_port": int(os.getenv('SMTP_PORT', '587')),
            "username": os.getenv('SMTP_USERNAME'),
            "password": os.getenv('SMTP_PASSWORD'),
            "from_email": os.getenv('FROM_EMAIL'),
            "to_emails": os.getenv('TO_EMAILS', '').split(',')
        }
        
        self.alert_threshold = int(os.getenv('ALERT_THRESHOLD', '3'))  # Number of consecutive failures
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))  # Seconds between checks
        
        self.failure_counts = {service: 0 for service in self.services.keys()}
        self.last_alert_sent = {service: None for service in self.services.keys()}
        self.alert_cooldown = int(os.getenv('ALERT_COOLDOWN', '3600'))  # Seconds between alerts

    def check_service(self, service_name: str, config: Dict) -> Tuple[bool, str]:
        """Check if a service is healthy"""
        try:
            response = requests.get(
                config['url'],
                timeout=config['timeout'],
                headers={'User-Agent': 'ClashArena-HealthMonitor/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, "Healthy"
                else:
                    return False, f"Unhealthy: {data.get('message', 'Unknown error')}"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def send_alert(self, service_name: str, error_message: str, is_recovery: bool = False):
        """Send email alert"""
        if not all([self.email_config['username'], self.email_config['password'], 
                   self.email_config['from_email'], self.email_config['to_emails']]):
            logging.warning("Email configuration incomplete, skipping alert")
            return
        
        # Check cooldown
        now = datetime.now()
        last_alert = self.last_alert_sent[service_name]
        
        if last_alert and (now - last_alert).seconds < self.alert_cooldown:
            logging.info(f"Alert cooldown active for {service_name}, skipping alert")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            
            if is_recovery:
                msg['Subject'] = f"✅ ClashArena Service Recovered: {service_name}"
                body = f"""
Service Recovery Alert

Service: {service_name}
Status: Recovered
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Message: {error_message}

The service is now back online and functioning normally.

---
ClashArena Health Monitor
"""
            else:
                msg['Subject'] = f"🚨 ClashArena Service Alert: {service_name}"
                body = f"""
Service Alert

Service: {service_name}
Status: Critical Failure
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Error: {error_message}

This service has failed {self.failure_counts[service_name]} consecutive health checks.

Please investigate immediately.

---
ClashArena Health Monitor
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], self.email_config['to_emails'], text)
            server.quit()
            
            self.last_alert_sent[service_name] = now
            logging.info(f"Alert sent for {service_name}")
            
        except Exception as e:
            logging.error(f"Failed to send alert for {service_name}: {str(e)}")

    def check_all_services(self):
        """Check all services and handle alerts"""
        logging.info("Starting health check cycle")
        
        for service_name, config in self.services.items():
            is_healthy, message = self.check_service(service_name, config)
            
            if is_healthy:
                if self.failure_counts[service_name] > 0:
                    # Service recovered
                    logging.info(f"✅ {service_name}: {message} (Recovered)")
                    self.send_alert(service_name, message, is_recovery=True)
                    self.failure_counts[service_name] = 0
                else:
                    logging.info(f"✅ {service_name}: {message}")
            else:
                self.failure_counts[service_name] += 1
                logging.warning(f"❌ {service_name}: {message} (Failure #{self.failure_counts[service_name]})")
                
                # Send alert if threshold reached
                if self.failure_counts[service_name] >= self.alert_threshold:
                    if config['critical']:
                        self.send_alert(service_name, message)
                    else:
                        logging.info(f"Non-critical service {service_name} failed, not sending alert")

    def run(self):
        """Run the health monitor continuously"""
        logging.info("Starting ClashArena Health Monitor")
        logging.info(f"Check interval: {self.check_interval} seconds")
        logging.info(f"Alert threshold: {self.alert_threshold} failures")
        logging.info(f"Alert cooldown: {self.alert_cooldown} seconds")
        
        try:
            while True:
                self.check_all_services()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logging.info("Health monitor stopped by user")
        except Exception as e:
            logging.error(f"Health monitor error: {str(e)}")
            sys.exit(1)

def main():
    """Main function"""
    monitor = HealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        # Run once instead of continuously
        monitor.check_all_services()
    else:
        # Run continuously
        monitor.run()

if __name__ == "__main__":
    main()
