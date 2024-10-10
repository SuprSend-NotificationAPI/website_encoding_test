import requests
from bs4 import BeautifulSoup
import sys
import chardet
import json
from urllib.parse import urljoin
import logging
from datetime import datetime

class EncodingTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            filename=f'encoding_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def test_http_headers(self):
        """Test HTTP headers for proper charset declaration"""
        try:
            response = requests.head(self.base_url)
            content_type = response.headers.get('Content-Type', '')
            
            self.logger.info(f"Testing HTTP Headers for: {self.base_url}")
            self.logger.info(f"Content-Type header: {content_type}")
            
            if 'charset=utf-8' in content_type.lower():
                return True, "Content-Type header properly declares UTF-8"
            else:
                return False, "Content-Type header missing charset declaration"
        except Exception as e:
            return False, f"Error testing HTTP headers: {str(e)}"

    def test_html_meta(self):
        """Test HTML meta tags for charset declaration"""
        try:
            response = requests.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check meta charset tag
            meta_charset = soup.find('meta', charset=True)
            meta_content_type = soup.find('meta', {'http-equiv': 'Content-Type'})
            
            issues = []
            if meta_charset and meta_charset['charset'].lower() == 'utf-8':
                self.logger.info("Found valid meta charset tag")
            else:
                issues.append("Missing or invalid meta charset tag")
                
            if meta_content_type and 'charset=utf-8' in meta_content_type.get('content', '').lower():
                self.logger.info("Found valid meta content-type tag")
            else:
                issues.append("Missing or invalid meta content-type tag")
                
            return len(issues) == 0, issues if issues else "HTML meta tags properly declare UTF-8"
        except Exception as e:
            return False, f"Error testing HTML meta tags: {str(e)}"

    def test_content_encoding(self, test_strings):
        """Test if content can handle various UTF-8 characters"""
        results = []
        for lang, text in test_strings.items():
            try:
                # Test encoding
                encoded = text.encode('utf-8')
                decoded = encoded.decode('utf-8')
                
                if decoded == text:
                    results.append((lang, True, "Successfully encoded and decoded"))
                else:
                    results.append((lang, False, "Encoding/decoding mismatch"))
                    
            except UnicodeError as e:
                results.append((lang, False, f"Encoding error: {str(e)}"))
                
        return results

    def detect_encoding(self, url):
        """Detect the actual encoding of a page"""
        try:
            response = requests.get(url)
            raw_content = response.content
            detected = chardet.detect(raw_content)
            return detected
        except Exception as e:
            return {"error": str(e)}

    def run_full_test(self):
        """Run all encoding tests and generate a report"""
        self.logger.info("Starting full encoding test")
        
        test_strings = {
            "Japanese": "開発者向けのツール",
            "Korean": "개발자를 위한 도구",
            "Russian": "инструменты для разработчиков",
            "Chinese": "开发人员工具",
            "Vietnamese": "công cụ cho nhà phát triển",
            "Special": "🔧 → ♠ × ≠ ≤ ÷"
        }
        
        results = {
            "url": self.base_url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test HTTP headers
        header_success, header_message = self.test_http_headers()
        results["tests"]["http_headers"] = {
            "success": header_success,
            "message": header_message
        }
        
        # Test HTML meta tags
        meta_success, meta_message = self.test_html_meta()
        results["tests"]["html_meta"] = {
            "success": meta_success,
            "message": meta_message
        }
        
        # Test content encoding
        content_results = self.test_content_encoding(test_strings)
        results["tests"]["content_encoding"] = {
            "success": all(result[1] for result in content_results),
            "details": {lang: {"success": success, "message": message} 
                       for lang, success, message in content_results}
        }
        
        # Detect actual encoding
        detected_encoding = self.detect_encoding(self.base_url)
        results["tests"]["detected_encoding"] = detected_encoding
        
        # Generate report
        self.generate_report(results)
        return results

    def generate_report(self, results):
        """Generate a detailed report of all test results"""
        report_filename = f'encoding_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Report generated: {report_filename}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python encoding_test.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    tester = EncodingTester(url)
    results = tester.run_full_test()
    
    # Print summary to console
    print("\n=== Encoding Test Results ===")
    print(f"URL: {results['url']}")
    print("\nTest Results:")
    for test_name, test_data in results['tests'].items():
        if isinstance(test_data, dict) and 'success' in test_data:
            status = "✅ PASS" if test_data['success'] else "❌ FAIL"
            print(f"{test_name}: {status}")
            if 'message' in test_data:
                print(f"  Message: {test_data['message']}")
        else:
            print(f"{test_name}: {test_data}")
    print("\nDetailed report has been saved to the encoding_report_*.json file")

if __name__ == "__main__":
    main()