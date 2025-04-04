from typing import Dict, List, Set
from collections import defaultdict

class ExecutionFlowBuilder:
    def __init__(self):
        self.test_case_graph: Dict[str, List[str]] = defaultdict(list)
        self.function_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.step_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.test_case_operations: Dict[str, List[str]] = defaultdict(list)

    def register_test_case_dependency(self, caller: str, callee: str):
        self.test_case_graph[caller].append(callee)

    def register_function_call(self, caller_func: str, called_func: str):
        self.function_dependencies[caller_func].append(called_func)

    def register_step_dependency(self, current_step: str, depends_on: str):
        self.step_dependencies[current_step].append(depends_on)

    def register_operation_for_test_case(self, test_case: str, op_type: str):
        self.test_case_operations[test_case].append(op_type)

    def get_execution_order(self) -> List[str]:
        visited = set()
        result = []

        def visit(node):
            if node not in visited:
                visited.add(node)
                for dep in self.test_case_graph.get(node, []):
                    visit(dep)
                result.append(node)

        for node in self.test_case_graph:
            visit(node)
        return result[::-1]  # reverse for proper order

    def get_step_order(self, step_name: str) -> List[str]:
        visited = set()
        order = []

        def walk(node):
            if node not in visited:
                visited.add(node)
                for dep in self.step_dependencies.get(node, []):
                    walk(dep)
                order.append(node)

        walk(step_name)
        return order[::-1]

    def get_function_chain(self, func_name: str) -> List[str]:
        visited = set()
        chain = []

        def trace(func):
            if func not in visited:
                visited.add(func)
                for dep in self.function_dependencies.get(func, []):
                    trace(dep)
                chain.append(func)

        trace(func_name)
        return chain[::-1]

    def detect_setup_test_cases(self) -> Set[str]:
        setup_cases = set()
        for test_case, ops in self.test_case_operations.items():
            # Heuristic: setup case if it only sets properties/headers/endpoints
            if all(op in {"set_property", "set_header", "set_endpoint"} for op in ops):
                setup_cases.add(test_case)
        return setup_cases

# Example usage:
if __name__ == "__main__":
    builder = ExecutionFlowBuilder()
    builder.register_test_case_dependency("TC_01", "TC_Setup")
    builder.register_test_case_dependency("TC_02", "TC_Setup")
    builder.register_function_call("SignInAvion", "SetHeader")
    builder.register_function_call("SetHeader", "SetCookie")
    builder.register_operation_for_test_case("TC_Setup", "set_property")
    builder.register_operation_for_test_case("TC_Setup", "set_header")

    print("Test case execution order:", builder.get_execution_order())
    print("Function chain for SignInAvion:", builder.get_function_chain("SignInAvion"))
    print("Setup test cases detected:", builder.detect_setup_test_cases())
