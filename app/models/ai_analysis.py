from typing import Optional, List
from pydantic import BaseModel, Field

class AIListRules(BaseModel):
    rules: str
    description: str

class AIAnalysisDTO(BaseModel):
    analysis_type: str
    custom_prompt: Optional[str] = None
    ai_rules: List[AIListRules] = Field(min_length=1, description="At least one rule is required")

class AIAnalysisFinding(BaseModel):
    rule_name: str
    evidence: str
    risk_level: str
    explanation: str
    mitigation: str

class AIAnalysisResult(BaseModel):
    executive_summary: str
    findings: List[AIAnalysisFinding]
    overall_risk_score: int