import gradio as gr
import chromadb
from chromadb.utils import embedding_functions
import ollama
import os
import re
from ingestion import (
    chunk_text,
    document_id_from_path,
    prepare_unique_chunks,
    timestamp_utc,
)

MODEL = "gemma3:1b"
RETRIEVAL_TOP_K = 8
INSUFFICIENT_CONTEXT_TEXT = "ไม่พบข้อมูลเพียงพอในเอกสารที่อัปโหลด"
SEMANTIC_WEIGHT = 0.75
LEXICAL_WEIGHT = 0.25
MIN_FINAL_SCORE = 0.22
FALLBACK_FINAL_SCORE = 0.16
MAX_CONTEXT_CHUNKS = 4

# Initialize ChromaDB client เตรียม Vector database สำหรับ RAG
client = chromadb.Client()

# Create or get collection สร้าง ถังเก็บข้อมูล
collection = client.get_or_create_collection(name="rag_collection")

# Initialize Ollama embedding function , เตรียม Function สำหรับ แปลงข้อมูลเป็น vector
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text"
)

# อ่านไฟล์ข้อความ
def load_text_file(file_path):
    """Read text file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def _safe_list(value):
    """Normalize optional array-like values from vector DB responses."""
    return value if isinstance(value, list) else []


def _tokenize_for_lexical_score(text):
    """Tokenize Thai/English text for lightweight lexical matching."""
    cleaned = re.sub(r"[^0-9a-zA-Zก-๙\s]", " ", text.lower())
    tokens = [token for token in cleaned.split() if token]
    return tokens


def _lexical_overlap_score(query, text):
    """Compute overlap score between query and candidate chunk text (0..1)."""
    query_tokens = set(_tokenize_for_lexical_score(query))
    text_tokens = set(_tokenize_for_lexical_score(text))
    if not query_tokens or not text_tokens:
        return 0.0
    shared = query_tokens.intersection(text_tokens)
    return len(shared) / len(query_tokens)


def distance_to_relevance(distance):
    """Convert vector distance to a bounded relevance score (0..1)."""
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + max(float(distance), 0.0))


def retrieve_relevant_chunks(query, n_results=RETRIEVAL_TOP_K):
    """Retrieve chunks with hybrid scoring (semantic + lexical) and rerank."""
    query_embedding = ollama_ef([query])[0]
    raw_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = raw_results.get("documents", [[]])
    metadatas = raw_results.get("metadatas", [[]])
    distances = raw_results.get("distances", [[]])

    docs = documents[0] if documents else []
    metas = metadatas[0] if metadatas else []
    dists = distances[0] if distances else []

    candidates = []
    for index, doc in enumerate(docs):
        metadata = metas[index] if index < len(metas) else {}
        distance = dists[index] if index < len(dists) else None
        semantic_score = distance_to_relevance(distance)
        lexical_score = _lexical_overlap_score(query, doc)
        final_score = (SEMANTIC_WEIGHT * semantic_score) + (LEXICAL_WEIGHT * lexical_score)
        candidates.append(
            {
                "document": doc,
                "metadata": metadata,
                "distance": distance,
                "semantic_score": semantic_score,
                "lexical_score": lexical_score,
                "final_score": final_score,
            }
        )

    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    selected = [c for c in candidates if c["final_score"] >= MIN_FINAL_SCORE]
    selected = selected[:MAX_CONTEXT_CHUNKS]

    # Safe fallback: if none pass strict threshold, keep a small set when relevance is still acceptable.
    if not selected:
        fallback = [c for c in candidates if c["final_score"] >= FALLBACK_FINAL_SCORE]
        selected = fallback[:2]

    top_score = candidates[0]["final_score"] if candidates else 0.0
    avg_score = sum(item["final_score"] for item in selected) / len(selected) if selected else 0.0

    return selected, {"top_score": top_score, "avg_score": avg_score}


def _small_talk_response(query):
    """Handle casual chat without routing to RAG retrieval."""
    normalized = re.sub(r"\s+", " ", query.lower()).strip()
    if not normalized:
        return None

    # Remove trailing punctuation and polite ending spaces for intent matching.
    normalized = re.sub(r"[!?.。]+$", "", normalized).strip()

    greeting_patterns = [
        r"^สวัสดี(ครับ|ค่ะ|คับ)?$",
        r"^หวัดดี(ครับ|ค่ะ|คับ)?$",
        r"^ดีจ้า(ครับ|ค่ะ|คับ)?$",
        r"^hello$",
        r"^hi$",
    ]
    thanks_patterns = [r"ขอบคุณ", r"thank you", r"thanks"]
    bye_patterns = [r"ลาก่อน", r"บาย", r"bye", r"goodbye"]
    capability_patterns = [
        r"คุณมีความรู้เรื่องใดบ้าง",
        r"ทำอะไรได้บ้าง",
        r"ช่วยอะไรได้บ้าง",
        r"ถามอะไรได้บ้าง",
    ]

    if any(re.search(pattern, normalized) for pattern in greeting_patterns):
        return "สวัสดีครับ ผมพร้อมช่วยตอบคำถามจากเอกสารที่อัปโหลด เช่น วันหยุด, รายชื่อบุคคล หรือข้อมูลในไฟล์ที่คุณใส่ไว้"

    if any(re.search(pattern, normalized) for pattern in thanks_patterns):
        return "ยินดีครับ หากต้องการทดสอบเพิ่ม ลองถามเป็นวันที่หรือหัวข้อเฉพาะจากเอกสารได้เลย"

    if any(re.search(pattern, normalized) for pattern in bye_patterns):
        return "ขอบคุณครับ แล้วพบกันใหม่"

    if any(re.search(pattern, normalized) for pattern in capability_patterns):
        return (
            "ผมช่วยตอบได้จากเอกสารที่อัปโหลด เช่น วันหยุด, หุ้น, หรือข้อมูลข้อความในไฟล์ต่าง ๆ\n"
            "ตัวอย่างคำถาม:\n"
            "- วันหยุดทั้งหมดในปีนี้มีกี่วัน\n"
            "- วันที่ 10 ธันวาคม 2568 คือวันอะไร\n"
            "- วันสงกรานต์ปี 2568 มีวันไหนบ้าง"
        )

    return None


def _should_abstain(selected_chunks, retrieval_stats):
    """Decide whether evidence quality is too low for a grounded answer."""
    if not selected_chunks:
        return True
    return retrieval_stats["top_score"] < FALLBACK_FINAL_SCORE


def upsert_document_chunks(doc_id, source_name, chunk_pairs):
    """Upsert a document by content hash and delete obsolete chunks only."""
    existing = collection.get(where={"document_id": doc_id}, include=["metadatas"])
    existing_ids = _safe_list(existing.get("ids") if existing else [])
    existing_metas = _safe_list(existing.get("metadatas") if existing else [])

    existing_hash_to_id = {}
    ids_to_delete = []
    for idx, metadata in enumerate(existing_metas):
        row_id = existing_ids[idx] if idx < len(existing_ids) else None
        content_hash = metadata.get("content_hash") if metadata else None
        if row_id and content_hash:
            existing_hash_to_id[content_hash] = row_id
        elif row_id:
            ids_to_delete.append(row_id)

    new_hashes = [content_hash for _, content_hash in chunk_pairs]
    new_hash_set = set(new_hashes)

    for content_hash, row_id in existing_hash_to_id.items():
        if content_hash not in new_hash_set:
            ids_to_delete.append(row_id)

    chunks_to_add = []
    hashes_to_add = []
    for chunk, content_hash in chunk_pairs:
        if content_hash not in existing_hash_to_id:
            chunks_to_add.append(chunk)
            hashes_to_add.append(content_hash)

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    added_count = 0
    if chunks_to_add:
        created_at = timestamp_utc()
        embeddings = ollama_ef(chunks_to_add)
        ids = [f"{doc_id}_{content_hash[:16]}" for content_hash in hashes_to_add]
        metadatas = [
            {
                "source": source_name,
                "document_id": doc_id,
                "chunk_id": index,
                "created_at": created_at,
                "content_hash": content_hash,
            }
            for index, content_hash in enumerate(hashes_to_add)
        ]
        collection.add(
            documents=chunks_to_add,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        added_count = len(chunks_to_add)

    skipped_count = len(chunk_pairs) - added_count
    removed_count = len(ids_to_delete)
    return added_count, skipped_count, removed_count


def get_index_stats():
    """Summarize current vector index state for admin monitoring."""
    total_chunks = collection.count()
    if total_chunks == 0:
        return "No indexed chunks yet"

    rows = collection.get(include=["metadatas"])
    metadatas = _safe_list(rows.get("metadatas") if rows else [])

    document_ids = set()
    sources = set()
    for metadata in metadatas:
        if not metadata:
            continue
        document_id = metadata.get("document_id")
        source = metadata.get("source")
        if document_id:
            document_ids.add(document_id)
        if source:
            sources.add(source)

    return (
        f"Total chunks: {total_chunks}\n"
        f"Unique documents: {len(document_ids)}\n"
        f"Sources: {', '.join(sorted(sources)) if sources else 'N/A'}"
    )


# ทำการใส่ข้อมูล จากไฟล์ ใส่เข้า Vector database
def index_document(file):
    """Index the document into ChromaDB."""
    if file and os.path.exists(file.name):
        text = load_text_file(file.name)
        if isinstance(text, str) and text.startswith("Error reading file:"):
            return text

        chunks = chunk_text(text, chunk_size=700, chunk_overlap=120)
        if not chunks:
            return "No content found in file after chunking"

        chunk_pairs = prepare_unique_chunks(chunks)
        if not chunk_pairs:
            return "No unique chunk content found in file"

        source_name = os.path.basename(file.name)
        doc_id = document_id_from_path(file.name)

        added_count, skipped_count, removed_count = upsert_document_chunks(
            doc_id=doc_id,
            source_name=source_name,
            chunk_pairs=chunk_pairs,
        )
        return (
            f"Processed {len(chunk_pairs)} unique chunks from {source_name} | "
            f"added={added_count}, reused={skipped_count}, removed={removed_count}"
        )
    return "Invalid file path or no file uploaded"

# สอบถามด้วยการ RAG จากข้อมูลก่อน
def query_rag(query, history,temperature=0.3, n_results=5):
   
    if not query:
        yield "Please enter a question"
        return

    small_talk = _small_talk_response(query)
    if small_talk:
        yield small_talk
        return

    selected_chunks, retrieval_stats = retrieve_relevant_chunks(
        query,
        n_results=max(n_results, RETRIEVAL_TOP_K),
    )
    if _should_abstain(selected_chunks, retrieval_stats):
        yield INSUFFICIENT_CONTEXT_TEXT
        return

    source_refs = []
    for item in selected_chunks:
        metadata = item["metadata"]
        source = metadata.get('source', 'unknown') if metadata else 'unknown'
        if source not in source_refs:
            source_refs.append(source)

    # Combine relevant chunks with source information ถ้าเจอข้อมูล ให้ทำการ สร้าง prompt 
    context = ""
    for item in selected_chunks:
        doc = item["document"]
        metadata = item["metadata"]
        source = metadata.get('source', 'unknown') if metadata else 'unknown'
        score = item.get("final_score", 0.0)
        context += f"[Source: {source} | Score: {score:.3f}]\n{doc}\n\n"

    # Stream response using ollama.generate with temperature  เตรียม context ที่ดึงจาก Vector database ถามไปที่ ollama
    prompt = (
        "คุณเป็นผู้ช่วยที่ตอบจากเอกสารที่ให้เท่านั้น\n"
        "กติกา:\n"
        "1) ใช้ข้อมูลจาก Context เท่านั้น\n"
        "2) ถ้าพบข้อมูลที่ตอบคำถามได้ ให้ตอบสั้น กระชับ ชัดเจน เป็นภาษาไทย\n"
        f"3) ถ้าไม่พบข้อมูลที่ตอบได้จริง ให้ตอบว่า: {INSUFFICIENT_CONTEXT_TEXT}\n"
        "4) ห้ามแต่งข้อมูลเพิ่มเอง\n\n"
        "5) ถ้าคำถามขอจำนวนหรือรายการ ให้คำนวณ/สรุปจาก Context ก่อนตอบ\n\n"
        f"Context:\n{context}\n"
        f"Question: {query}\n"
        "Answer:"
    )
    
    stream = ollama.generate(
        model=MODEL,
        prompt=prompt,
        stream=True,
        options={"temperature": float(temperature)}
    )
    
    # คืนค่า คำตอบ
    response = ""
    for chunk in stream:
        response += chunk['response']
        yield response

    if source_refs:
        citation_block = "\n\nSources:\n" + "\n".join([f"- {source}" for source in source_refs])
        yield response + citation_block

# ส่วนของหน้าจอ UI
# Admin interface for uploading files ส่วน Admin 
def admin_interface(file):
    """Admin interface for uploading and indexing text files."""
    return index_document(file)


def admin_stats_interface():
    """Admin interface for viewing index stats."""
    return get_index_stats()

# Create Gradio interfaces
with gr.Blocks() as admin_app:
    gr.Markdown("# Admin Interface")
    gr.Markdown("Upload a text file to index its content for the chatbot.")
    file_input = gr.File(label="Upload Text File")
    output = gr.Textbox(label="Indexing Result")
    upload_btn = gr.Button("Upload and Index")
    stats_btn = gr.Button("Show Index Stats")
    stats_output = gr.Textbox(label="Index Stats")
    upload_btn.click(fn=admin_interface, inputs=file_input, outputs=output)
    stats_btn.click(fn=admin_stats_interface, inputs=None, outputs=stats_output)
# ส่วนของ ChatBot
with gr.Blocks() as chat_app:
    gr.Markdown("# Chatbot Interface")
    gr.Markdown("Ask questions based on the indexed text file content.")
    gr.ChatInterface(query_rag)

# main function
if __name__ == "__main__":
    # Launch both interfaces
    gr.TabbedInterface(
        [admin_app, chat_app],
        ["Admin Upload", "User Chat"],
        title="RAG Application with Ollama and ChromaDB"
    ).launch()