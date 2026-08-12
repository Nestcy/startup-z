from typing import Dict, Any
from app.nodes.base import BaseNode
from app.models.outputs import CustomerOutput
from app.services.search import SearchService

PROMPT = """Given the startup idea:
{context[idea]}

Use ONLY the evidence provided to answer: Who is the customer?

Evidence (list of snippets with urls): {evidence}

Return JSON only with keys:
{
  "primary_customer": "...",
  "secondary_customer": "... or null",
  "reasoning": "...",
  "evidence": [{"text":"...", "url":"..."}],
  "confidence": 0.0-1.0
}
"""

REFLECTION_PROMPT = """
You evaluated an answer. Given the evidence and the answer (JSON), is the conclusion supported?
Return JSON:
{"approved": true/false, "retry": true/false, "reason":"...", "confidence":0.0-1.0}
"""

class CustomerNode(BaseNode):
    name = "customer"
    prompt_template = PROMPT
    reflection_prompt_template = REFLECTION_PROMPT
    output_model = CustomerOutput

    def __init__(self, search_service: SearchService):
        super().__init__(search_service)

    def _make_search_query(self, context: Dict[str, Any]) -> str:
        return f"{context['idea']} who is the customer target market users use cases"

    def _save_to_state(self, state: Any, validated: Any, evidence: Any, reflection: Any) -> None:
        state.customer = validated.dict()
        self._append_message(state, {
            "node": self.name,
            "output": validated.dict(),
            "evidence": evidence,
            "reflection": reflection.dict()
        })
