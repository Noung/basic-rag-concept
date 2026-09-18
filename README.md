####  Demo Application RAG 

    This repo is code demo RAG  using ollama, chroma, gradio    
    เป็น Code ตัวอย่าง ในการเรียนรู้ การทำ RAG ด้วย ollama, chroma, gradio
    ประกอบ การนำเสนอ Youtube เมื่อการ tuning Model ไม่เพียงพอ เราจึงต้อง RAG จากช่อง T-LIVE-CODE

### การเตรียม เครื่อง
    1. ติดตั้ง Ollama
    2. Load Model
    3. run python rag_app.py
   
### ติดตั้ง Ollama  
    สามารถดูได้ที่ Clip: Guild Install and Use Local LLM Ollama (Thai) 
    https://www.youtube.com/watch?v=EcHLhO8gJ5Y&t=2149s

### Load Model
    > ollama pull  nomic-embed-text
    > ollama pull  gemma3:1b
    

### install Python lib
    > pip install -r requirements.txt

### Run App
    > python rag_app.py

### Remark
    This code in this repository  for RAG learning only  do not using on production environment
    โค๊ดภายใต้ Repo นี้ จัดทำเพื่อการศึกษา และทำความเข้าใจ กระบวนการ RAG เท่านั้น ไม่สามารถนำไปใช้งาน จริงบนระบบ โปรดัคชั่นได้

### License 
    GNU Public License