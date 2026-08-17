from app.schemas.intent import IntentName, IntentRequest


def test_route_without_llm_returns_unknown_not_a_keyword_guess(monkeypatch):
    import app.services.intent_router_service as mod

    monkeypatch.setattr(mod.settings, "LLM_API_KEY", "")
    result = mod.intent_router_service.route(IntentRequest(user_query="explain FIN.P2P.AP.0001"))

    # Guardrail: no keyword-based fallback routing (section 9). Must be UNKNOWN,
    # not a guessed explain_script intent, when the LLM isn't configured.
    assert result.intent == IntentName.UNKNOWN
    assert result.tool == "unknown"
