from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.ai_analysis import AIAnalysisDTO, AIListRules, AIAnalysisResult
from app.core.gemini_client import gemAI
from app.services.documents_service import DocumentService
from app.utils.prompt import get_analysis_prompt
from app.migrations.documents import Document as DocumentDataModel
import json

class AIAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.documents_service = DocumentService(db)

    async def analyze_document(self, user_id: int, analysis_dto: AIAnalysisDTO, document: DocumentDataModel=None) -> dict:
        """Analyze a document using AI"""
        try:
            # Verify document exists
            print(document.id)
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")
            prompt = get_analysis_prompt(analysis_dto)
            response = await gemAI.generate_context_with_file(document.file_path, prompt, AIAnalysisResult)
            return json.loads(response)
            
        except Exception as e:
            return HTTPException(status_code=503, detail=e)

    async def get_analysis_types(self) -> List[dict]:
        """Get available analysis types"""
        return [
            {"id": "contract_analysis", "name": "Contract Analysis"},
            {"id": "risk_assessment", "name": "Risk Assessment"},
            {"id": "compliance_check", "name": "Compliance Check"},
            {"id": "financial_analysis", "name": "Financial Analysis"},
            {"id": "legal_review", "name": "Legal Review"}
        ]

    async def get_analysis_rules(self) -> List[AIListRules]:
        """Get available analysis rules"""
        return [
            AIListRules(
                rules="liability_clause",
                description="Check liability limitations and caps"
            ),
            AIListRules(
                rules="termination_terms",
                description="Analyze termination conditions and notice periods"
            ),
            AIListRules(
                rules="payment_structure",
                description="Review payment terms and schedules"
            ),
            AIListRules(
                rules="confidentiality",
                description="Examine confidentiality and data protection clauses"
            ),
            AIListRules(
                rules="jurisdiction",
                description="Identify governing law and jurisdiction"
            ),
            AIListRules(
                rules="force_majeure",
                description="Check force majeure provisions"
            ),
            AIListRules(
                rules="indemnification",
                description="Analyze indemnification clauses"
            ),
            AIListRules(
                rules="intellectual_property",
                description="Review IP ownership and licensing terms"
            )
        ]