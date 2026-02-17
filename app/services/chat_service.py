from app.core.gemini_client import gemAI
from app.core.pinecone_client import pinecone_client
from app.services.documents_service import DocumentService
from app.models.chat import ChatRequest

class ChatService():
    def __init__(self, db):
        self.db = db
        self.gemAI = gemAI
        self.pinecone_client = pinecone_client
        pass

    def generate_response_for_single_doc(self, user_id: int, request: ChatRequest):
        document_service = DocumentService(self.db)
        document_service.get_document_detail(user_id, request.document_id)
        
        query_vector = self.gemAI.create_embedding(request.query)
        
        metadata_filter = {
            "document_id": request.document_id,
        }
        namespace_pin = f"user_{user_id}"

        search_results = self.pinecone_client.query_vectors(
            query_vector=query_vector,
            filter_dict=metadata_filter,
            namespace=namespace_pin
        )
        
        context_parts = []
        # citations = []
        
        for res in search_results.matches:
            content = res.metadata.get("text", "")
            page = res.metadata.get("page", "?")
            context_parts.append(f"[Source: Page {page}]\n{content}")
            # citations.append({
            #     "page": page,
            #     "text": content,
            #     "relevance_score": res.score
            # })

        context_text = "\n\n".join(context_parts)

        # 5. Build the Prompt for Gemini
        prompt = f"""
        You are the Kontrakwise AI. Use the provided context to answer the question.

        REASONING INSTRUCTIONS:
        1. If the user asks about something NOT mentioned (like gym memberships or lunch money), 
        explicitly state: "The contract is silent on this matter."
        2. If the user asks for a calculation (like a notice period), find the relevant 
        clause and apply it to their situation.
        3. If the user asks for legal advice, clarify that you are an AI assistant to help analyze the document, not a lawyer.

        STRICT RULES:
        1. Base your answer ONLY on the context.
        2. If the user asks a question that cannot be answered using the provided CONTEXT (e.g., general knowledge, politics, or other documents), you must politely decline to answer.
        3. Say: "I'm sorry, but I can only answer questions based on the provided legal document. I don't have information regarding [User's Topic]."
        4. For every source used, identify the EXACT sentence or short paragraph that contains the evidence. If consecutive sentences are relevant, group them into a single citation.
        5. Return your response in this EXACT format:
        
        ANSWER: [Your professional legal answer here]
        ---
        EVIDENCE:
        - Page [Number]: "[Exact sentence from text]"
        - Page [Number]: "[Exact sentence from text]"

        CONTEXT:
        {context_text}

        QUESTION: 
        {request.query}
        """

        # 6. Generate content using Gemini
        try:
            response = self.gemAI.generate_content(prompt)
            
            # Parse the response to extract answer and evidence
            parts = response.split("---")
            answer_text = parts[0].replace("ANSWER:", "").strip()
            evidence_text = parts[1].replace("EVIDENCE:", "").strip()
            
            # Parse evidence into individual citations
            citation_array = []
            if evidence_text.strip():
                # Split by lines and parse each citation
                evidence_lines = [line.strip() for line in evidence_text.split('\n') if line.strip()]
                for line in evidence_lines:
                    if line.startswith('- Page'):
                        # Extract page number and quote
                        page_match = line.split('Page')[1].split(':')[0].strip()
                        quote_start = line.find('"') + 1
                        quote_end = line.rfind('"')
                        quote = line[quote_start:quote_end] if quote_start > 0 and quote_end > quote_start else ""
                        
                        citation_array.append({
                            "page": page_match,
                            "text": quote
                        })

            return {
                "answer": answer_text,
                "citations": citation_array
            }
        except Exception as e:
            raise Exception(f"Failed to generate AI response: {str(e)}")
        
