from converters.rest_request_converter import convert_rest_request
from converters.datasource_converter import convert_datasource_step
from converters.properties_converter import convert_properties_step
from converters.property_transfer_converter import convert_property_transfer_step
from analyzer.groovy_behavior_classifier import GroovyBehaviorClassifier
from typing import Dict, List, Any

def convert_groovy_to_js(groovy_script: str, operations: List[Any], script_type: str) -> str:
    """Convert Groovy script to JavaScript for Postman"""
    js_code = []
    
    if script_type == "pre-request":
        # Add setup code for pre-request script
        js_code.append("// Pre-request script converted from Groovy")
        js_code.append("// This script runs before the request is sent")
        js_code.append("// Original Groovy script:")
        js_code.append(f"// {groovy_script}")
        js_code.append("")
        
        # Add code to handle property operations
        for op in operations:
            if op.op_type == "set_property":
                js_code.append(f"pm.environment.set('{op.target}', '{op.value}');")
            elif op.op_type == "set_header":
                js_code.append(f"pm.request.headers.add({{key: '{op.target}', value: '{op.value}'}});")
            elif op.op_type == "set_endpoint":
                js_code.append(f"pm.request.url = '{op.value}';")
            elif op.op_type == "set_request_body":
                js_code.append(f"pm.request.body.raw = JSON.stringify({op.value});")
    
    elif script_type == "test":
        # Add test code for test script
        js_code.append("// Test script converted from Groovy")
        js_code.append("// This script runs after the response is received")
        js_code.append("")
        
        # Define utility classes and functions
        js_code.append("// Define utility classes")
        js_code.append("class GLF {")
        js_code.append("    constructor(log, context, testRunner) {")
        js_code.append("        this.log = log;")
        js_code.append("        this.context = context;")
        js_code.append("        this.testRunner = testRunner;")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    // Function to run a test case multiple times")
        js_code.append("    runTestCaseMultipleTimes(testSuiteName, testCaseName, count) {")
        js_code.append("        try {")
        js_code.append("            console.log(`Running ${testCaseName} ${count} times`);")
        js_code.append("        } catch (e) {")
        js_code.append("            return e;")
        js_code.append("        }")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    // Function to enable and disable a test step")
        js_code.append("    enableDisableTestStep(testStepName, enabled) {")
        js_code.append("        console.log(`Setting ${testStepName} to ${enabled ? 'enabled' : 'disabled'}`);")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    // SignIn function")
        js_code.append("    SignInAvion(cardNumber, env) {")
        js_code.append("        console.log(`Signing in with card number: ${cardNumber} in environment: ${env}`);")
        js_code.append("        const sessionID = 'JSESSIONID=DummySessionID';")
        js_code.append("        return sessionID;")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    // Environment functions")
        js_code.append("    MobiliserEnvType() {")
        js_code.append("        return pm.environment.get('envType');")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    SetEndpoint(testStep) {")
        js_code.append("        const envType = this.MobiliserEnvType();")
        js_code.append("        const endpoint = 'https://mobile.sterbcroyalbank.com';")
        js_code.append("        console.log(`Setting endpoint to ${endpoint}`);")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    TestCaseFailureCheck(testCase) {")
        js_code.append("        return true;")
        js_code.append("    }")
        js_code.append("    ")
        js_code.append("    // Logging function")
        js_code.append("    CreateLogFile(fileName) {")
        js_code.append("        console.log(`Creating log file: ${fileName}`);")
        js_code.append("        return fileName;")
        js_code.append("    }")
        js_code.append("}")
        js_code.append("")
        js_code.append("// Initialize the GLF class")
        js_code.append("const glf = new GLF(console, pm, pm);")
        js_code.append("")
        
        # Add assertions based on Groovy assertions
        for op in operations:
            if op.op_type == "assertion":
                # Convert Groovy assertions to Postman tests
                if "response.code" in op.line:
                    js_code.append("pm.test('Status code is 200', function () {")
                    js_code.append("    pm.response.to.have.status(200);")
                    js_code.append("});")
                elif "response.json" in op.line:
                    js_code.append("pm.test('Response is JSON', function () {")
                    js_code.append("    pm.response.to.be.json;")
                    js_code.append("});")
                elif "response.time" in op.line:
                    js_code.append("pm.test('Response time is acceptable', function () {")
                    js_code.append("    pm.expect(pm.response.responseTime).to.be.below(2000);")
                    js_code.append("});")
                else:
                    # Generic assertion
                    js_code.append(f"pm.test('Assertion: {op.line}', function () {{")
                    js_code.append(f"    // TODO: Convert Groovy assertion to JavaScript")
                    js_code.append(f"    // Original: {op.line}")
                    js_code.append(f"}});")
            elif op.op_type == "extract_property":
                js_code.append(f"// Extract property: {op.target}")
                js_code.append(f"const response = pm.response.json();")
                js_code.append(f"pm.environment.set('{op.target}', response.{op.path});")
    
    return "\n".join(js_code)

def convert_groovy_step(test_step, context: Dict) -> List[Dict[str, Any]]:
    """Convert a Groovy script step to Postman format with pre-request and test scripts"""
    try:
        # Extract script content
        script_text = ""
        if hasattr(test_step.config, 'findtext'):
            script_text = test_step.config.findtext('.//script', '')
        else:
            script_text = str(test_step.config)
            
        # Analyze the script to understand its behavior
        operations = GroovyBehaviorClassifier(test_step.config).classify()
        
        # Create a Postman request with pre-request and test scripts
        result = {
            "name": test_step.name,
            "type": "groovy",
            "test_case": context.get("test_case_name", "Main Tests"),
            "pre_request_script": convert_groovy_to_js(script_text, operations, "pre-request"),
            "test_script": convert_groovy_to_js(script_text, operations, "test"),
            "note": f"Converted from Groovy script: {test_step.name}"
        }
        
        # Register operations for flow analysis
        for op in operations:
            context.get("flow_builder", None).register_operation_for_test_case(
                context.get("test_case_name", "Main Tests"), 
                op.op_type
            )
            
        return [result]
    except Exception as e:
        print(f"[ERROR] Failed to convert Groovy step '{test_step.name}': {e}")
        return []

STEP_HANDLERS = {
    "restrequest": convert_rest_request,
    "httprequest": convert_rest_request,
    "datasource": convert_datasource_step,
    "properties": convert_properties_step,
    "property-transfer": convert_property_transfer_step,
    "groovy": convert_groovy_step,
}

def dispatch_step_conversion(test_step, context: Dict):
    if isinstance(test_step, str):
        step_type = test_step.lower()
    else:
        step_type = test_step.step_type.lower()
        
    handler = STEP_HANDLERS.get(step_type)
    if handler:
        result = handler(test_step, context)
        # Add test case information to the result
        if isinstance(result, dict):
            result["test_case"] = context.get("test_case_name", "Main Tests")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    item["test_case"] = context.get("test_case_name", "Main Tests")
        return result
    else:
        print(f"[WARN] Unsupported step type: {step_type}, skipping.")
        return None
