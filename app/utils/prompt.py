from app.models.ai_analysis import AIAnalysisDTO


def get_document_prompt(context: str, question: str):
    return """
        You are Kontrakwise AI. Use the provided context to answer the question.

        REASONING INSTRUCTIONS:
        1. If the user asks about something NOT mentioned (like gym memberships or lunch money), 
        explicitly state: "The contract is silent on this matter." in their language
        2. If the user asks for a calculation (like a notice period), find the relevant 
        clause and apply it to their situation.
        3. If the user asks for legal advice, clarify that you are an AI assistant to help analyze the document, not a lawyer.

        STRICT RULES:
        1. Base your answer ONLY on the context.
        2. If the user asks a question that cannot be answered using the provided CONTEXT (e.g., general knowledge, politics, or other documents), you must politely decline to answer.
        3. Say: "I'm sorry, but I can only answer questions based on the provided legal document. I don't have information regarding [User's Topic]."
        4. For every source used, identify the EXACT sentence or short paragraph that contains the evidence. If consecutive sentences are relevant, group them into a single citation.
        5. Citations are OPTIONAL - only include them if the question requires specific evidence from the document. If the question is general or doesn't need specific citations, you can omit the EVIDENCE section entirely.

        RESPONSE FORMAT:
        If citations are needed:
        
        ANSWER: [Your professional legal answer here]
        ---
        EVIDENCE:
        - Page [Number]: "[Exact sentence from text]"
        - Page [Number]: "[Exact sentence from text]"

        If no citations are needed:
        
        ANSWER: [Your professional legal answer here]

        CONTEXT:
        {context}

        QUESTION: 
        {question}
        """.format(context=context, question=question)

def get_summarization_prompt(document_type_name: str, document_type_description: str, list_of_rules: list[dict]):
    # 1. Format the rules list
    formatted_rules_list = "\n".join([
        f"- Rule: {r['clause']} - {r['criteria']} (Severity: {r['severity']})"
        for r in list_of_rules
    ])

    # 2. Use a raw string or clean indentation
    # Use double {{ }} for the JSON structure so .format() ignores them
    prompt_template = """
        Act as a Senior Legal Auditor and Risk Management Expert. Your task is to analyze the provided legal document based on a set of predefined rules and determine the overall risk profile.

        ### DOCUMENT CONTEXT:
        - Document Category: {doc_type}
        - Category Description: {doc_desc}

        ### OBJECTIVES:
        1. SUMMARY: Provide a concise executive summary of the document.
        2. RISK LEVEL: Assign an overall risk level (HIGH, MEDIUM, or LOW).
        3. REASONING: Explain the logic behind the assigned risk level.

        ### ANALYSIS RULES:
        The following rules must be used to evaluate the document:
        {rules_list}

        ### RISK LEVEL CRITERIA:
        - HIGH: Assigned if at least one "HIGH" severity rule is violated, or if there are clauses that significantly jeopardize the legal/financial position.
        - MEDIUM: Assigned if "MEDIUM" severity rules are triggered, or if there is significant ambiguity.
        - LOW: Assigned if the document follows all rules with no significant impact.

        ### DOCUMENT TEXT TO ANALYZE:
        """

    # 3. Format the prompt
    final_prompt = prompt_template.format(
        doc_type=document_type_name,
        doc_desc=document_type_description,
        rules_list=formatted_rules_list
    )
    
    return final_prompt

def get_analysis_prompt(analysis_dto: AIAnalysisDTO):
    # 1. Format Rules dengan lebih ketat
    formatted_rules = "\n".join([
        f"- [RULE: {r.rules}]: {r.description}" 
        for r in analysis_dto.ai_rules
    ])

    # 2. Gunakan Persona agar tidak kena "Legal Advice Filter"
    # Kita sebut AI sebagai "Document Auditor" bukan "Legal Advisor"
    base_prompt = f"""
    Role: You are a Professional Document Auditor (Kontrakwise AI).
    Task: Extract data and identify inconsistencies based on specific rules.
    Document Type Context: {analysis_dto.analysis_type}

    ## Operational Rules:
    {formatted_rules}
    
    ## User Instructions:
    {analysis_dto.custom_prompt or "Perform a standard audit."}

    ## Critical Instructions:
    1. Base your analysis ONLY on the provided text.
    2. If a rule is violated or a risk is found, quote the specific sentence/section.
    3. Categorize severity as High (Financial loss/Legal void), Medium (Operational burden), or Low (Info).
    """

    # 3. Paksa Output JSON Murni (Tanpa Markdown)
    # Ini sangat penting untuk integrasi Frontend/React Flow
    base_prompt += """
    ## Output Format (Strict JSON):
    Return ONLY a JSON object with this structure:
    {
      "executive_summary": "string",
      "findings": [
        {
          "rule_name": "string",
          "evidence": "quote from document",
          "risk_level": "High/Medium/Low",
          "explanation": "string",
          "mitigation": "string"
        }
      ],
      "overall_risk_score": 1-10
    }
    """
    
    return base_prompt.strip()
    