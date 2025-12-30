from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from app.api.routes import router
from app.api.history import router as history_router
from app.core.config import UPLOAD_DIR, RESULTS_DIR, AUDIO_PROCESSED_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Whisper ASR API",
    description="基于 Whisper 和 WhisperX 的语音识别服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(history_router)


@app.get("/")
async def root():
    return JSONResponse({
        "service": "Whisper ASR API",
        "version": "1.0.0",
        "status": "running"
    })


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "upload_dir": UPLOAD_DIR,
        "results_dir": RESULTS_DIR,
        "processed_dir": AUDIO_PROCESSED_DIR
    }


@app.on_event("startup")
async def startup_event():
    logger.info("正在启动 Whisper ASR 服务...")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(AUDIO_PROCESSED_DIR, exist_ok=True)
    logger.info(f"上传目录: {UPLOAD_DIR}")
    logger.info(f"结果目录: {RESULTS_DIR}")
    logger.info(f"处理目录: {AUDIO_PROCESSED_DIR}")
    logger.info("Whisper ASR 服务启动完成!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Whisper ASR 服务正在关闭...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
