"""
Vision API - Photo-based scenic spot recognition ("看景即讲")
Uses Doubao's multimodal image understanding capability
"""
import logging
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas import VisionRecognizeResponse
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision", tags=["Vision"])


@router.post("/recognize", response_model=VisionRecognizeResponse)
async def recognize_spot(image: UploadFile = File(..., description="景区照片")):
    """Recognize scenic spot from uploaded photo and provide narration"""
    # Read and encode image
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

    image_base64 = base64.b64encode(contents).decode("utf-8")

    # Get knowledge base context for better recognition
    context = await rag_service.get_context("景点介绍 景区景点名称", top_k=5)

    # Call LLM vision
    import json
    result_text = await llm_service.recognize_spot_from_image(image_base64, context)

    # Parse result
    try:
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(result_text)
    except json.JSONDecodeError:
        logger.warning(f"Vision result not valid JSON: {result_text[:200]}")
        data = {
            "spot_name": "景点",
            "description": result_text[:500] if result_text else "图片识别完成",
            "history": "",
            "tips": "",
        }

    return VisionRecognizeResponse(
        spot_name=data.get("spot_name", "未知景点"),
        description=data.get("description", ""),
        history=data.get("history", ""),
        tips=data.get("tips", ""),
    )


@router.post("/describe")
async def describe_image(image: UploadFile = File(..., description="景区照片")):
    """Simple image description endpoint"""
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

    image_base64 = base64.b64encode(contents).decode("utf-8")

    result_text = await llm_service.recognize_spot_from_image(image_base64)

    return {"description": result_text}
