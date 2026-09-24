# Basic RAG Learning Lab — คู่มือการรันระบบ

คู่มือนี้ใช้สำหรับรันโครงการบน Windows ด้วย Ollama และ Gradio

## 1. เตรียม Ollama และโมเดล

เปิด Ollama แล้วตรวจสอบโมเดล:

```powershell
ollama list
```

ต้องมี:

```text
gemma3:1b
nomic-embed-text
```

ถ้ายังไม่มี ให้ติดตั้ง:

```powershell
ollama pull gemma3:1b
ollama pull nomic-embed-text
```

## 2. เปิดโครงการ

```powershell
cd C:\Users\Kittisak\Downloads\local-rag\rag_learning-main
```

หากเก็บโครงการไว้ที่อื่น ให้เปลี่ยน path ให้ตรงกับเครื่องจริง

## 3. ติดตั้งและตรวจสอบ Python dependencies

ทำครั้งแรก หรือเมื่อ `requirements.txt` เปลี่ยนแปลง:

```powershell
python -m pip install -r requirements.txt
```

ตรวจสอบ syntax และ unit tests:

```powershell
python -m py_compile rag_app.py ingestion.py config.py vector_store.py retrieval.py generation.py evaluation.py
python -m unittest discover -s tests -v
```

## 4. รัน Gradio

```powershell
python rag_app.py
```

เปิดเบราว์เซอร์ที่:

```text
http://127.0.0.1:7860
```

ถ้า Terminal แสดง URL หรือ port อื่น ให้ใช้ค่าที่แสดงจริง

## 5. ลำดับการทดสอบหน้าเว็บ

### Admin Upload

1. เลือก `thai_holiday.txt`
2. ใช้ค่า Chunk Size `700` และ Chunk Overlap `120` หรือทดลองค่าอื่น
3. กด `Upload and Index`
4. กด `Show Index Stats`
5. กด `Inspect Documents & Chunks`

### Retrieval Inspector

ป้อนคำถาม เช่น:

```text
วันสงกรานต์ปี 2568 มีวันไหนบ้าง
```

ตรวจสอบ Top-K, semantic score, lexical score, final score และ threshold decision

### Prompt & Context Inspector

ใช้คำถามเดียวกันเพื่อดู context, source citation และ prompt ก่อนส่งให้ LLM

### Evaluation Lab

กด `Run Golden Set Evaluation` หรือรันจาก Terminal:

```powershell
python evaluation.py
```

### User Chat

ไปแท็บ `User Chat` แล้วถาม เช่น:

```text
วันรัฐธรรมนูญปี 2568 ตรงกับวันที่เท่าไร
```

คำตอบควรแสดง source citation เช่น `thai_holiday.txt`

## 6. หยุดและเริ่มระบบใหม่

หยุดด้วย `Ctrl + C` แล้วเริ่มใหม่:

```powershell
python rag_app.py
```

Persistent ChromaDB อยู่ที่:

```text
data\chroma\
```

จึงไม่ต้อง ingest เอกสารซ้ำหลัง restart

## 7. ทดสอบ deduplication

อัปโหลดไฟล์เดิมซ้ำ ผลลัพธ์ควรมีลักษณะดังนี้:

```text
added=0, reused=<จำนวน chunks>, removed=0
```

## 8. Environment Variables

ตั้งค่าก่อนเปิดโปรแกรมได้ เช่น:

```powershell
$env:RAG_MODEL="gemma3:1b"
$env:RAG_EMBEDDING_MODEL="nomic-embed-text"
$env:RAG_RETRIEVAL_TOP_K="8"
$env:RAG_CHUNK_SIZE="700"
$env:RAG_CHUNK_OVERLAP="120"
```

ค่าจะมีผลกับการเปิดโปรแกรมครั้งถัดไปใน Terminal นั้น

## 9. ปัญหาที่พบบ่อย

### Ollama ไม่พบโมเดล

```powershell
ollama list
ollama pull gemma3:1b
ollama pull nomic-embed-text
```

### Ollama ไม่ทำงาน

เปิด Ollama แล้วตรวจสอบ:

```powershell
ollama ps
```

### Port 7860 ถูกใช้งาน

ปิดโปรแกรมที่ใช้ port อยู่ หรือกำหนด port ผ่าน Gradio ตามเวอร์ชันที่ติดตั้ง

### ระบบตอบว่าไม่พบข้อมูล

ตรวจว่าอัปโหลดเอกสารแล้ว, ดู `Show Index Stats`, ใช้คำถามที่มีอยู่ในเอกสาร และดู Retrieval Inspector เพื่อเช็ก score/threshold

### ภาษาไทยแสดงผิดใน Terminal

DevSpace หรือ Terminal บางแบบอาจแสดง UTF-8 เพี้ยน แต่หน้า Gradio และไฟล์ UTF-8 ควรแสดงภาษาไทยถูกต้อง

## 10. คำสั่งที่ใช้บ่อย

```powershell
python rag_app.py
python evaluation.py
python -m unittest discover -s tests -v
```
