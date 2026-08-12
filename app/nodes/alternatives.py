from typing import Dict, Any
from app.nodes.base import BaseNode
from app.models.outputs import AlternativesOutput
from app.services.search import SearchService
from app.services.model import ModelClient

PROMPT = """Idea: {context[idea]}
Evidence: {evidence}
Question: What existing alternatives do they use? For each alternative, return category, strengths, weaknesses.
Return JSON:
{"alternatives":[{"alternative":"...","category":"...","strengths":["..."],"weaknesses":["..."],"evidence":[{"text":"...","url":"..."}]}], "confidence":0.0-1.0}
"""

REFLECTION_PROMPT = """
Return JSON: {"approved": true/false, "retry": true/false, "reason":"...", "confidence":0.0-1.0}
"""

class AlternativesNode(BaseNode):
    name = "alternatives"
    prompt_template = PROMPT
    reflection_prompt_template = REFLECTION_PROMPT
    output_model = AlternativesOutput

    def __init__(self, search_service: SearchService, model_client: ModelClient):
        super().__init__(search_service, model_client)

    def _make_search_query(self, context: Dict[str, Any]) -> str:
        return f"{context['idea']} competitors alternatives 'vs' 'review' 'comparison'"

    def _save_to_state(self, state: Any, validated: Any, evidence: Any, reflection: Any) -> None:
        state.alternatives = validated.dict()
        self._append_message(state, {"node": self.name, "output": validated.dict(), "evidence": evidence, "reflection": reflection.dict()})
