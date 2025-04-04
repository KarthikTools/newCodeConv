import re
import logging
from typing import List, Dict, Any, Optional
from analyzer.groovy_behavior_classifier import GroovyBehaviorClassifier, GroovyOperation

logger = logging.getLogger(__name__)

class GroovyScriptConverter:
    def __init__(self):
        # No predefined functions - we'll handle them generically
        pass
        
    def convert(self, groovy_script: str, script_type: str = "prerequest") -> str:
        """
        Convert a Groovy script to JavaScript
        """
        try:
            # Initialize classifier
            classifier = GroovyBehaviorClassifier(groovy_script)
            operations = classifier.classify()
            
            # Start with header comments
            js_lines = [
                f"// {script_type.capitalize()} script converted from Groovy",
                "// This script runs before the request is sent" if script_type == "prerequest" else "// This script runs after the response is received",
                ""
            ]
            
            # Process each operation
            for op in operations:
                if op.op_type == "function_def":
                    js_lines.extend(self._convert_function_definition(op))
                elif op.op_type == "function_call":
                    js_lines.extend(self._convert_function_call(op))
                elif op.op_type == "set_property":
                    js_lines.extend(self._convert_set_property(op))
                elif op.op_type == "set_header":
                    js_lines.extend(self._convert_set_header(op))
                elif op.op_type == "set_endpoint":
                    js_lines.extend(self._convert_set_endpoint(op))
                elif op.op_type == "assertion":
                    js_lines.extend(self._convert_assertion(op))
                elif op.op_type == "import":
                    # Skip imports as they're not needed in JavaScript
                    continue
                elif op.op_type == "class_def":
                    js_lines.extend(self._convert_class_definition(op))
                elif op.op_type == "variable_def":
                    js_lines.extend(self._convert_variable_definition(op))
                elif op.op_type == "script_library":
                    js_lines.extend(self._convert_script_library(op))
            
            return "\n".join(js_lines)
            
        except Exception as e:
            logger.error(f"Failed to convert Groovy script: {str(e)}")
            return f"// Error converting Groovy script: {str(e)}"
    
    def _convert_class_definition(self, op: GroovyOperation) -> List[str]:
        """Convert a Groovy class definition to JavaScript"""
        lines = []
        # Extract class name and properties
        match = re.match(r'class\s+(\w+)', op.line)
        if match:
            class_name = match.group(1)
            lines.append(f"// Class {class_name} converted to JavaScript")
            lines.append(f"class {class_name} {{")
            
            # Add constructor with dynamic parameters
            params = self._extract_constructor_params(op.line)
            param_list = ", ".join(params) if params else ""
            lines.append(f"    constructor({param_list}) {{")
            for param in params:
                lines.append(f"        this.{param} = {param};")
            lines.append("    }")
            lines.append("}")
            lines.append("")
        return lines
    
    def _extract_constructor_params(self, class_line: str) -> List[str]:
        """Extract constructor parameters from class definition"""
        # Look for property definitions in the class
        params = []
        prop_pattern = r'def\s+(\w+)'
        matches = re.finditer(prop_pattern, class_line)
        for match in matches:
            params.append(match.group(1))
        return params
    
    def _convert_variable_definition(self, op: GroovyOperation) -> List[str]:
        """Convert a Groovy variable definition to JavaScript"""
        lines = []
        # Extract variable name and value
        match = re.match(r'def\s+(\w+)\s*=\s*(.*)', op.line)
        if match:
            var_name = match.group(1)
            value = match.group(2)
            
            # Handle environment variable expansion
            if "${#Project#" in value:
                env_var = re.search(r'\${#Project#(\w+)}', value).group(1)
                lines.append(f"const {var_name} = pm.environment.get('{env_var}');")
            # Handle property value getter
            elif "getPropertyValue" in value:
                prop_match = re.search(r'getPropertyValue\(["\'](\w+)["\']', value)
                if prop_match:
                    prop_name = prop_match.group(1)
                    lines.append(f"const {var_name} = pm.environment.get('{prop_name}');")
            # Handle new object creation
            elif value.startswith("new "):
                lines.append(f"const {var_name} = {{}};  // Converted from {value}")
            # Handle string concatenation
            elif "+" in value:
                parts = value.split("+")
                concat_parts = []
                for part in parts:
                    part = part.strip()
                    if part.startswith('"') or part.startswith("'"):
                        concat_parts.append(part)
                    else:
                        concat_parts.append(f"${{pm.environment.get('{part.strip()}') || '{part.strip()}'}}")
                lines.append(f"const {var_name} = `{''.join(concat_parts)}`;")
            else:
                lines.append(f"const {var_name} = {value};")
            lines.append("")
        return lines
    
    def _convert_script_library(self, op: GroovyOperation) -> List[str]:
        """Convert script library assignment to JavaScript"""
        lines = [
            "// Set script library",
            "pm.environment.set('scriptLibrary', pm.environment.get('scriptLibrary') || {});",
            ""
        ]
        return lines
    
    def _convert_function_definition(self, op: GroovyOperation) -> List[str]:
        """Convert a Groovy function definition to JavaScript"""
        lines = []
        # Extract function name and parameters
        match = re.match(r'def\s+(\w+)\s*\((.*)\)', op.line)
        if match:
            func_name = match.group(1)
            params = match.group(2).split(',')
            params = [p.strip() for p in params if p.strip()]
            
            # Convert to JavaScript function
            lines.append(f"function {func_name}({', '.join(params)}) {{")
            
            # Add generic function body that handles common ReadyAPI operations
            lines.extend([
                "    // Generic function implementation",
                "    const functionName = arguments.callee.name;",
                "    console.log(`Executing ${functionName} with params:`, ...arguments);",
                "",
                "    // Handle common ReadyAPI operations",
                "    if (arguments.length > 0) {",
                "        // Store function arguments in environment",
                "        arguments.forEach((arg, index) => {",
                "            pm.environment.set(`${functionName}_arg${index}`, arg);",
                "        });",
                "    }",
                "",
                "    // Check for endpoint setting",
                "    if (op.line.includes('endpoint') || op.line.includes('url')) {",
                "        const endpoint = pm.environment.get('baseUrl');",
                "        if (endpoint) {",
                "            pm.request.url = endpoint;",
                "            console.log(`Set endpoint to ${endpoint}`);",
                "        }",
                "    }",
                "",
                "    // Check for header operations",
                "    if (op.line.includes('headers') || op.line.includes('Cookie')) {",
                "        const headers = pm.environment.get('headers') || {};",
                "        Object.entries(headers).forEach(([key, value]) => {",
                "            pm.request.headers.add({key, value});",
                "        });",
                "    }",
                "",
                "    // Return any stored result",
                "    return pm.environment.get(`${functionName}_result`);",
            ])
            lines.append("}")
            lines.append("")
        return lines
    
    def _convert_function_call(self, op: GroovyOperation) -> List[str]:
        """Convert a Groovy function call to JavaScript"""
        lines = []
        # Extract function name and arguments
        match = re.match(r'(\w+)\s*\((.*)\)', op.line)
        if match:
            func_name = match.group(1)
            args = match.group(2).split(',')
            args = [arg.strip() for arg in args if arg.strip()]
            
            # Convert arguments to handle environment variables
            converted_args = []
            for arg in args:
                if arg.startswith('"') or arg.startswith("'"):
                    converted_args.append(arg)
                else:
                    converted_args.append(f"pm.environment.get('{arg}') || '{arg}'")
            
            lines.append(f"// Function call: {op.line}")
            lines.append(f"{func_name}({', '.join(converted_args)});")
            lines.append("")
        return lines
    
    def _convert_set_property(self, op: GroovyOperation) -> List[str]:
        """Convert property set to JavaScript"""
        lines = []
        if op.target and op.value:
            # Handle dynamic property names
            if "${" in op.target:
                prop_var = re.search(r'\${(.+?)}', op.target).group(1)
                lines.append(f"const propName = pm.environment.get('{prop_var}');")
                lines.append(f"pm.environment.set(propName, '{op.value}');")
            else:
                lines.append(f"pm.environment.set('{op.target}', '{op.value}');")
        lines.append("")
        return lines
    
    def _convert_set_header(self, op: GroovyOperation) -> List[str]:
        """Convert header setting to JavaScript"""
        lines = []
        if op.target and op.value:
            # Handle dynamic header values
            if "${" in op.value:
                header_var = re.search(r'\${(.+?)}', op.value).group(1)
                lines.append(f"const headerValue = pm.environment.get('{header_var}');")
                lines.append(f"pm.request.headers.add({{key: '{op.target}', value: headerValue}});")
            else:
                lines.append(f"pm.request.headers.add({{key: '{op.target}', value: '{op.value}'}});")
        lines.append("")
        return lines
    
    def _convert_set_endpoint(self, op: GroovyOperation) -> List[str]:
        """Convert endpoint setting to JavaScript"""
        lines = [
            "const endpoint = pm.environment.get('baseUrl');",
            "if (!endpoint) {",
            "    console.error('baseUrl environment variable not set');",
            "    return;",
            "}",
            "pm.request.url = endpoint;",
            "console.log(`Setting endpoint to ${endpoint}`);",
            ""
        ]
        return lines
    
    def _convert_assertion(self, op: GroovyOperation) -> List[str]:
        """Convert assertion to JavaScript"""
        lines = [
            "pm.test('Assertion', function() {",
            f"    // Original assertion: {op.line}",
            "    try {",
            "        const assertionResult = eval(pm.environment.get('assertionExpression'));",
            "        pm.expect(assertionResult).to.be.true;",
            "    } catch (error) {",
            "        console.error('Assertion failed:', error);",
            "        pm.expect(false).to.be.true;",
            "    }",
            "});",
            ""
        ]
        return lines

def convert_groovy_script(groovy_script: str, script_type: str = "prerequest") -> str:
    """
    Convert a Groovy script to JavaScript
    """
    converter = GroovyScriptConverter()
    return converter.convert(groovy_script, script_type)

def create_script_step(name: str, script_type: str, script_content: str = None) -> Dict[str, Any]:
    """
    Create a Postman script step from a Groovy script
    """
    if script_content is None:
        script_content = ""
    
    # Convert Groovy to JavaScript
    js_script = convert_groovy_script(script_content, script_type)
    
    # Create the step
    step = {
        "name": name,
        "event": [{
            "listen": script_type,
            "script": {
                "type": "text/javascript",
                "exec": js_script.split("\n")
            }
        }],
        "request": {
            "method": "GET",
            "header": [],
            "url": {
                "raw": "{{baseUrl}}",
                "host": ["{{baseUrl}}"],
                "path": [""]
            }
        }
    }
    
    return step 