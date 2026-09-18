# RAG Learning + Production Upgrade Plan

เอกสารนี้ออกแบบให้ทำไปพร้อมกัน 2 เป้าหมาย:

1. เข้าใจหลักการ RAG อย่างเป็นระบบ
2. ยกระดับโค้ดจาก Demo ไปสู่ Production-ready ทีละขั้น

เวอร์ชันนี้เป็น Execution Playbook ที่เพิ่มเกณฑ์วัดผลชัดเจน, Exit Criteria ต่อเฟส, และแนวทาง rollout หลังขึ้นจริง

## เป้าหมายเชิงตัวเลข (Target KPIs)

- Accuracy (คำตอบถูกต้องตาม golden set): >= 80%
- Faithfulness (ไม่ตอบเกินหลักฐาน): >= 90%
- Retrieval hit rate@5: >= 85%
- p95 latency ต่อคำถาม: <= 8 วินาที (บนเครื่องทดสอบเดียวกัน)
- Error rate (5xx/timeout): <= 2%

หมายเหตุ: หากใช้โมเดลคนละขนาดหรือ hardware ต่างกัน ให้บันทึก benchmark ใหม่ทุกครั้ง

---

## แนวทางทำงาน

- แต่ละเฟสมี: หลักการ, งานที่ต้องทำ, สิ่งที่ต้องวัดผล, Exit Criteria
- จบแต่ละเฟสต้องมีผลลัพธ์ที่รันได้จริง
- ห้ามข้ามการวัดผล (evaluation)
- ทุกการเปลี่ยนพารามิเตอร์ต้องมี before/after result

---

## สถาปัตยกรรมเป้าหมาย (Target Architecture)

- Ingestion service: อ่านไฟล์, chunking, metadata, upsert
- Retrieval service: embed query, search, rerank, filter
- Generation service: prompt template, citation formatting, safety guardrails
- Evaluation module: golden set runner + report
- Observability module: structured logs, latency, errors, retrieval stats

---

## Phase 0: Baseline และความเข้าใจระบบเดิม (0.5-1 วัน)

### หลักการที่เรียน

- RAG pipeline: Ingest -> Chunk -> Embed -> Retrieve -> Generate
- ความต่างระหว่าง PoC กับ Production
- ความหมายของ Recall, Precision, Faithfulness

### งานที่ต้องทำ

- รันระบบเดิมให้ได้
- เตรียมชุดคำถามทดสอบ 20 ข้อ (golden questions)
- บันทึกพฤติกรรมเดิม: ตอบถูก/ผิด/มั่ว
- เก็บ baseline config ที่ใช้ทดสอบ (model, n_results, temperature, chunk strategy)

### สิ่งที่ต้องวัดผล

- Baseline accuracy จาก 20 คำถาม
- Latency เฉลี่ยต่อคำถาม
- สัดส่วนคำตอบที่ไม่มีหลักฐานอ้างอิง

### Exit Criteria

- มีไฟล์ baseline report อย่างน้อย 1 ชุด
- อธิบายได้ว่าปัญหาหลักอยู่ที่ retrieval หรือ generation

---

## Phase 1: Data Ingestion และ Chunking ที่ถูกต้อง (1-2 วัน)

### หลักการที่เรียน

- ทำไม chunking มีผลต่อ retrieval มากที่สุด
- Fixed-size vs Semantic/Recursive chunking
- Overlap มีผลต่อ context continuity อย่างไร

### งานที่ต้องทำ

- แยกโมดูล ingestion ออกจาก UI
- เปลี่ยนจาก split ตามบรรทัด เป็น chunking ที่กำหนดขนาดและ overlap
- เก็บ metadata ให้ครบ เช่น source, chunk_id, created_at
- ไม่ลบทั้ง collection ทุกครั้งที่อัปโหลดไฟล์
- รองรับ upsert ด้วย document_id เพื่อกันข้อมูลซ้ำ

### ค่าตั้งต้นแนะนำ

- chunk_size: 500-900 ตัวอักษร
- chunk_overlap: 80-150 ตัวอักษร
- normalize newlines: รองรับทั้ง \n และ \r\n

### สิ่งที่ต้องวัดผล

- เทียบผลก่อน/หลัง chunking ด้วยชุด 20 คำถาม
- ดู Top-k retrieval ว่าเจอเอกสารถูกชิ้นมากขึ้นหรือไม่
- ตรวจ duplicate ratio หลัง ingest

### Exit Criteria

- Retrieval hit rate@5 ดีขึ้นจาก baseline อย่างมีนัยสำคัญ
- ไม่เกิด data loss เมื่ออัปโหลดหลายไฟล์

---

## Phase 2: Retrieval Quality (2-3 วัน)

### หลักการที่เรียน

- Similarity search, Top-k, score threshold
- Query expansion และ reranking
- Hybrid search (dense + keyword)

### งานที่ต้องทำ

- เพิ่ม score threshold
- เพิ่ม reranker (cross-encoder หรือ heuristic rerank)
- รองรับ filter ตาม metadata
- เพิ่ม fallback strategy เมื่อผลค้นหาน้อยเกิน threshold

### สิ่งที่ต้องวัดผล

- Retrieval hit rate@k (k=3,5,10)
- MRR (Mean Reciprocal Rank)
- สัดส่วนคำตอบที่มีหลักฐานรองรับ

### Exit Criteria

- hit rate@5 >= 85% บน golden set
- คำถามที่ตอบมั่วจาก retrieval ผิด ลดลงอย่างน้อย 30% จาก baseline

---

## Phase 3: Prompting และ Safety (1-2 วัน)

### หลักการที่เรียน

- Prompt template ที่ลด hallucination
- Prompt injection คืออะไรและกันอย่างไร
- Grounded answer และการบังคับอ้างอิงแหล่งข้อมูล

### งานที่ต้องทำ

- ออกแบบ system prompt ที่บังคับตอบจาก context เท่านั้น
- ถ้า context ไม่พอ ให้ตอบว่าไม่พบข้อมูล
- แสดงแหล่งอ้างอิงในทุกคำตอบ
- เพิ่ม input sanitization ขั้นพื้นฐาน (เช่นจำกัดความยาวคำถาม)

### สิ่งที่ต้องวัดผล

- Faithfulness score
- Hallucination rate ลดลงจาก baseline
- Citation coverage (% คำตอบที่มีแหล่งอ้างอิง)

### Exit Criteria

- Faithfulness >= 90%
- Citation coverage >= 95%

---

## Phase 4: Engineering สำหรับ Production (2-4 วัน)

### หลักการที่เรียน

- 12-factor config
- Logging, monitoring, tracing
- Error handling, retry, timeout, rate limit

### งานที่ต้องทำ

- ย้ายค่าคงที่ไป env vars
- เพิ่ม structured logging
- เพิ่ม health endpoint และ basic metrics
- แยก service layer: ingestion, retrieval, generation
- ตั้ง timeout/retry สำหรับ embedding และ generation

### สิ่งที่ต้องวัดผล

- Mean latency, p95 latency, error rate
- MTTR เบื้องต้นจากกรณีจำลองล่ม
- Availability ระหว่างทดสอบโหลดเบื้องต้น

### Exit Criteria

- p95 latency <= 8 วินาที
- error rate <= 2%
- มี runbook incident พื้นฐานอย่างน้อย 1 ฉบับ

---

## Phase 5: Testing และ Evaluation Pipeline (2-3 วัน)

### หลักการที่เรียน

- Unit vs integration vs eval tests สำหรับ RAG
- Offline eval และ regression prevention

### งานที่ต้องทำ

- เพิ่ม unit tests ให้ chunking/retrieval logic
- เพิ่ม integration test เส้นทางถาม-ตอบ
- ทำ eval script ที่รัน golden questions อัตโนมัติ
- เพิ่ม regression gate ก่อน merge

### สิ่งที่ต้องวัดผล

- test pass rate
- eval regression gate ก่อนปล่อยระบบ
- สถิติ fail reasons (retrieve miss / grounding miss / generation miss)

### Exit Criteria

- test pass rate = 100% ใน main branch
- ไม่มี metric ต่ำกว่า baseline โดยไม่ระบุเหตุผลและ approve

---

## Phase 6: Release, Rollout และ Continuous Improvement (1-2 วัน)

### หลักการที่เรียน

- Safe rollout และ canary mindset
- Feedback loop สำหรับ knowledge base และ prompts
- Cost-performance tradeoff ของ model และ retrieval depth

### งานที่ต้องทำ

- สร้าง release checklist
- กำหนด rollback criteria
- เก็บ user feedback และ mapping กลับสู่ golden questions
- วาง cadence รีวิวคุณภาพรายสัปดาห์

### สิ่งที่ต้องวัดผล

- Post-release error rate
- User satisfaction score แบบง่าย (เช่น thumbs up/down)
- จำนวน issue ที่ถูกปิดจาก feedback loop

### Exit Criteria

- มี rollout + rollback ที่ทดสอบแล้ว
- มีรอบปรับปรุงคุณภาพต่อเนื่องอย่างน้อย 1 รอบ

---

## Evaluation Framework (ใช้เหมือนกันทุกเฟส)

ให้ประเมินคำตอบต่อข้อด้วย rubric 0-2:

- Correctness: 0 ผิด, 1 ถูกบางส่วน, 2 ถูกครบ
- Grounding: 0 ไม่มีหลักฐาน, 1 หลักฐานไม่ตรงบางส่วน, 2 หลักฐานตรงชัดเจน
- Helpfulness: 0 ใช้งานไม่ได้, 1 พอใช้, 2 ใช้งานได้ดี

สูตรคะแนนรวมต่อรอบ:

- weighted_score = 0.5 _ correctness + 0.3 _ grounding + 0.2 \* helpfulness

เกณฑ์ผ่านรอบ:

- average weighted_score >= 1.6
- grounding เฉลี่ยต้องไม่ต่ำกว่า 1.7

---

## Risk Register (ย่อ)

- ความเสี่ยง: chunk เล็กเกินไปจนบริบทขาด
  ผลกระทบ: retrieval hit ลด
  วิธีลดความเสี่ยง: เพิ่ม overlap และ eval ซ้ำ

- ความเสี่ยง: index ทับข้อมูลเก่าโดยไม่ตั้งใจ
  ผลกระทบ: data loss
  วิธีลดความเสี่ยง: ใช้ upsert + versioned document_id

- ความเสี่ยง: model ตอบเกิน context
  ผลกระทบ: hallucination
  วิธีลดความเสี่ยง: strict prompt + citation + fail-safe response

- ความเสี่ยง: latency สูงเมื่อข้อมูลโต
  ผลกระทบ: UX แย่
  วิธีลดความเสี่ยง: caching, rerank เฉพาะ top candidates, tune top-k

---

## Definition of Done (Production-ready ระดับเริ่มใช้งาน)

- มี ingestion pipeline ที่ไม่ทำข้อมูลหาย
- retrieval วัดผลได้และปรับจูนได้
- prompt มี safety guardrails
- มี logging/monitoring/error handling
- มี test + eval อัตโนมัติ
- มี rollout/rollback checklist

---

## ลำดับลงมือทำที่แนะนำในรีโปนี้

1. แยกโค้ดจากไฟล์เดียวเป็นหลายโมดูล
2. ปรับ chunking + metadata + upsert
3. เพิ่ม prompt template + source citation
4. เพิ่ม config ผ่าน env
5. เพิ่ม tests + eval script
6. เพิ่ม observability + release checklist

---

## แบบฝึกหัดสั้นทุกวัน (30-45 นาที)

- อธิบายให้ได้ว่าทำไมการตั้งค่า chunk_size และ overlap ปัจจุบันจึงเหมาะ/ไม่เหมาะ
- เขียนคำถามที่ระบบตอบผิด แล้วระบุว่าพลาดที่ retrieve หรือ generate
- ปรับ 1 พารามิเตอร์ แล้ววัดผลก่อน/หลังทุกครั้ง
- เลือก 1 คำตอบที่มั่ว แล้วเขียน prompt/safety rule ใหม่เพื่อลดโอกาสเกิดซ้ำ

---

## Template บันทึกผลการทดลอง (คัดลอกใช้ได้ทันที)

- Date:
- Dataset version:
- Model + Embedding:
- Chunk strategy:
- Retrieval config (k, threshold, rerank):
- Prompt version:
- Accuracy:
- Faithfulness:
- Hit rate@5:
- p95 latency:
- สรุปสิ่งที่ดีขึ้น:
- ปัญหาที่ยังค้าง:
- Action ถัดไป:
