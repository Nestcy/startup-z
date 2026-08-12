from typing import Dict, Any
from app.nodes.base import BaseNode
from app.models.outputs import EarlyAdoptersOutput
from app.services.search import SearchService

PROMPT = """Idea: {context[idea]}
Evidence: {evidence}
Question: Who are the early adopters? Why would they adopt first?
Return JSON with:
{"early_adopter_description":"...", "why":"...", "evidence":[{"text":"...","url":"..."}], "confidence":0.0-1.0}
"""

REFLECTION_PROMPT = """
Return JSON: {"approved": true/false, "retry": true/false, "reason":"...", "confidence":0.0-1.0}
"""

class EarlyAdoptersNode(BaseNode):
    name = "early_adopters"
    prompt_template = PROMPT
    reflection_prompt_template = REFLECTION_PROMPT
    output_model = EarlyAdoptersOutput

    def _make_search_query(self, context: Dict[str, Any]) -> str:
        return f"{context['idea']} who would adopt first 'early adopters' 'who benefits'"

    def _save_to_state(self, state: Any, validated: Any, evidence: Any, reflection: Any) -> None:
        state.early_adopters = validated.dict()
        self._append_message(state, {"node": self.name, "output": validated.dict(), "evidence": evidence, "reflection": reflection.dict()})
