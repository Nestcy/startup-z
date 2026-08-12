from typing import Any, Dict, Optional, Type
from app.services.search import SearchService
from pydantic import BaseModel, ValidationError
import json
import logging
from abc import ABC, abstractmethod
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import os

logger = logging.getLogger("startup-stress-test-agent.nodes")

# Reflection result model (simple typed structure)
class ReflectionResult(BaseModel):
    approved: bool
    retry: bool
    reason: str
    confidence: float

# Base output model for node outputs (nodes will define their own models in models/outputs.py)
class NodeOutputModel(BaseModel):
    pass

class BaseNode(ABC):
    name: str
    prompt_template: str
    reflection_prompt_template: str
    output_model: Type[BaseModel]

    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.model = ChatOpenAI(temperature=0, model_name=os.getenv("OPENAI_MODEL", "gpt-4o"), client=None)  # model name via env
        # If OPENAI_API_KEY not set, ChatOpenAI will error; that's desired
        logger.debug("Initialized node %s", getattr(self, "name", "base"))

    async def execute(self, state: Any) -> Dict[str, Any]:
        """
        The main lifecycle for a node:
          - prepare minimal context
          - search using SearchService
          - call AI with prompt + evidence
          - validate and store output in state
          - run reflection; if reflection disapproves, retry once using refined query
        """
        # 1. minimal context
        context = self._prepare_context(state)
        query = self._make_search_query(context)
        logger.info("[%s] Search query: %s", self.name, query)

        # 2. Search
        evidence = await self.search_service.search(query)
        logger.info("[%s] Retrieved %d evidence items", self.name, len(evidence))

        # 3. Run AI chain
        output = await self._run_ai_with_evidence(context, evidence)
        validated = self._validate_output(output)

        # 4. Reflection
        reflection = await self._reflect(context, evidence, validated)
        if not reflection.approved and reflection.retry:
            # refine query using reflection.reason
            refined_query = f"{query} {reflection.reason}"
            logger.info("[%s] Reflection requested retry. Refined query: %s", self.name, refined_query)
            evidence = await self.search_service.search(refined_query)
            output = await self._run_ai_with_evidence(context, evidence, retry=True)
            validated = self._validate_output(output)
            reflection = await self._reflect(context, evidence, validated)

            if not reflection.approved:
                logger.warning("[%s] Second attempt still unapproved. Saving with low confidence", self.name)

        # 5. Save to workflow state (node is responsible for how it's saved)
        self._save_to_state(state, validated, evidence, reflection)
        return validated

    def _prepare_context(self, state: Any) -> Dict[str, Any]:
        # default minimal context: idea + existing state fields relevant
        return {"idea": state.idea}

    @abstractmethod
    def _make_search_query(self, context: Dict[str, Any]) -> str:
        ...

    async def _run_ai_with_evidence(self, context: Dict[str, Any], evidence: Any, retry: bool = False) -> Dict[str, Any]:
        # Simplest approach: create a system + user message using prompt_template
        system = SystemMessage(content="You are a startup analyst. Reason only from the evidence supplied. Return JSON only.")
        human = HumanMessage(content=self.prompt_template.format(context=context, evidence=json.dumps(evidence)[:4000]))
        logger.debug("[%s] Sending prompt to model", self.name)
        # Call model
        resp = await self.model.apredict(messages=[system, human])
        text = resp.content
        # Ensure JSON parse
        try:
            parsed = json.loads(text)
            return parsed
        except json.JSONDecodeError:
            # attempt to extract JSON blob
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except Exception as e:
                    logger.exception("[%s] Failed to parse JSON from model", self.name)
                    raise
            else:
                logger.error("[%s] Model did not return valid JSON", self.name)
                raise ValueError("Model did not return valid JSON")

    def _validate_output(self, output: Dict[str, Any]) -> BaseModel:
        try:
            return self.output_model.parse_obj(output)
        except ValidationError as e:
            logger.exception("[%s] Output validation failed", self.name)
            # Return as-is in a wrapper or raise based on policy
            raise

    async def _reflect(self, context: Dict[str, Any], evidence: Any, validated_output: BaseModel) -> ReflectionResult:
        system = SystemMessage(content="You are a startup analyst evaluating whether the previous answer was well-supported by evidence. Return JSON only.")
        reflection_prompt = self.reflection_prompt_template.format(context=context, evidence=json.dumps(evidence)[:4000], answer=validated_output.json())
        human = HumanMessage(content=reflection_prompt)
        resp = await self.model.apredict(messages=[system, human])
        try:
            return ReflectionResult.parse_raw(resp.content)
        except Exception:
            # fallback: if model non-conforming, conservatively disapprove
            logger.warning("[%s] Reflection parsing failed, defaulting to disapprove", self.name)
            return ReflectionResult(approved=False, retry=False, reason="Reflection parsing failed", confidence=0.0)

    @abstractmethod
    def _save_to_state(self, state: Any, validated: BaseModel, evidence: Any, reflection: ReflectionResult) -> None:
        ...

    def _append_message(self, state: Any, entry: Dict[str, Any]) -> None:
        state.messages.append(entry)
