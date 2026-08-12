from typing import Dict, List, Optional
from app.graph.state import WorkflowState
from app.nodes.customer import CustomerNode
from app.nodes.switching_triggers import SwitchingTriggersNode
from app.nodes.early_adopters import EarlyAdoptersNode
from app.nodes.alternatives import AlternativesNode
from app.nodes.problems import ProblemsNode
from app.nodes.solution import SolutionNode
from app.services.search import SearchService, get_search_service
from app.nodes.base import BaseNode
import logging
from fastapi import Depends

logger = logging.getLogger("startup-stress-test-agent.graph")

class WorkflowGraph:
    def __init__(self, search_service: SearchService):
        # instantiate nodes with shared search service
        self.search_service = search_service
        self.nodes_order: List[BaseNode] = [
            CustomerNode(search_service=search_service),
            SwitchingTriggersNode(search_service=search_service),
            EarlyAdoptersNode(search_service=search_service),
            AlternativesNode(search_service=search_service),
            ProblemsNode(search_service=search_service),
            SolutionNode(search_service=search_service),
        ]
        # map node name to index
        self.name_to_index = {n.name: i for i, n in enumerate(self.nodes_order)}

    async def run_full(self, idea: str) -> WorkflowState:
        state = WorkflowState(idea=idea)
        logger.info("Running full workflow for idea: %s", idea)
        for node in self.nodes_order:
            logger.info("Running node: %s", node.name)
            result = await node.execute(state)
            # node.execute is responsible for updating state.messages and state.* fields
        return state

    async def refine_and_rerun(self, workflow_state: Dict, action: Dict, search_service: SearchService = Depends(get_search_service)) -> WorkflowState:
        """
        action can be:
          {"refine": "<node_name>", "payload": {...}}  -> apply founder edits to the state then rerun downstream
          {"rerun": "<node_name>"} -> rerun node and downstream
        """
        state = WorkflowState.parse_obj(workflow_state)
        # apply feedback/refine if present
        if "refine" in action:
            node_name = action["refine"]
            payload = action.get("payload", {})
            # apply to state directly
            setattr(state, node_name, payload)
            state.founder_feedback[node_name] = payload

            start_index = self.name_to_index.get(node_name, 0)
        elif "rerun" in action:
            node_name = action["rerun"]
            start_index = self.name_to_index.get(node_name, 0)
        else:
            raise ValueError("Unknown action for refine endpoint")

        # run nodes from start_index onward
        for node in self.nodes_order[start_index:]:
            logger.info("Re-running node: %s", node.name)
            await node.execute(state)

        return state

# Dependency to provide a graph instance
def get_graph(search_service: SearchService = Depends(get_search_service)) -> WorkflowGraph:
    return WorkflowGraph(search_service=search_service)
