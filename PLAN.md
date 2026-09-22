# Basic RAG Concept — Learning Lab Plan

## Goal
พัฒนา Basic RAG ให้เป็น RAG Learning Lab ที่รันบน Local และทำให้ผู้เรียนมองเห็น pipeline: Document → Chunk → Embedding → Vector Store → Retrieval → Context → LLM → Answer โดยเน้นความเข้าใจและการทดลอง มากกว่าความซับซ้อนแบบ production.

## Development Rule
ทุก code change ต้องทำตามลำดับ: ระบุ task → แก้ code → ทดสอบ → อัปเดต PLAN.md → ตรวจ diff/status → commit → push ไป origin/main.

สถานะ: ⬜ Planned | 🟡 In Progress | ✅ Completed | 🔴 Blocked

## Baseline
**Status: ✅ Completed**

ระบบปัจจุบันใช้ Python, Gradio, Ollama, gemma3:1b, nomic-embed-text และ ChromaDB มี fixed-size chunking + overlap, metadata, content-hash deduplication, semantic + lexical hybrid scoring, reranking/threshold, grounded prompt, abstain เมื่อ context ไม่พอ, source citation และ small-talk routing. Entry point คือ `rag_app.py`.

## Roadmap

### Phase 1 — Persistent Vector Store
**Status: ✅ Completed**
- [x] เปลี่ยน ChromaDB จาก in-memory เป็น persistent storage
- [x] กำหนด directory สำหรับ vector data
- [x] ป้องกัน runtime vector data ไม่ให้เข้า Git
- [x] ทดสอบ restart แล้ว index ยังอยู่ (ทดสอบผ่านด้วย Persistent ChromaDB)
- [x] ตรวจ dedup/upsert เดิมว่ายังทำงาน (เอกสารเดิม reused=3, added=0, removed=0)
- [x] แสดงจำนวน documents/chunks ใน index (มี `get_index_stats()` จาก baseline)

**Learning outcome:** เข้าใจความแตกต่างระหว่าง document, embedding และ vector store.
**Exit criteria:** restart แล้วข้อมูลยังอยู่, ingest ซ้ำไม่เกิด duplicate, runtime data ไม่ถูก commit.

### Phase 2 — Document & Chunk Inspector
**Status: ⬜ Planned**
- [ ] แสดง document, จำนวน chunks, chunk size/overlap
- [ ] เปิดดูเนื้อหา chunk และ metadata
- [ ] แสดง added/reused/removed chunks

**Learning outcome:** เห็นว่าเอกสารถูก chunk ก่อน embedding และเห็นผลของ chunk size/overlap.

### Phase 3 — Retrieval Inspector
**Status: ⬜ Planned**
- [ ] แสดง Top-K chunks และ source
- [ ] แสดง semantic, lexical และ final score
- [ ] แสดง threshold decision
- [ ] ระบุ chunks ที่ถูกส่งเข้า LLM

**Learning outcome:** เข้าใจว่า application retrieve context ก่อนส่งให้ LLM.

### Phase 4 — RAG Configuration Lab
**Status: ⬜ Planned**
- [ ] ทดลองปรับ chunk size/overlap
- [ ] Top-K / max context chunks
- [ ] semantic/lexical weight
- [ ] score threshold
- [ ] temperature

**Learning outcome:** เห็นผลของ parameter ต่อ retrieval และคำตอบ.

### Phase 5 — Prompt & Context Inspector
**Status: ⬜ Planned**
- [ ] แสดง context ที่ส่งเข้า LLM
- [ ] แสดง prompt template และ sources
- [ ] แสดง insufficient-context path

**Learning outcome:** เข้าใจ grounding, hallucination และบทบาทของ prompt.

### Phase 6 — Evaluation Lab
**Status: ⬜ Planned**
- [ ] สร้าง golden questions
- [ ] expected answer/source
- [ ] วัด Retrieval Hit Rate@K, Source Match, Correct/Incorrect/No Answer และ latency
- [ ] เปรียบเทียบก่อน/หลังปรับ configuration

**Learning outcome:** เข้าใจว่าการปรับ RAG ต้องวัดผล ไม่ตัดสินจากคำถามไม่กี่ข้อ.

### Phase 7 — Learning-oriented Refactor
**Status: ⬜ Planned**
- [ ] แยก `vector_store.py`
- [ ] แยก `retrieval.py`
- [ ] แยก `generation.py`
- [ ] แยก `config.py`
- [ ] เพิ่ม evaluation directory
- [ ] ปรับ README ให้ตรงกับ Learning Lab

เป้าหมายคือ module อ่านง่ายและ map กลับไปยัง RAG pipeline ได้ โดยยังไม่เพิ่ม framework ที่ไม่จำเป็น เช่น FastAPI, React/Vue, Redis, Celery, Kubernetes หรือ LangChain/LlamaIndex abstraction.

## Progress Log

### 2026-09-18 — Planning Baseline
**Status: ✅ Completed**
- ยืนยัน branch `main`
- ยืนยัน `origin` = `https://github.com/Noung/basic-rag-concept.git`
- Baseline commit: `29ea18b chore: initialize basic RAG learning project`
- วิเคราะห์ pipeline ปัจจุบัน
- กำหนด roadmap Phase 1–7
- กำหนด workflow: test → PLAN.md → diff/status → commit → push

### 2026-09-18 — Phase 1 Implementation
**Status: 🟡 In Progress**
- เปลี่ยน `chromadb.Client()` เป็น `chromadb.PersistentClient()`
- กำหนด vector data ที่ `data/chroma/`
- เพิ่ม `.gitignore` ป้องกัน runtime vector data และ Python cache ใหม่
- ปรับ README อธิบาย architecture, persistence และขั้นตอนทดสอบ
- `python -m py_compile rag_app.py ingestion.py` ผ่าน
- `git diff --check` ผ่าน
- ตรวจ `.gitignore` แล้ว `data/chroma/` ถูก ignore ตามที่กำหนด
- ยังต้องทดสอบ persistence และ dedup/upsert แบบ end-to-end ร่วมกับ Ollama ก่อนปิด Phase 1

**Next:** เริ่ม Phase 2 — Document & Chunk Inspector

### 2026-09-22 — Development Models and End-to-End Test
**Status: 🟡 In Progress**
- ติดตั้งโมเดลสำหรับ Development/Test: `gemma3:1b` และ `nomic-embed-text`
- ปรับ `rag_app.py`, `README.md` และ Baseline description ให้ใช้โมเดลทั้งสอง
- `python -m py_compile rag_app.py ingestion.py` ผ่าน
- ทดสอบ End-to-End กับ `thai_holiday.txt` สำเร็จ: อ่านเอกสาร → สร้าง 3 chunks → สร้าง embeddings → บันทึก ChromaDB → retrieval ได้ 3 chunks → สร้างคำตอบและแสดง source citation
- Retrieval ได้ `top_score=0.574` และ `avg_score=0.568`
- ยืนยันว่าโมเดลขนาดใหญ่ `gemma3:12b` และ `qwen3-embedding:8b` ไม่เหมาะกับเครื่อง Development ปัจจุบันเนื่องจากหน่วยความจำไม่เพียงพอ
- ทดสอบ restart persistence สำเร็จ: เปิด process ใหม่แล้วยังพบ 3 chunks และ 1 document
- ทดสอบ ingest เอกสารเดิมซ้ำสำเร็จ: `added=0`, `reused=3`, `removed=0`
- ปิด Phase 1 สำเร็จตาม Exit Criteria

### 2026-09-22 — Phase 1 Verification
**Status: ✅ Completed**
- ตรวจ index ก่อนและหลังเปิด Python process ใหม่ พบข้อมูลคงอยู่ครบ: 3 chunks, 1 document
- ingest `thai_holiday.txt` ซ้ำหลัง restart ไม่สร้างข้อมูลซ้ำ
- ผลลัพธ์: `added=0`, `reused=3`, `removed=0`
- ยืนยันว่า runtime data ใน `data/chroma/` ไม่ถูก commit เนื่องจาก `.gitignore`

## Current Status
Baseline ✅ | Phase 1 ✅ | Phase 2 ⬜ | Phase 3 ⬜ | Phase 4 ⬜ | Phase 5 ⬜ | Phase 6 ⬜ | Phase 7 ⬜
