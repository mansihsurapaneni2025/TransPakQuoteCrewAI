"""
Comprehensive API Test Suite for TransPak AI Quoter
Tests all endpoints, A2A protocol functionality, and system integration
"""

import json
import asyncio
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APITestSuite:
    """Comprehensive test suite for all TransPak API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TransPak-API-Test-Suite/1.0'
        })
        self.test_results = []
        
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Execute complete test suite"""
        print("🚀 Starting TransPak API Comprehensive Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test categories
        test_categories = [
            ("Basic Connectivity", self._test_basic_connectivity),
            ("Web Application Routes", self._test_web_routes),
            ("A2A Protocol Discovery", self._test_a2a_discovery),
            ("A2A Agent Communication", self._test_a2a_communication),
            ("Quote Generation", self._test_quote_generation),
            ("System Analytics", self._test_analytics_endpoints),
            ("Error Handling", self._test_error_handling),
            ("Performance Testing", self._test_performance)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n📋 Testing: {category_name}")
            print("-" * 40)
            try:
                test_function()
            except Exception as e:
                self._log_test_result(category_name, "FAILED", f"Category failed: {str(e)}")
                print(f"❌ Category failed: {str(e)}")
        
        # Generate summary report
        total_time = time.time() - start_time
        return self._generate_test_report(total_time)
    
    def _test_basic_connectivity(self):
        """Test basic system connectivity and health"""
        tests = [
            ("Health Check", "GET", "/health"),
            ("Homepage", "GET", "/"),
            ("A2A System Ping", "GET", "/api/v1/a2a/test/ping")
        ]
        
        for test_name, method, endpoint in tests:
            self._execute_test(test_name, method, endpoint)
    
    def _test_web_routes(self):
        """Test all web application routes"""
        web_routes = [
            ("Homepage", "GET", "/"),
            ("AI Agents Process", "GET", "/ai-agents-process"),
            ("A2A Demo Page", "GET", "/a2a-demo"),
            ("Knowledge Base", "GET", "/knowledge-base"),
            ("Login Page", "GET", "/auth/login"),
            ("Register Page", "GET", "/auth/register")
        ]
        
        for test_name, method, endpoint in web_routes:
            self._execute_test(test_name, method, endpoint, expected_status=[200, 302])
    
    def _test_a2a_discovery(self):
        """Test A2A agent discovery functionality"""
        discovery_tests = [
            ("Agent Registry Status", "GET", "/api/v1/a2a/registry/status"),
            ("Discover All Agents", "GET", "/api/v1/a2a/agents"),
            ("Agent Capabilities", "GET", "/api/v1/a2a/agents/transpak_sales_briefing_agent/capabilities"),
            ("Skill-based Discovery", "GET", "/api/v1/a2a/skills/analyze_shipment/agents")
        ]
        
        for test_name, method, endpoint in discovery_tests:
            result = self._execute_test(test_name, method, endpoint)
            if result and result.get('success'):
                self._validate_a2a_response_structure(test_name, result)
    
    def _test_a2a_communication(self):
        """Test A2A protocol communication features"""
        # Test skill query
        skill_query_data = {
            "parameters": {
                "shipment_data": {
                    "item_description": "Test equipment",
                    "weight": "50 lbs"
                }
            }
        }
        
        result = self._execute_test(
            "A2A Skill Query",
            "POST",
            "/api/v1/a2a/agents/transpak_sales_briefing_agent/skills/analyze_shipment/query",
            data=skill_query_data
        )
        
        # Test agent message sending
        message_data = {
            "sender_id": "test_client",
            "message_type": "skill_query",
            "payload": {
                "skill_id": "analyze_shipment",
                "parameters": {"test": True}
            }
        }
        
        self._execute_test(
            "A2A Message Sending",
            "POST",
            "/api/v1/a2a/agents/transpak_sales_briefing_agent/message",
            data=message_data
        )
        
        # Test communication mode negotiation
        negotiation_data = {
            "agent_id": "transpak_sales_briefing_agent",
            "preferred_modes": ["json", "text"]
        }
        
        self._execute_test(
            "Communication Negotiation",
            "POST",
            "/api/v1/a2a/communication/negotiate",
            data=negotiation_data
        )
    
    def _test_quote_generation(self):
        """Test quote generation functionality"""
        # Test data for quote generation
        test_shipment_data = {
            "shipment_data": {
                "item_description": "High-precision electronic measurement equipment",
                "dimensions": "36 x 24 x 18 inches",
                "weight": "85 lbs",
                "origin": "San Francisco, CA",
                "destination": "Boston, MA",
                "fragility": "High",
                "special_requirements": "Temperature controlled",
                "timeline": "5 business days"
            }
        }
        
        # Test A2A workflow execution
        result = self._execute_test(
            "A2A Workflow Execution",
            "POST",
            "/api/v1/a2a/workflow/execute",
            data=test_shipment_data
        )
        
        if result and result.get('success'):
            self._validate_quote_structure(result.get('workflow_result', {}))
    
    def _test_analytics_endpoints(self):
        """Test analytics and monitoring endpoints"""
        analytics_tests = [
            ("System Metrics", "GET", "/api/system/metrics"),
            ("Cost Analysis", "GET", "/api/analytics/cost-analysis")
        ]
        
        for test_name, method, endpoint in analytics_tests:
            self._execute_test(test_name, method, endpoint)
    
    def _test_error_handling(self):
        """Test error handling and edge cases"""
        error_tests = [
            ("Invalid Agent ID", "GET", "/api/v1/a2a/agents/invalid_agent_id"),
            ("Invalid Skill Query", "POST", "/api/v1/a2a/agents/transpak_sales_briefing_agent/skills/invalid_skill/query", {}),
            ("Malformed JSON", "POST", "/api/v1/a2a/workflow/execute", "invalid_json"),
            ("Missing Required Data", "POST", "/api/v1/a2a/workflow/execute", {})
        ]
        
        for test_name, method, endpoint, *args in error_tests:
            data = args[0] if args else None
            self._execute_test(test_name, method, endpoint, data=data, expected_status=[400, 404, 500])
    
    def _test_performance(self):
        """Test system performance and response times"""
        performance_tests = [
            ("/api/v1/a2a/test/ping", "System Ping"),
            ("/api/v1/a2a/registry/status", "Registry Status"),
            ("/api/v1/a2a/agents", "Agent Discovery")
        ]
        
        for endpoint, test_name in performance_tests:
            start_time = time.time()
            response = self._make_request("GET", endpoint)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response and response.status_code == 200:
                status = "PASS" if response_time < 1000 else "SLOW"
                self._log_test_result(
                    f"{test_name} Performance",
                    status,
                    f"Response time: {response_time:.2f}ms"
                )
                print(f"⏱️  {test_name}: {response_time:.2f}ms")
            else:
                self._log_test_result(f"{test_name} Performance", "FAIL", "No response")
    
    def _execute_test(self, test_name: str, method: str, endpoint: str, 
                     data: Any = None, expected_status: List[int] = None) -> Optional[Dict[str, Any]]:
        """Execute a single test case"""
        if expected_status is None:
            expected_status = [200]
        
        try:
            response = self._make_request(method, endpoint, data)
            
            if not response:
                self._log_test_result(test_name, "FAIL", "No response received")
                print(f"❌ {test_name}: No response")
                return None
            
            if response.status_code in expected_status:
                try:
                    result = response.json() if response.content else {}
                    self._log_test_result(test_name, "PASS", f"Status: {response.status_code}")
                    print(f"✅ {test_name}: {response.status_code}")
                    return result
                except json.JSONDecodeError:
                    self._log_test_result(test_name, "PASS", f"Status: {response.status_code} (HTML response)")
                    print(f"✅ {test_name}: {response.status_code} (HTML)")
                    return {}
            else:
                self._log_test_result(test_name, "FAIL", f"Unexpected status: {response.status_code}")
                print(f"❌ {test_name}: Expected {expected_status}, got {response.status_code}")
                return None
                
        except Exception as e:
            self._log_test_result(test_name, "ERROR", str(e))
            print(f"💥 {test_name}: {str(e)}")
            return None
    
    def _make_request(self, method: str, endpoint: str, data: Any = None) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                return self.session.get(url, timeout=10)
            elif method == "POST":
                if isinstance(data, str):
                    # Test malformed JSON
                    return self.session.post(url, data=data, timeout=10)
                else:
                    return self.session.post(url, json=data, timeout=10)
            elif method == "PUT":
                return self.session.put(url, json=data, timeout=10)
            elif method == "DELETE":
                return self.session.delete(url, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    def _validate_a2a_response_structure(self, test_name: str, response: Dict[str, Any]):
        """Validate A2A response structure"""
        required_fields = ['success']
        
        for field in required_fields:
            if field not in response:
                self._log_test_result(f"{test_name} Structure", "FAIL", f"Missing field: {field}")
                return
        
        self._log_test_result(f"{test_name} Structure", "PASS", "Valid A2A response structure")
    
    def _validate_quote_structure(self, quote_result: Dict[str, Any]):
        """Validate quote generation result structure"""
        if not quote_result.get('success'):
            self._log_test_result("Quote Structure", "FAIL", "Quote generation failed")
            return
        
        required_sections = ['results', 'workflow_id', 'total_processing_time']
        
        for section in required_sections:
            if section not in quote_result:
                self._log_test_result("Quote Structure", "FAIL", f"Missing section: {section}")
                return
        
        # Validate workflow results structure
        results = quote_result.get('results', {})
        expected_stages = ['analysis', 'packaging', 'logistics', 'final_quote']
        
        for stage in expected_stages:
            if stage not in results:
                self._log_test_result("Quote Workflow", "FAIL", f"Missing workflow stage: {stage}")
                return
        
        self._log_test_result("Quote Structure", "PASS", "Valid quote workflow structure")
    
    def _log_test_result(self, test_name: str, status: str, details: str):
        """Log test result for reporting"""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']])
        slow = len([r for r in self.test_results if r['status'] == 'SLOW'])
        total = len(self.test_results)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Slow: {slow}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        # Detailed results
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  • {result['test_name']}: {result['details']}")
        
        if slow > 0:
            print("\n⏱️  SLOW TESTS:")
            for result in self.test_results:
                if result['status'] == 'SLOW':
                    print(f"  • {result['test_name']}: {result['details']}")
        
        return {
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'slow': slow,
                'success_rate': success_rate,
                'total_time': total_time
            },
            'detailed_results': self.test_results,
            'timestamp': datetime.utcnow().isoformat()
        }

def run_api_tests():
    """Main function to run API tests"""
    test_suite = APITestSuite()
    return test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    results = run_api_tests()
    
    # Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: test_results.json")