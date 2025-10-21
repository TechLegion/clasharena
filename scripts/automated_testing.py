#!/usr/bin/env python3
"""
Automated testing script for ClashArena
"""

import os
import sys
import subprocess
import logging
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_testing.log'),
        logging.StreamHandler()
    ]
)

class AutomatedTester:
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'http://localhost:8001')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.test_results = []
        
    def run_command(self, command: str, cwd: str = None) -> tuple:
        """Run a command and return (success, output, error)"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def run_backend_tests(self) -> Dict[str, Any]:
        """Run backend tests"""
        logging.info("Running backend tests...")
        
        test_result = {
            "type": "backend",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run pytest
        success, stdout, stderr = self.run_command("pytest --cov=app --cov-report=json", cwd="backend")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Backend tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.error(f"Backend tests failed: {stderr}")
        
        return test_result
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend tests"""
        logging.info("Running frontend tests...")
        
        test_result = {
            "type": "frontend",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run npm test
        success, stdout, stderr = self.run_command("npm test -- --coverage --watchAll=false", cwd="frontend")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Frontend tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.error(f"Frontend tests failed: {stderr}")
        
        return test_result
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        logging.info("Running integration tests...")
        
        test_result = {
            "type": "integration",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run API tests
        success, stdout, stderr = self.run_command("python scripts/test_api.py")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Integration tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.error(f"Integration tests failed: {stderr}")
        
        return test_result
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        logging.info("Running security tests...")
        
        test_result = {
            "type": "security",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run bandit security scan
        success, stdout, stderr = self.run_command("bandit -r backend/ -f json", cwd=".")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Security tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.error(f"Security tests failed: {stderr}")
        
        return test_result
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        logging.info("Running performance tests...")
        
        test_result = {
            "type": "performance",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run load tests with locust (if available)
        success, stdout, stderr = self.run_command("locust --headless -u 10 -r 2 -t 30s --host=http://localhost:8001")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Performance tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.warning(f"Performance tests failed or skipped: {stderr}")
        
        return test_result
    
    def run_accessibility_tests(self) -> Dict[str, Any]:
        """Run accessibility tests"""
        logging.info("Running accessibility tests...")
        
        test_result = {
            "type": "accessibility",
            "status": "failed",
            "details": {},
            "timestamp": time.time()
        }
        
        # Run axe-core tests (if available)
        success, stdout, stderr = self.run_command("npm run test:a11y", cwd="frontend")
        
        if success:
            test_result["status"] = "passed"
            test_result["details"]["output"] = stdout
            logging.info("Accessibility tests passed")
        else:
            test_result["details"]["error"] = stderr
            test_result["details"]["output"] = stdout
            logging.warning(f"Accessibility tests failed or skipped: {stderr}")
        
        return test_result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all tests"""
        logging.info("Starting automated testing suite...")
        
        tests = [
            self.run_backend_tests,
            self.run_frontend_tests,
            self.run_integration_tests,
            self.run_security_tests,
            self.run_performance_tests,
            self.run_accessibility_tests
        ]
        
        results = []
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                self.test_results.append(result)
            except Exception as e:
                logging.error(f"Test {test_func.__name__} failed with exception: {str(e)}")
                results.append({
                    "type": test_func.__name__,
                    "status": "error",
                    "details": {"exception": str(e)},
                    "timestamp": time.time()
                })
        
        return results
    
    def generate_report(self) -> str:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results if r["status"] == "failed"])
        error_tests = len([r for r in self.test_results if r["status"] == "error"])
        
        report = f"""
# ClashArena Automated Test Report

## Summary
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Errors: {error_tests}
- Success Rate: {(passed_tests / total_tests * 100):.1f}%

## Test Results
"""
        
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            report += f"\n### {status_emoji} {result['type'].title()} Tests\n"
            report += f"- Status: {result['status']}\n"
            report += f"- Timestamp: {time.ctime(result['timestamp'])}\n"
            
            if result["details"].get("error"):
                report += f"- Error: {result['details']['error']}\n"
            
            if result["details"].get("output"):
                report += f"- Output: {result['details']['output'][:500]}...\n"
        
        return report
    
    def save_report(self, filename: str = "test_report.md"):
        """Save test report to file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        logging.info(f"Test report saved to {filename}")

def main():
    """Main function"""
    tester = AutomatedTester()
    
    # Check if services are running
    logging.info("Checking if services are running...")
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Generate and save report
    tester.save_report()
    
    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r["status"] == "passed"])
    
    print(f"\n{'='*50}")
    print(f"Test Summary: {passed_tests}/{total_tests} tests passed")
    print(f"{'='*50}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the test report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
