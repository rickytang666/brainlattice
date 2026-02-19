from mangum import Mangum
from main import app
import json
import os
import asyncio

# pipelines
from services.storage_service import S3StorageService
from services.pdf_service import PDFService
from services.chunking_service import RecursiveMarkdownSplitter
from services.embedding_service import EmbeddingService
from services.job_service import JobService
from db.session import get_db, SessionLocal
from db import models

# 1. api handler
api_handler = Mangum(app)

# 2. worker handler
def worker_handler(event, context):
    """
    processor for async background tasks
    trigger: qstash webhook -> lambda url
    """
    print(f"[WORKER] received event: {json.dumps(event)}")
    
    try:
        # qstash sends body as string in 'body' field for lambda function urls
        # or as raw event if using sqs/sns. assuming http trigger here.
        body = event.get("body")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body or {}
            
        # extract job details
        job_id = payload.get("job_id")
        file_key = payload.get("file_key")
        
        if not job_id or not file_key:
            print("[WORKER] error: missing job_id or file_key")
            return {"statusCode": 400, "body": "missing params"}
            
        print(f"[WORKER] processing job: {job_id} file: {file_key}")
        
        # init services
        storage = S3StorageService()
        pdf_service = PDFService()
        splitter = RecursiveMarkdownSplitter()
        embedder = EmbeddingService()
        jobs = JobService()
        db = SessionLocal()
        
        try:
            # update status: processing
            jobs.update_progress(job_id, "processing", 10)
            
            # 1. download from r2
            print(f"[WORKER] downloading {file_key}...")
            file_bytes = storage.download_file(file_key)
            jobs.update_progress(job_id, "processing", 20)
            
            # 2. save file record to db
            project_id = job_info.get("metadata", {}).get("project_id")
            
            # if no project, create one (demo mode)
            if not project_id:
                new_proj = models.Project(title=f"upload_{job_id[:8]}", status="ready")
                db.add(new_proj)
                db.flush() 
                project_id = new_proj.id
            
            db_file = models.File(
                project_id=project_id,
                filename=job_info.get("metadata", {}).get("filename", "unknown.pdf"),
                s3_path=file_key,
                content="" # we'll fill this with markdown
            )
            db.add(db_file)
            db.flush()
            
            # 3. parse pdf -> markdown
            print("[WORKER] parsing pdf...")
            # save temp file for PyMuPDF
            temp_path = f"/tmp/{job_id}.pdf"
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
                
            markdown_content = pdf_service.extract_content(temp_path)
            db_file.content = markdown_content
            db.commit() # save markdown
            jobs.update_progress(job_id, "processing", 50)
            
            # 4. chunking
            print("[WORKER] chunking...")
            chunks = splitter.split_text(markdown_content, {})
            jobs.update_progress(job_id, "processing", 70)
            
            # 5. embedding & saving chunks
            print(f"[WORKER] embedding {len(chunks)} chunks...")
            
            chunk_texts = [c.page_content for c in chunks]
            vectors = embedder.get_embeddings(chunk_texts)
            
            # save to db
            db_chunks = []
            for i, chunk in enumerate(chunks):
                db_chunk = models.Chunk(
                    file_id=db_file.id,
                    content=chunk.page_content,
                    embedding=vectors[i],
                    chunk_metadata=chunk.metadata
                )
                db_chunks.append(db_chunk)
            
            db.add_all(db_chunks)
            db.commit()
            
            # complete
            jobs.update_progress(job_id, "completed", 100, {"chunks_count": len(chunks)})
            print(f"[WORKER] job {job_id} complete")
            
            return {"statusCode": 200, "body": json.dumps({"status": "completed", "chunks": len(chunks)})}

        except Exception as e:
            print(f"[WORKER] processing failed: {e}")
            jobs.update_progress(job_id, "failed", details={"error": str(e)})
            raise e
        finally:
            db.close()
            # cleanup tmp
            if os.path.exists(f"/tmp/{job_id}.pdf"):
                os.remove(f"/tmp/{job_id}.pdf")
            
    except Exception as e:
        print(f"[WORKER] fatal error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
