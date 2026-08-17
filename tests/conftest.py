import pytest


@pytest.fixture
def sample_script():
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "test_script_number": "FIN.P2P.AP.0001",
        "qualified_name": "FIN.P2P.AP.0001",
        "script_name": "Create Standard Supplier Invoice",
        "description": "Validates creation of a standard AP invoice.",
        "module": "Accounts Payable (AP)",
        "process": "Procure to Pay (P2P)",
        "process_area": "Financials",
        "role": "Accounts Payable Specialist",
    }


@pytest.fixture
def sample_steps():
    return [
        {"step_no": 1, "step_action": "Navigate", "step_description": "Open Create Invoice",
         "input_parameter": "", "default_value": ""},
        {"step_no": 2, "step_action": "Enter", "step_description": "Enter supplier name",
         "input_parameter": "supplier_name", "default_value": "Acme Corp"},
    ]
