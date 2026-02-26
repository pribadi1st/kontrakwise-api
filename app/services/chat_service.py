import json
from app.core.gemini_client import gemAI
from app.core.pinecone_client import pinecone_client
from app.services.documents_service import DocumentService
from app.models.chat import ChatRequest
from app.utils.prompt import get_document_prompt

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
        prompt = get_document_prompt(context_text, request.query)

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
    
    def generate_response_for_single_doc_stream(self, user_id: int, request: ChatRequest):
        """Generate streaming response for single document query"""
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
        
        for res in search_results.matches:
            content = res.metadata.get("text", "")
            page = res.metadata.get("page", "?")
            context_parts.append(f"[Source: Page {page}]\n{content}")

        context_text = "\n\n".join(context_parts)

        prompt = get_document_prompt(context_text, request.query)
        print(prompt)
        try:
            # Send initial event to indicate streaming started
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting response generation'})}\n\n"
            
            full_response = ""
            
            # Stream the content generation
            for chunk in self.gemAI.generate_content_stream(prompt):
                if chunk:
                    full_response += chunk
                    # Send each chunk as SSE
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Parse the complete response to extract answer and evidence
            parts = full_response.split("---")
            answer_text = parts[0].replace("ANSWER:", "").strip()
            
            # Parse evidence if available
            citation_array = []
            if len(parts) > 1:
                evidence_text = parts[1].replace("EVIDENCE:", "").strip()
                if evidence_text.strip():
                    evidence_lines = [line.strip() for line in evidence_text.split('\n') if line.strip()]
                    for line in evidence_lines:
                        if line.startswith('- Page'):
                            page_match = line.split('Page')[1].split(':')[0].strip()
                            quote_start = line.find('"') + 1
                            quote_end = line.rfind('"')
                            quote = line[quote_start:quote_end] if quote_start > 0 and quote_end > quote_start else ""
                            
                            citation_array.append({
                                "page": page_match,
                                "text": quote
                            })
            
            # Send final event with complete structured response
            final_data = {
                'type': 'complete',
                'answer': answer_text,
                'citations': citation_array
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f"Failed to generate AI response: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        
