# Basic RAG Concept

โปรเจกต์สำหรับศึกษา **Retrieval-Augmented Generation (RAG)** แบบ Local โดยตั้งใจให้ source code อ่านง่ายและมองเห็น pipeline ของ RAG โดยตรง มากกว่าซ่อนรายละเอียดไว้หลัง framework ขนาดใหญ่

> ใช้เพื่อการศึกษาและทดลองแนวคิด RAG ไม่ใช่ production application

## RAG Flow

```text
Document
   ↓
Chunking
   ↓
Embedding (nomic-embed-text)
   ↓
Persistent ChromaDB
   ↓
User Query → Query Embedding
   ↓
Semantic Retrieval + Lexical Matching
   ↓
Hybrid Score / Rerank / Threshold
   ↓
Selected Context
   ↓
Prompt
   ↓
Gemma 3 1B via Ollama
   ↓
Answer + Sources
```

## Technology Stack

- Python
- Gradio — Admin/Chat UI
- Ollama — Local model runtime
- `gemma3:1b` — generation model
- `nomic-embed-text` — embedding model
- ChromaDB — vector store

## Current Learning Features

- Fixed-size chunking พร้อม overlap
- Metadata และ content-hash deduplication
- Semantic + lexical hybrid retrieval
- Reranking และ score threshold
- Grounded prompt และ insufficient-context fallback
- Source citation
- Small-talk routing
- **Persistent Vector Store** — index ยังคงอยู่หลัง restart application

Roadmap การพัฒนา RAG Learning Lab ดูได้ที่ `PLAN.md`

## Prerequisites

1. Python
2. Ollama
3. โมเดล embedding และ generation

```bash
ollama pull nomic-embed-text
ollama pull gemma3:1b
```

ติดตั้ง Python dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python rag_app.py
```

Entry point คือ `rag_app.py` และ Gradio จะแสดงทั้ง Admin Upload และ User Chat

## Persistent ChromaDB

ตั้งแต่ Phase 1 ระบบใช้ `chromadb.PersistentClient` แทน in-memory client โดยเก็บ vector index ไว้ที่:

```text
data/chroma/
```

โฟลเดอร์นี้เป็น **runtime data** และถูก ignore จาก Git

ความหมายเชิงการเรียนรู้คือ เอกสารที่ upload จะถูกแบ่งเป็น chunks → สร้าง embeddings → บันทึกลง Vector Store และเมื่อปิด/เปิด application ใหม่ index เดิมยังสามารถถูกเรียกใช้ได้ โดยไม่ต้อง ingest เอกสารใหม่ทุกครั้ง

### วิธีทดลอง Persistence

1. เปิด Ollama และรัน `python rag_app.py`
2. Upload ไฟล์ `.txt` จากหน้า Admin
3. กด **Show Index Stats** และจดจำนวน chunks/documents
4. ปิด application
5. รัน `python rag_app.py` ใหม่
6. กด **Show Index Stats** อีกครั้ง
7. จำนวน indexed chunks/documents ควรยังคงอยู่

การ upload เอกสารเดิมซ้ำใช้ content hash และ document metadata เพื่อลดการสร้าง chunk ซ้ำ

## Learning Roadmap

โปรเจกต์จะพัฒนาต่อเป็นลำดับ:

1. Persistent Vector Store
2. Document & Chunk Inspector
3. Retrieval Inspector
4. RAG Configuration Lab
5. Prompt & Context Inspector
6. Evaluation Lab
7. Learning-oriented Refactor

เป้าหมายคือทำให้ผู้เรียนสามารถทดลองและอธิบายได้ว่า **RAG ดึงข้อมูลอะไรมา ทำไมจึงเลือกข้อมูลนั้น และ context ใดถูกส่งให้ LLM ก่อนสร้างคำตอบ**

## License

GNU General Public License (GPL)
