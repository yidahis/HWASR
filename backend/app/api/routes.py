import logging
import os
import json
import asyncio
from typing import Optional, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, Response
from ..models.schemas import ASRResult, TaskStatus
from ..services.whisper_service import WhisperService
from ..services.diarization_service import diarization_service
from ..services.translation_service import translation_service
from ..services.task_manager import task_manager
from ..utils.helpers import (
    generate_result_id,
    get_current_timestamp,
    ensure_directory,
    calculate_audio_hash
)
from ..utils.audio_processor import convert_to_wav
from ..core.config import (
    UPLOAD_DIR, RESULTS_DIR, AUDIO_PROCESSED_DIR,
    ENABLE_DIARIZATION, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ASR"])

# 全局服务实例
whisper_service = None


async def process_audio_task(
    task_id: str,
    original_filename: str,
    uploaded_file_path: str
):
    """后台处理音频识别任务"""
    global whisper_service
    
    try:
        await task_manager.update_task(
            task_id, status="processing", progress=10.0, message="正在初始化..."
        )
        
        # 延迟加载 Whisper 模型
        if whisper_service is None:
            whisper_service = WhisperService()
        
        await task_manager.update_task(
            task_id, progress=30.0, message="正在处理音频..."
        )
        
        # 转换音频格式
        processed_filename = f"{os.path.splitext(original_filename)[0]}_processed.wav"
        processed_file_path = os.path.join(AUDIO_PROCESSED_DIR, processed_filename)
        converted_path, duration = await convert_to_wav(uploaded_file_path, processed_file_path)
        
        await task_manager.update_task(
            task_id, progress=50.0, message="正在进行语音识别..."
        )
        
        # 执行 Whisper 识别
        asr_result = whisper_service.transcribe(converted_path)
        
        await task_manager.update_task(
            task_id, progress=70.0, message="正在进行说话人识别..."
        )
        
        # 说话人分离
        if ENABLE_DIARIZATION:
            segments = diarization_service.assign_speakers(converted_path, asr_result["segments"])
        else:
            for seg in asr_result["segments"]:
                seg["speaker"] = 0
        
        await task_manager.update_task(
            task_id, progress=85.0, message="正在生成结果..."
        )
        
        # 翻译
        segments = translation_service.translate_all(segments)
        
        # 提取所有说话人
        speakers = sorted(list(set(seg.get("speaker", 0) for seg in segments)))
        
        # 计算 audio_hash
        audio_hash = await calculate_audio_hash(converted_path)
        
        # 生成 result_id
        result_id = generate_result_id()
        
        # 构建结果数据结构（符合 demo.json 格式）
        result_data = {
            "success": True,
            "result_id": result_id,
            "text": asr_result["text"],
            "sentences": [],
            "speakers": speakers,
            "total_duration": duration,
            "audio_hash": audio_hash,
            "filename": original_filename,
            "timestamp": get_current_timestamp(),
            "message": "Recognition completed successfully",
            "audio_path": f"{result_id}_audio.wav",
            "updated_timestamp": get_current_timestamp()
        }
        
        # 构建句子列表
        for idx, seg in enumerate(segments):
            sentence = {
                "text": seg["text"],
                "start": seg["start"],
                "end": seg["end"],
                "speaker": seg["speaker"],
                "translation": seg.get("translation", {
                    "zh": "",
                    "en": "",
                    "source_lang": "en"
                })
            }
            result_data["sentences"].append(sentence)
        
        # 保存结果到文件
        result_filename = f"{result_id}.json"
        result_file_path = os.path.join(RESULTS_DIR, result_filename)
        await asyncio.to_thread(json.dump, result_data, open(result_file_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

        # 复制处理后的音频文件到 results 目录
        audio_output_path = os.path.join(RESULTS_DIR, f"{result_id}_audio.wav")
        await asyncio.to_thread(os.rename, converted_path, audio_output_path)
        
        await task_manager.update_task(
            task_id,
            status="completed",
            progress=100.0,
            message="识别完成",
            result_id=result_id
        )
        
        logger.info(f"任务 {task_id} 处理完成，结果ID: {result_id}")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {e}", exc_info=True)
        await task_manager.update_task(
            task_id,
            status="failed",
            message=f"处理失败: {str(e)}"
        )


@router.post("/upload", response_model=TaskStatus)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """上传音频文件并启动识别任务"""
    
    # 验证文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 保存上传的文件
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    ensure_directory(UPLOAD_DIR)
    
    try:
        content = await file.read()
        
        # 验证文件大小
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 生成任务ID
        task_id = generate_result_id()
        
        # 创建任务
        await task_manager.create_task(task_id)
        
        # 启动后台处理
        background_tasks.add_task(
            process_audio_task,
            task_id,
            file.filename,
            file_path
        )
        
        return TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            message="文件上传成功，开始处理"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查询任务状态"""
    task = await task_manager.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.get("/result/{result_id}", response_model=ASRResult)
async def get_result(result_id: str):
    """获取识别结果"""
    result_file = os.path.join(RESULTS_DIR, f"{result_id}.json")
    
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="结果不存在")
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return ASRResult(**result_data)
        
    except Exception as e:
        logger.error(f"读取结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取结果失败: {str(e)}")


@router.get("/audio/{result_id}")
async def get_audio(result_id: str, request: Request):
    """获取识别后的音频文件"""
    audio_file = os.path.join(RESULTS_DIR, f"{result_id}_audio.wav")

    if not os.path.exists(audio_file):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    # 获取文件大小
    file_size = os.path.getsize(audio_file)

    # 检查是否支持 Range 请求
    range_header = None
    if "range" in [h.lower() for h, v in request.headers.items()]:
        for h, v in request.headers.items():
            if h.lower() == "range":
                range_header = v
                break

    if range_header:
        # 处理 Range 请求
        try:
            start, end = parse_range_header(range_header, file_size)
            chunk_size = end - start + 1

            with open(audio_file, 'rb') as f:
                f.seek(start)
                data = f.read(chunk_size)

            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(chunk_size),
            }

            return Response(
                content=data,
                media_type="audio/wav",
                status_code=206,
                headers=headers
            )
        except Exception as e:
            # 如果 Range 解析失败，返回整个文件
            pass

    # 返回整个文件
    return FileResponse(
        audio_file,
        media_type="audio/wav",
        filename=f"{result_id}_audio.wav",
        headers={
            'Accept-Ranges': 'bytes',
        }
    )


def parse_range_header(range_header: str, file_size: int):
    """解析 Range 请求头"""
    range_header = range_header.replace('bytes=', '')
    parts = range_header.split('-')

    start = int(parts[0]) if parts[0] else 0
    end = int(parts[1]) if parts[1] else file_size - 1

    # 确保范围有效
    start = max(0, min(start, file_size - 1))
    end = max(start, min(end, file_size - 1))

    return start, end


@router.get("/download/{result_id}")
async def download_result(result_id: str):
    """下载识别结果 JSON 文件"""
    result_file = os.path.join(RESULTS_DIR, f"{result_id}.json")

    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="结果不存在")

    return FileResponse(
        result_file,
        media_type="application/json",
        filename=f"{result_id}.json"
    )


@router.post("/update/{result_id}")
async def update_result(result_id: str, update_data: dict[str, Any]):
    """更新识别结果并保存到 JSON 文件"""
    result_file = os.path.join(RESULTS_DIR, f"{result_id}.json")

    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="结果不存在")

    try:
        # 读取现有结果
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        # 更新句子列表
        if "sentences" in update_data:
            # 重新翻译被修改的句子
            updated_sentences = update_data["sentences"]
            original_sentences = result_data["sentences"]

            for i, new_sentence in enumerate(updated_sentences):
                # 找到对应的原句子
                if i < len(original_sentences):
                    old_sentence = original_sentences[i]
                    # 检查文本是否被修改
                    if new_sentence["text"] != old_sentence["text"]:
                        # 重新翻译
                        translation = translation_service.translate_segment(
                            new_sentence["text"],
                            source_lang=new_sentence.get("translation", {}).get("source_lang", "auto")
                        )
                        new_sentence["translation"] = translation
                    elif "translation" in old_sentence:
                        # 保留原有翻译
                        new_sentence["translation"] = old_sentence["translation"]

            result_data["sentences"] = updated_sentences
            # 更新 updated_timestamp
            result_data["updated_timestamp"] = get_current_timestamp()

        # 保存更新后的结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"结果 {result_id} 已更新")

        return {"success": True, "message": "更新成功"}

    except Exception as e:
        logger.error(f"更新结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新结果失败: {str(e)}")
