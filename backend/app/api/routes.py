import logging
import os
import json
import asyncio
import zipfile
import io
import aiohttp
import uuid
from typing import Any
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
    import time

    try:
        start_time = time.time()  # 记录开始时间

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

        # 确保 processed 目录存在
        ensure_directory(AUDIO_PROCESSED_DIR)

        converted_path, duration = await convert_to_wav(uploaded_file_path, processed_file_path)
        
        await task_manager.update_task(
            task_id, progress=50.0, message="正在进行语音识别..."
        )

        logger.info(f"Starting transcription for task {task_id}")

        # 获取当前事件循环
        loop = asyncio.get_running_loop()
        logger.info(f"Got event loop: {loop}")

        # 执行 Whisper 识别，传递进度回调
        def progress_callback(progress: float):
            try:
                logger.info(f"Progress callback called: {progress}%")
                asyncio.run_coroutine_threadsafe(
                    task_manager.update_task(
                        task_id, progress=progress, message=f"正在进行语音识别... ({int(progress)}%)"
                    ),
                    loop
                )
            except Exception as e:
                logger.error(f"Failed to update progress: {e}", exc_info=True)

        asr_result = whisper_service.transcribe(converted_path, progress_callback=progress_callback)

        logger.info(f"Transcription completed for task {task_id}")

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

        # 计算处理时间（在保存之前）
        processing_time = time.time() - start_time
        result_data["processing_time"] = round(processing_time, 2)

        # 保存结果到文件
        result_filename = f"{result_id}.json"
        result_file_path = os.path.join(RESULTS_DIR, result_filename)

        # 确保 results 目录存在
        ensure_directory(RESULTS_DIR)

        await asyncio.to_thread(json.dump, result_data, open(result_file_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

        # 复制处理后的音频文件到 results 目录
        audio_output_path = os.path.join(RESULTS_DIR, f"{result_id}_audio.wav")
        await asyncio.to_thread(os.rename, converted_path, audio_output_path)

        await task_manager.update_task(
            task_id,
            status="completed",
            progress=100.0,
            message=f"识别完成 (耗时 {processing_time:.2f}秒)",
            result_id=result_id
        )

        logger.info(f"任务 {task_id} 处理完成，结果ID: {result_id}，耗时 {processing_time:.2f}秒")
        
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
    """下载识别结果 JSON 和音频文件的 ZIP 压缩包"""
    result_file = os.path.join(RESULTS_DIR, f"{result_id}.json")
    audio_file = os.path.join(RESULTS_DIR, f"{result_id}_audio.wav")

    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    if not os.path.exists(audio_file):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    # 创建内存中的 ZIP 文件
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 添加 JSON 文件
        with open(result_file, 'rb') as f:
            zip_file.writestr(f"{result_id}.json", f.read())
        # 添加音频文件
        with open(audio_file, 'rb') as f:
            zip_file.writestr(f"{result_id}_audio.wav", f.read())

    zip_buffer.seek(0)

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            'Content-Disposition': f'attachment; filename="{result_id}_result.zip"'
        }
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
            updated_sentences = update_data["sentences"]
            original_sentences = result_data["sentences"]

            # 检查是否为合并操作（句子数量减少）
            is_merge_operation = len(updated_sentences) < len(original_sentences)

            # 标记已处理的原句子索引（用于合并场景）
            processed_original_indices = set()

            for i, new_sentence in enumerate(updated_sentences):
                text_changed = False
                matching_original_idx = None

                # 尝试找到匹配的原句子（通过文本精确匹配）
                for j, old_sentence in enumerate(original_sentences):
                    if j in processed_original_indices:
                        continue

                    if new_sentence["text"] == old_sentence["text"]:
                        # 找到精确匹配的原句子
                        matching_original_idx = j
                        text_changed = False
                        processed_original_indices.add(j)
                        break

                if matching_original_idx is None:
                    # 未找到精确匹配，说明是新的合并分句，需要翻译
                    text_changed = True

                if text_changed:
                    # 新分句或文本被修改，需要重新翻译
                    translation = translation_service.translate_segment(
                        new_sentence["text"],
                        source_lang="auto"
                    )
                    new_sentence["translation"] = translation
                elif matching_original_idx is not None:
                    # 保留原有翻译
                    old_sentence = original_sentences[matching_original_idx]
                    if "translation" in old_sentence:
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


@router.post("/import")
async def import_result(
    json_file: UploadFile = File(..., description="JSON 结果文件"),
    audio_file: UploadFile = File(..., description="对应的音频文件")
):
    """导入 JSON 结果和音频文件"""
    # 生成新的 result_id
    result_id = generate_result_id()

    try:
        # 读取并验证 JSON 文件
        json_content = await json_file.read()
        result_data = json.loads(json_content)

        # 验证 JSON 结构
        required_fields = ["sentences", "speakers", "total_duration"]
        for field in required_fields:
            if field not in result_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"JSON 文件缺少必需字段: {field}"
                )

        # 保存 JSON 文件
        json_file_path = os.path.join(RESULTS_DIR, f"{result_id}.json")
        # 更新 result_id
        result_data["result_id"] = result_id
        # 更新时间戳
        result_data["timestamp"] = get_current_timestamp()
        result_data["updated_timestamp"] = get_current_timestamp()

        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        # 保存音频文件
        if audio_file.filename:
            _ = os.path.splitext(audio_file.filename)[1].lower()

        audio_filename = f"{result_id}_audio.wav"

        # 读取音频文件内容
        audio_content = await audio_file.read()
        audio_file_path = os.path.join(RESULTS_DIR, audio_filename)

        # 保存音频文件
        with open(audio_file_path, 'wb') as f:
            f.write(audio_content)

        logger.info(f"成功导入结果 {result_id}")

        return {
            "success": True,
            "message": "导入成功",
            "result_id": result_id
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON 文件格式错误")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/download-url", response_model=TaskStatus)
async def download_audio_from_url(
    background_tasks: BackgroundTasks,
    url: str = None
):
    """从 URL 下载音频文件并启动识别任务"""
    
    if not url:
        raise HTTPException(status_code=400, detail="请提供音频 URL")
    
    # 生成文件名
    original_filename = f"downloaded_{uuid.uuid4().hex[:8]}"
    
    try:
        # 下载音频文件
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"下载失败，HTTP 状态码: {response.status}"
                    )
                
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '')
                if not any(ct in content_type for ct in ['audio', 'octet-stream']):
                    logger.warning(f"内容类型可能不是音频: {content_type}")
                
                # 读取文件内容
                content = await response.read()
                
                # 验证文件大小
                if len(content) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                
                # 根据内容类型确定扩展名
                file_ext = '.mp3'  # 默认使用 mp3
                if 'wav' in content_type:
                    file_ext = '.wav'
                elif 'm4a' in content_type:
                    file_ext = '.m4a'
                elif 'ogg' in content_type:
                    file_ext = '.ogg'
                
                original_filename = original_filename + file_ext
                
                # 保存下载的文件
                file_path = os.path.join(UPLOAD_DIR, original_filename)
                ensure_directory(UPLOAD_DIR)
                
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
            original_filename,
            file_path
        )
        
        logger.info(f"从 {url} 下载音频成功，任务ID: {task_id}")
        
        return TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            message="音频下载成功，开始处理"
        )
        
    except aiohttp.ClientError as e:
        logger.error(f"下载音频失败: {e}")
        raise HTTPException(status_code=400, detail=f"下载音频失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理 URL 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理 URL 失败: {str(e)}")
