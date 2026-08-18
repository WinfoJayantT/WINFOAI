from app.schemas.intent import IntentRequest
from app.services.intent_router_service import intent_router_service

test_cases = [
    # 1. Natural language step generation
    ('How do I add a new supplier with their office address and payment method?', 'generate_script_steps'),
    ('Walk me through entering a new customer sales order and booking it', 'generate_script_steps'),
    ('Give me the steps to create and submit a supplier invoice in Accounts Payable', 'generate_script_steps'),
    # 2. Technical QA step generation
    ('Generate test steps for creating a supplier in Oracle', 'generate_script_steps'),
    # 3. Search
    ('Find test scripts for supplier invoice payment', 'semantic_search_tests'),
    # 4. Lookup
    ('Explain script PRC.P2P.PO.22', 'filtered_script_lookup'),
    # 5. Failure Analysis vs Locator repair
    ('Why did this test fail with TimeoutError: locator.click', 'analyze_entity'),
    ('Suggest locator fixes for failing script PRC.P2P with broken locator', 'recommend_locator_fixes'),
    # 6. Test Suite & Risk & Clustering
    ('Generate an end to end test suite for procure to pay', 'generate_test_suite'),
    ('Which tests are most likely to fail and flaky', 'assess_test_risk'),
    ('Group test scripts by process area', 'semantic_cluster_scripts'),
    # 7. Execution
    ('Run the test scripts now', 'execute_script_set'),
]

print('=== EXECUTING INTENT ROUTER VERIFICATION BENCHMARK ===')
all_passed = True
for query, expected_tool in test_cases:
    req = IntentRequest(user_query=query)
    res = intent_router_service.route(req)
    actual_tool = res.primary_intent.tool
    conf = res.primary_intent.confidence
    passed = actual_tool == expected_tool
    if not passed:
        all_passed = False
    status = 'PASS' if passed else 'FAIL'
    print(f'[{status}] Expected: {expected_tool:25} | Got: {actual_tool:25} | Conf: {conf:.2f} | Query: "{query[:45]}..."')

print(f'\nOVERALL BENCHMARK RESULT: {"ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"}')
