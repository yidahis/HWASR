import logging
import os
import json
from typing import List
from fastapi import APIRouter, HTTPException
from ..models.schemas import ASRResult
from ..core.config import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/list", response_model=List[dict])
async def get_history_list():
    """获取历史记录列表"""
    history_items = []
    
    try:
        if not os.path.exists(RESULTS_DIR):
            return []
        
        # 遍历 results 目录
        for filename in os.listdir(RESULTS_DIR):
            if filename.endswith('.json') and not filename.startswith('.'):
                file_path = os.path.join(RESULTS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 提取元数据
                    result_id = data.get('result_id', filename.replace('.json', ''))
                    speaker_count = len(data.get('speakers', []))
                    text_preview = data.get('text', '')[:100] + '...' if len(data.get('text', '')) > 100 else data.get('text', '')
                    
                    history_items.append({
                        'result_id': result_id,
                        'filename': data.get('filename', filename),
                        'timestamp': data.get('timestamp', ''),
                        'total_duration': data.get('total_duration', 0),
                        'speaker_count': speaker_count,
                        'text_preview': text_preview,
                        'processing_time': data.get('processing_time')  # 添加处理时间
                    })
                except Exception as e:
                    logger.warning(f"读取文件 {filename} 失败: {e}")
                    continue
        
        # 按时间倒序排序
        history_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return history_items
        
    except Exception as e:
        logger.error(f"获取历史记录列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/load/{result_id}", response_model=ASRResult)
async def load_history(result_id: str):
    """加载指定历史记录详情"""
    result_file = os.path.join(RESULTS_DIR, f"{result_id}.json")
    
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return ASRResult(**result_data)
        
    except Exception as e:
        logger.error(f"读取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取历史记录失败: {str(e)}")
