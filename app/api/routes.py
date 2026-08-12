from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from app.graph.graph import WorkflowGraph, get_graph
from app.graph.state import WorkflowState
import logging

router = APIRouter()
logger = logging.getLogger("startup-stress-test-agent.api")

class AnalyzeRequest(BaseModel):
    idea: str

class RefineRequest(BaseModel):
    workflow_state: Dict[str, Any]
    action: Dict[str, Any]  # e.g., {"refine": "customer", "payload": {...}} or {"rerun": "problems"}

@router.post("/analyze")
async def analyze(req: AnalyzeRequest, graph: WorkflowGraph = Depends(get_graph)):
    try:
        state = await graph.run_full(req.idea)
        return {"workflow_state": state.dict()}
    except Exception as e:
        logger.exception("Error running analysis")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refine")
async def refine(req: RefineRequest, graph: WorkflowGraph = Depends(get_graph)):
    """
    action examples:
      {"refine": "customer", "payload": {"primary_customer": "..."}}
      {"rerun": "problems"}
    """
    try:
        new_state = await graph.refine_and_rerun(req.workflow_state, req.action)
        return {"workflow_state": new_state.dict()}
    except Exception as e:
        logger.exception("Error in refine endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "ok"}
