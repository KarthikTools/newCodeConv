import unittest
from converters.groovy_script_converter import convert_groovy_script

class TestGroovyScriptConverter(unittest.TestCase):
    def setUp(self):
        self.sample_scripts = {
            "setup_script": """
testRunner.testCase.testSuite.project.scriptLibrary = testRunner.testCase.testSuite.project.getScriptLibrary()
""",
            "function_library": """
import groovy.json.JsonSlurper
import com.eviware.soapui.support.types.StringToStringMap
import com.eviware.soapui.support.XmlHolder
import groovy.sql.Sql

class GLF {
    def log
    def context
    def testRunner
    
    def GLF(login, contextIn, testRunnerIn) {
        this.log = login
        this.context = contextIn
        this.testRunner = testRunnerIn
    }
    
    def runTestCaseMultipleTimes(testSuiteName, testCaseName, count) {
        try {
            def project = testRunner.testCase.testSuite.project
            def tcase = project.testSuites["${testSuiteName}"].testCases["${testCaseName}"]
            def myContext = new com.eviware.soapui.support.types.StringToObjectMap(context)
            count.times {
                tcase.run(myContext, false)
                log.info "Running ${testCaseName} -- ${count}"
            }
        } catch (Exception e) {
            return e
        }
    }
    
    def enableDisableTestStep(testStepName, enabled) {
        def testStep = testRunner.testCase.testSteps[testStepName]
        testStep.disabled = !enabled
    }
    
    def SignInAvion(cardNumber, env) {
        log.info "Signing in with card number: ${cardNumber} in environment: ${env}"
        def headers = new StringToStringMap()
        
        def testSteps = context.testCase.getTestStepList()
        testSteps.each {
            if (it.config.type == "restrequest" && !(it.name in ["Signin", "pvqvalidation", "WIM"])) {
                headers.put("Cookie", "")
                headers.put("Content-Type", "application/xml")
                it.httpRequest.setRequestHeaders(headers)
                SetEndpoint(it)
            }
        }
        
        def sessionID = "JSESSIONID=DummySessionID"
        return sessionID
    }
    
    def MobiliserEnvType() {
        return context.expand('${#Project#envType}')
    }
    
    def SetEndpoint(testStep) {
        def envType = MobiliserEnvType()
        def endpoint = "https://mobile.sterbcroyalbank.com"
        testStep.testRequest.endpoint = endpoint
    }
}
""",
            "insetup_script": """
import com.eviware.soapui.support.types.StringToStringMap
def env = testRunner.testCase.testSuite.project.getPropertyValue("env")
def RT = new soapui.utils.FunctionLibrary(log, context, testRunner)
def fileStream = RT.CreateLogFile("", testRunner.testCase.testSuite.project.getPropertyValue("LogFileName"))
def cardNumber = context.expand('${#Project#CardNumber}')
def testSessionID = RT.SignInAvion(cardNumber, env)

assert RT.TestCaseFailureCheck(testRunner.testCase.testSuite.project.testSuites["LibraryFunctions"].testCases["SetupScriptLibrary"]) == true

testRunner.testCase.testSuite.project.setPropertyValue("JSESSIONID", testSessionID)
def headers = new StringToStringMap()

def testSteps = context.testCase.getTestStepList()
testSteps.each {
    if (it.config.type == "restrequest" && !(it.name in ["Signin", "pvqvalidation", "WIM"])) {
        headers.put("Cookie", testSessionID)
        headers.put("Content-Type", "application/xml")
        it.httpRequest.setRequestHeaders(headers)
        RT.SetEndpoint(it)
    }
}

headers.clear()
"""
        }
    
    def test_setup_script_conversion(self):
        """Test conversion of setup script"""
        result = convert_groovy_script(self.sample_scripts["setup_script"], "prerequest")
        self.assertIn("pm.environment.set", result)
        self.assertIn("scriptLibrary", result)
    
    def test_function_library_conversion(self):
        """Test conversion of function library"""
        result = convert_groovy_script(self.sample_scripts["function_library"], "prerequest")
        self.assertIn("class GLF", result)
        self.assertIn("SignInAvion", result)
        self.assertIn("SetEndpoint", result)
    
    def test_insetup_script_conversion(self):
        """Test conversion of insetup script"""
        result = convert_groovy_script(self.sample_scripts["insetup_script"], "prerequest")
        self.assertIn("pm.environment.get", result)
        self.assertIn("pm.request.headers.add", result)
        self.assertIn("Cookie", result)
        self.assertIn("Content-Type", result)

if __name__ == '__main__':
    unittest.main() 