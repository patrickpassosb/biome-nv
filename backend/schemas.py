from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str


class LogSet(BaseModel):
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    machine_level: Optional[int] = None
    rpe: Optional[float] = None
    notes: Optional[str] = None
    is_warmup: int = 0


class LogExercise(BaseModel):
    exercise_name: str
    side: Optional[str] = None
    sets: List[LogSet]


class LogWorkout(BaseModel):
    date: str
    workout_type: str
    exercises: List[LogExercise]


class ProfileCreate(BaseModel):
    name: str
    fitness_goal: Optional[str] = None
    goals_json: Optional[Dict[str, Any]] = None


class Profile(BaseModel):
    id: str
    name: str
    fitness_goal: Optional[str] = None
    goals_json: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
