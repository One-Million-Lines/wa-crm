from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RadarProject(BaseModel):
    name: str
    description: str
    targetUser: Optional[str] = ""
    coreProblem: Optional[str] = ""
    subreddits: Optional[List[str]] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class Signal(BaseModel):
    projectId: str
    phrase: str
    group: str = "problem"  # problem | alternative | question
    isActive: bool = True
    createdAt: Optional[datetime] = None


class Run(BaseModel):
    projectId: str
    status: str = "pending"  # pending | running | done | failed
    triggeredBy: str = "manual"
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    stats: Optional[dict] = {}


class Opportunity(BaseModel):
    runId: str
    projectId: str
    platform: str = "reddit"
    postId: str
    postTitle: str = ""
    text: str = ""
    author: str = ""
    subreddit: str = ""
    url: str = ""
    score: int = 0
    intentStrength: str = "low"  # low | med | high
    matchedSignals: Optional[List[str]] = []
    reasoning: str = ""
    suggestedAngle: str = ""
    status: str = "pending"  # pending | relevant | ignored | saved | replied
    createdAt: Optional[datetime] = None
