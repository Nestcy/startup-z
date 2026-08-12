from typing import Dict, Any
from app.nodes.base import BaseNode
from app.models.outputs import ProblemsOutput
from app.services.search import SearchService

PROMPT = """Idea: {context[idea]}
Evidence: {evidence}
Search for complaints, frustrations, limitations and unmet needs from prioritized sources: Reddit, G2, Product Hunt, App Store reviews, blogs, forums.
Return JSON list of problems with frequency, severity, supporting evidence, and confidence.
Return JSON:
{"problems":[{"problem":"...","frequency":"low|medium|high","severity":"low|medium|high","supporting_evidence":[{"text":"...","url":"..."}]}], "confidence":0.0-1.0}
"""

REFLECTION_PROMPT = """
Return JSON: {"approved": true/false, "retry": true/false, "reason":"...", "confidence":0.0-1.0}
"""

class ProblemsNode(BaseNode):
    name = "problems"
    prompt_template = PROMPT
    reflection_prompt_template = REFLECTION_PROMPT
    output_model = ProblemsOutput

    def _make_search_query(self, context: Dict[str, Any]) -> str:
        # include alternatives in context if available
        alt = ""
        if getattr(context, "alternatives", None):
            alt = " ".join(context["alternatives"])
        return f"{context['idea']} problems complaints limitations 'error' 'frustration' reddit g2 'product hunt' 'app store'"

    def _save_to_state(self, state: Any, validated: Any, evidence: Any, reflection: Any) -> None:
        state.problems = validated.dict()
        self._append_message(state, {"node": self.name, "output": validated.dict(), "evidence": evidence, "reflection": reflection.dict()})
