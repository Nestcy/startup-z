from typing import Dict, Any
from app.nodes.base import BaseNode
from app.models.outputs import SolutionOutput
from app.services.search import SearchService
from app.services.model import ModelClient

PROMPT = """Idea: {context[idea]}
Validated problems (only use these):
{evidence}
Generate a hypothesized solution (value proposition, summary, assumptions, risks). Use ONLY validated problems.
Return JSON:
{"value_proposition":"...","solution_summary":"...","assumptions":["..."],"risks":["..."],"confidence":0.0-1.0}
"""

REFLECTION_PROMPT = """
Return JSON: {"approved": true/false, "retry": true/false, "reason":"...", "confidence":0.0-1.0}
"""

class SolutionNode(BaseNode):
    name = "solution"
    prompt_template = PROMPT
    reflection_prompt_template = REFLECTION_PROMPT
    output_model = SolutionOutput

    def __init__(self, search_service: SearchService, model_client: ModelClient):
        super().__init__(search_service, model_client)

    def _make_search_query(self, context: Dict[str, Any]) -> str:
        # rely on validated problems
        return f"{context['idea']} validated problems 'pain points' 'unmet needs'"

    def _save_to_state(self, state: Any, validated: Any, evidence: Any, reflection: Any) -> None:
        state.solution = validated.dict()
        self._append_message(state, {"node": self.name, "output": validated.dict(), "evidence": evidence, "reflection": reflection.dict()})
