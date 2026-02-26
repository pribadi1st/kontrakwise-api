import shutil
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile
from app.migrations.documents import Document as DocumentModel
from pathlib import Path
import pymupdf

from app.core.db import get_db
from app.core.gemini_client import gemAI
from app.core.pinecone_client import pinecone_client
from app.models.documents import DocumentResponse, DocumentDetailResponse
from app.models.document_types import DocumentTypeRelationResponse
from sqlalchemy import select
from fastapi import HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from app.services.document_type_service import DocumentTypeService


class DocumentService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.upload_path = Path("./storage")

    def get_documents(self, user_id: int, skip: int = 0, limit: int = 100):
        from sqlalchemy.orm import joinedload
        stmt = select(DocumentModel).options(
            joinedload(DocumentModel.document_type)
        ).filter(
            DocumentModel.user_id == user_id
        ).limit(limit).offset(skip)
        result = self.db.execute(stmt).scalars().all()
        return [DocumentResponse(
            id=doc.id, 
            filename=doc.filename, 
            created_at=doc.created_at,
            ai_progress= doc.ai_progress,
            summary=doc.summary,
            document_type=DocumentTypeRelationResponse(
                id=doc.document_type.id,
                name=doc.document_type.name,
            ) if doc.document_type else None
        ) for doc in result]

    def get_document_detail(self, user_id: int, document_id: int):
        doc = self.db.query(DocumentModel).filter(
            DocumentModel.user_id == user_id,
            DocumentModel.id == document_id
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        resp = DocumentDetailResponse(
            id=doc.id,
            filename=doc.filename,
            created_at=doc.created_at,
            ai_progress=doc.ai_progress,
            summary=doc.summary,
            file_path=doc.file_path,
        )
        return resp

    async def upload_document(self, user_id: int, file: UploadFile, filename: str, document_type_id: int):
        document_type_service = DocumentTypeService(self.db)
        document_type = document_type_service.get_single_type(user_id, document_type_id)
        if not document_type:
            raise HTTPException(status_code=404, detail="Document type not found")

        db_document = DocumentModel(
            user_id=user_id, 
            filename=filename, 
            file_path="temp", # Placeholder,
            document_type_id=document_type_id
        )
        self.db.add(db_document)
        self.db.flush()
        new_id = db_document.id
        doc_path = self.upload_path / str(user_id)
        doc_path.mkdir(parents=True, exist_ok=True)
        path = doc_path / f"{new_id}_{filename}.{file.filename.split('.')[-1]}"
        try:
            with path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            file.file.close()
        db_document.file_path = str(path)
        self.db.commit()
        self.db.refresh(db_document)
        # will upload it manually
        # await self.upload_to_pinecone(str(path), db_document.id, user_id)
        return db_document
    
    async def upload_to_pinecone(self, path: str, document_id: int, user_id: int):
        try:
            doc = pymupdf.open(path)
            namespace = f"user_{user_id}"
            
            raw_documents = []
            need_llm = False
            for page in doc:
                # Create a tiny object for each page that knows its page number
                page_text = page.get_text()
                if len(page_text.strip()) == 0:
                    need_llm = True
                    break
                
                if page_text.strip():
                    raw_documents.append(
                        LCDocument(
                            page_content=page_text,
                            metadata={"page": page.number + 1}
                        )
                    )
            
            if need_llm:
                prompt = """
                    Transcribe this legal document page by page.
                    Return a JSON array where each item represents one page in order.
                    Format: ["Page 1 content here", "Page 2 content here", "Page 3 content here"]
                    Only return the page content, no additional text or explanations.
                """
                try:
                    response = await gemAI.generate_context_with_file(path, prompt)
                    print("LLM Response:", response)
                    
                    # Parse the LLM response and create documents
                    if response and response.strip():
                        try:
                            # Clean response and try to parse as JSON array
                            import json
                            cleaned_response = response.strip()
                            
                            # Remove markdown code blocks if present
                            if cleaned_response.startswith('```json'):
                                cleaned_response = cleaned_response[7:]  # Remove ```json
                            if cleaned_response.startswith('```'):
                                cleaned_response = cleaned_response[3:]   # Remove ```
                            if cleaned_response.endswith('```'):
                                cleaned_response = cleaned_response[:-3]  # Remove ```
                            
                            cleaned_response = cleaned_response.strip()
                            print(f"Cleaned response: {cleaned_response[:100]}...")
                            pages = json.loads(cleaned_response)
                            print(f"Parsed {len(pages)} pages from LLM response")
                            
                            for i, page_content in enumerate(pages):
                                if page_content and page_content.strip():
                                    raw_documents.append(
                                        LCDocument(
                                            page_content=page_content.strip(),
                                            metadata={"page": i + 1}
                                        )
                                    )
                        except json.JSONDecodeError as e:
                            # Fallback: treat as plain text split by pages
                            print(f"JSON parsing failed: {e}")
                            print("LLM response is not JSON, treating as plain text")
                            pages = response.split('\n\n')  # Split by double newlines
                            for i, page_content in enumerate(pages):
                                if page_content.strip():
                                    raw_documents.append(
                                        LCDocument(
                                            page_content=page_content.strip(),
                                            metadata={"page": i + 1}
                                        )
                                    )
                        print(f"Created {len(raw_documents)} documents from LLM response")
                    else:
                        print("LLM returned empty response")
                except Exception as e:
                    print(f"ERROR: LLM transcription failed: {e}")
                    print("Falling back to basic text extraction...")
                    
                    # Fallback: Try to extract any text at all
                    try:
                        all_text = "\n".join([page.get_text() for page in doc])
                        if all_text.strip():
                            raw_documents.append(
                                LCDocument(
                                    page_content=all_text.strip(),
                                    metadata={"page": 1}
                                )
                            )
                    except Exception as fallback_e:
                        print(f"Fallback extraction also failed: {fallback_e}")
                        return
                
                if not raw_documents:
                    print("ERROR: Could not extract any content from PDF")
                    return
            
            # 2. Smart Chunking (this will now preserve metadata!)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # Reduced chunk size
                chunk_overlap=100,  # Reduced overlap
                separators=["\n\n", "\n", ". ", " "]  # More flexible separators
            )
            
            # .split_documents is smarter than .split_text
            # If a chunk comes from Page 1, it keeps {"page": 1} in its metadata
            chunks = text_splitter.split_documents(raw_documents)
            
            print(f"DEBUG: Generated {len(chunks)} chunks from {len(raw_documents)} documents")
            
            if not chunks:
                print("ERROR: No chunks generated from document!")
                # Try fallback: simple text splitting
                all_text = "\n".join([doc.page_content for doc in raw_documents])
                if all_text.strip():
                    print("DEBUG: Using fallback text splitting method")
                    chunks = text_splitter.split_text(all_text)
                else:
                    print("ERROR: Document has no extractable text content!")
                    return
            
            # 2. Prepare Vectors in a List (Batching)
            vectors_to_upsert = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Ensure chunk has content
                    if not chunk.page_content or not chunk.page_content.strip():
                        print(f"WARNING: Skipping empty chunk {i}")
                        continue
                    
                    embedding = gemAI.create_embedding(chunk.page_content)
                    vectors_to_upsert.append({
                        "id": f"doc_{document_id}_chunk_{i}",
                        "values": embedding,
                        "metadata": {
                            "document_id": document_id,
                            "user_id": user_id,
                            "text": chunk.page_content, # The actual text
                            "page": chunk.metadata.get("page", 0), # Safe access with fallback
                            "chunk_index": i
                        }
                    })
                except Exception as e:
                    print(f"ERROR: Failed to create embedding for chunk {i}: {e}")
                    continue
            
            print(f"DEBUG: Prepared {len(vectors_to_upsert)} vectors for upsert")
            
            if not vectors_to_upsert:
                print("ERROR: No vectors prepared for upsert!")
                return
            
            # 3. Batch Upload to Handle 2MB Size Limit
            # Pinecone max request size is 2MB, so we need to batch
            batch_size = 50  # Conservative batch size to stay under 2MB
            total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
            
            print(f"DEBUG: Uploading {len(vectors_to_upsert)} vectors in {total_batches} batches of {batch_size}")
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                print(f"DEBUG: Uploading batch {batch_num}/{total_batches} with {len(batch)} vectors")
                
                try:
                    result = pinecone_client.upsert_vectors(batch, namespace=namespace)
                    print(f"DEBUG: Batch {batch_num} upsert result: {result}")
                except Exception as batch_error:
                    print(f"ERROR: Batch {batch_num} failed: {batch_error}")
                    raise Exception(f"Failed to upload batch {batch_num}: {str(batch_error)}")
            
            print(f"DEBUG: All {total_batches} batches uploaded successfully")
            
        except Exception as e:
            print(f"ERROR in upload_to_pinecone: {e}")
            raise
    
    def delete_document(self, user_id: int, document_id: int):
        doc = self.db.query(DocumentModel).filter(
            DocumentModel.user_id == user_id,
            DocumentModel.id == document_id
        ).first()
        doc_path = doc.file_path
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        self.db.delete(doc)
        self.db.commit()
        
        # Delete from Pinecone
        pinecone_client.delete_vectors(f"user_{user_id}", {"document_id": document_id})

        # Delete file
        import os
        os.remove(doc_path)
        
        return {"detail": "success"}