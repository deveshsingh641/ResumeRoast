"""
Pydantic models for roast results and database records.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScoreBand(str, Enum):
    WEAK = "weak"
    MID = "mid"
    STRONG = "strong"


class IssueCategory(str, Enum):
    BUZZWORD = "buzzword"
    NO_METRICS = "no-metrics"
    FORMATTING = "formatting"
    LENGTH = "length"
    IRRELEVANT = "irrelevant"
    TYPO = "typo"
    OTHER = "other"


class Issue(BaseModel):
    quoted_text: str = Field(description="Exact substring from the resume")
    category: IssueCategory
    roast: str = Field(description="Short witty callout, under 20 words")
    fix: str = Field(description="Concrete rewritten version or specific instruction")
    start_offset: Optional[int] = Field(
        default=None, description="Character offset of quoted_text start in extracted text"
    )
    end_offset: Optional[int] = Field(
        default=None, description="Character offset of quoted_text end in extracted text"
    )
    severity_rank: Optional[int] = Field(
        default=None, description="1-based severity rank (1 = most severe)"
    )


class RoastResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    band: ScoreBand
    one_line_verdict: str = Field(description="The roast headline, under 12 words")
    issues: list[Issue]
    strengths: list[str]


class RoastRecord(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    device_fingerprint: Optional[str] = None
    overall_score: int
    band: ScoreBand
    one_line_verdict: str
    issues: list[Issue]
    strengths: list[str]
    created_at: str
    expires_at: Optional[str] = None


class UsageInfo(BaseModel):
    remaining: int
    limit: int
    is_pro: bool


class RoastResponse(BaseModel):
    id: str
    overall_score: int
    band: ScoreBand
    one_line_verdict: str
    issues: list[Issue]
    strengths: list[str]
    is_truncated: bool = False  # True if free tier truncated issues to 3
