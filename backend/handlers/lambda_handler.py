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
        # qstash sends body as string in 'body' field
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
            job_info = jobs.get_job(job_id)
            project_id = job_info.get("metadata", {}).get("project_id")
            
            # if no project, create one
            if not project_id:
                new_proj = models.Project(title=f"upload_{job_id[:8]}", status="processing")
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
            chunks = splitter.split_text(markdown_content)
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
            jobs.update_progress(job_id, "processing", 80)
            
             # 6. graph extraction (stateful & sequential)
            print("[WORKER] starting graph extraction...")
            from services.llm.graph_extractor import GraphExtractor
            from services.graph_service import GraphService
            
            extractor = GraphExtractor()
            graph_service = GraphService()
            
            # create simple windows (striding)
            # 50k chars per window, overlap 5k
            window_size = 50000
            overlap = 5000
            
            # naive splitting of markdown_content
            text_len = len(markdown_content)
            windows = []
            
            if text_len <= window_size:
                windows.append(markdown_content)
            else:
                start = 0
                while start < text_len:
                    end = min(start + window_size, text_len)
                    windows.append(markdown_content[start:end])
                    if end == text_len:
                        break
                    start += (window_size - overlap)
            
            print(f"[WORKER] created {len(windows)} windows for extraction")
            
            # sequential processing
            accumulated_nodes = [] # keeps track of what we found to guide next prompt
            extracted_graphs = []
            
            async def process_windows():
                for i, window_text in enumerate(windows):
                    print(f"[WORKER] extracting window {i+1}/{len(windows)}...")
                    # pass existing concept IDs to guide LLM
                    concept_ids = [n.id for n in accumulated_nodes]
                    
                    # calling gemini with state
                    graph_data = await extractor.extract_from_window(window_text, existing_concepts=concept_ids)
                    
                    extracted_graphs.append(graph_data)
                    
                    # accumulate new nodes for next iteration context
                    accumulated_nodes.extend(graph_data.nodes)
                    
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.run_until_complete(process_windows())
                
            # 7. graph resolution & merge
            print("[WORKER] resolving entities...")
            resolved_graph = graph_service.build_graph(extracted_graphs)
            print(f"[WORKER] resolved to {len(resolved_graph.nodes)} nodes")
            
            graph_dump = resolved_graph.model_dump()
            
            # 8. save result
            jobs.update_progress(job_id, "completed", 100, {
                "chunks_count": len(chunks),
                "graph_nodes": len(resolved_graph.nodes),
                "graph_links": sum(len(n.links) for n in resolved_graph.nodes),
                "graph_preview": graph_dump
            })
            print(f"[WORKER] job {job_id} complete")
            
            return {"statusCode": 200, "body": json.dumps({
                "status": "completed", 
                "chunks": len(chunks),
                "graph": graph_dump
            })}

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
