"""Grounded prompt and citation helpers for the Learning Lab."""

from config import INSUFFICIENT_CONTEXT_TEXT


def build_grounded_prompt(query, selected_chunks):
    """Build the exact grounded prompt used before generation."""
    context_parts = []
    sources = []
    for item in selected_chunks:
        metadata = item.get("metadata") or {}
        source = metadata.get("source", "unknown")
        if source not in sources:
            sources.append(source)
        context_parts.append(
            f"[Source: {source} | Score: {item.get('final_score', 0.0):.3f}]\n"
            f"{item.get('document', '')}"
        )

    context = "\n\n".join(context_parts)
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
    return {"prompt": prompt, "context": context, "sources": sources}


def citation_block(sources):
    """Format source names for the final answer."""
    return "\n\nSources:\n" + "\n".join(
        f"- {source}" for source in sources
    )
