import unittest
import xml.etree.ElementTree as ET
from converters.groovy_script_converter import convert_groovy_script
import re

class TestComplexConversion(unittest.TestCase):
    def setUp(self):
        # Load the sample project
        self.tree = ET.parse('input_files/sample_readyapi_project.xml')
        self.root = self.tree.getroot()
        # Register namespace
        self.ns = {'con': 'http://eviware.com/soapui/config'}

    def _extract_script_content(self, script_elem):
        """Extract script content from CDATA section"""
        if script_elem is not None:
            text = script_elem.text
            if text:
                # Remove CDATA wrapper if present
                cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
                match = re.search(cdata_pattern, text, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return text.strip()
        return None

    def test_authentication_setup_conversion(self):
        # Find the authentication setup script
        setup_script = None
        for test_suite in self.root.findall('.//con:testSuite', self.ns):
            if test_suite.get('name') == 'Authentication Suite':
                for test_case in test_suite.findall('.//con:testCase', self.ns):
                    for test_step in test_case.findall('.//con:testStep', self.ns):
                        if test_step.get('name') == 'Setup':
                            script_elem = test_step.find('.//con:config/script', self.ns)
                            setup_script = self._extract_script_content(script_elem)

        # Convert the script
        self.assertIsNotNone(setup_script, "Setup script not found")
        js_script = convert_groovy_script(setup_script, "prerequest")

        # Verify key components
        self.assertIn('class AuthenticationManager', js_script)
        self.assertIn('pm.environment.set', js_script)
        self.assertIn('scriptLibrary', js_script)
        self.assertIn('login()', js_script)
        self.assertIn('validateToken', js_script)

    def test_user_management_conversion(self):
        # Find the user management script
        user_script = None
        for test_suite in self.root.findall('.//con:testSuite', self.ns):
            if test_suite.get('name') == 'Data Management Suite':
                for test_case in test_suite.findall('.//con:testCase', self.ns):
                    for test_step in test_case.findall('.//con:testStep', self.ns):
                        if test_step.get('name') == 'Create User':
                            script_elem = test_step.find('.//con:config/script', self.ns)
                            user_script = self._extract_script_content(script_elem)

        # Convert the script
        self.assertIsNotNone(user_script, "User management script not found")
        js_script = convert_groovy_script(user_script, "test")

        # Verify key components
        self.assertIn('userManager.createUser', js_script)
        self.assertIn('pm.environment.get', js_script)
        self.assertIn('assert', js_script)
        self.assertIn('validateUser', js_script)

    def test_response_validation_conversion(self):
        # Find the response validation script
        validation_script = None
        for test_suite in self.root.findall('.//con:testSuite', self.ns):
            if test_suite.get('name') == 'API Validation Suite':
                for test_case in test_suite.findall('.//con:testCase', self.ns):
                    for test_step in test_case.findall('.//con:testStep', self.ns):
                        if test_step.get('name') == 'Validate Response':
                            script_elem = test_step.find('.//con:config/script', self.ns)
                            validation_script = self._extract_script_content(script_elem)

        # Convert the script
        self.assertIsNotNone(validation_script, "Response validation script not found")
        js_script = convert_groovy_script(validation_script, "test")

        # Verify key components
        self.assertIn('validator.validateResponse', js_script)
        self.assertIn('pm.test', js_script)
        self.assertIn('pm.expect', js_script)
        self.assertIn('console.error', js_script)
        self.assertIn('validation.isValid', js_script)
        self.assertIn('validation.errors', js_script)

if __name__ == '__main__':
    unittest.main() 