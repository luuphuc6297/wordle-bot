"""FastAPI application for Wordle Bot."""

from typing import Any, Dict, Optional

# Import from workspace packages
from core.algorithms.orchestrator import Orchestrator
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from shared.config.settings import settings

app = FastAPI(
    title="Wordle Bot API",
    description="API service for autonomous Wordle solving",
    version="1.0.0",
)


class SolveRequest(BaseModel):
    """Request model for solving puzzle."""

    time_budget: Optional[float] = None


class SimulateRequest(BaseModel):
    """Request model for simulating game."""

    target: str
    time_budget: Optional[float] = None


class AnalyzeRequest(BaseModel):
    """Request model for analyzing word."""

    word: str
    possible_answers: Optional[list[str]] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Wordle Bot API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/solve")
async def solve_daily_puzzle(request: SolveRequest) -> Dict[str, Any]:
    """Solve the daily Wordle puzzle."""
    try:
        time_budget = request.time_budget or settings.SOLVER_TIME_BUDGET_SECONDS

        orchestrator = Orchestrator(
            api_base_url=settings.WORDLE_API_BASE_URL,
            solver_time_budget=time_budget,
            show_rich_display=False,
            show_detailed=False,
        )

        result = orchestrator.solve_daily_puzzle()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate")
async def simulate_game(request: SimulateRequest) -> Dict[str, Any]:
    """Simulate solving a game with known target."""
    try:
        if len(request.target) != 5:
            raise HTTPException(status_code=400, detail="Target must be 5 letters")

        time_budget = request.time_budget or settings.SOLVER_TIME_BUDGET_SECONDS

        orchestrator = Orchestrator(
            solver_time_budget=time_budget,
            show_rich_display=False,
            show_detailed=False,
        )

        result = orchestrator.simulate_game(request.target.upper())
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_word(request: AnalyzeRequest) -> Dict[str, Any]:
    """Analyze the entropy of a specific word."""
    try:
        if len(request.word) != 5:
            raise HTTPException(status_code=400, detail="Word must be 5 letters")

        orchestrator = Orchestrator(
            show_rich_display=False,
            show_detailed=False,
        )

        result = orchestrator.analyze_guess(
            request.word.upper(), request.possible_answers
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
