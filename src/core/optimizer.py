import time
from typing import Dict, List, Optional
from loguru import logger
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import numpy as np
from datetime import datetime, timedelta

class PerformanceOptimizer:
    def __init__(self, config: Dict):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cache = {}
        self._cache_ttl = 60  # 缓存有效期（秒）
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 清理间隔（秒）

    @lru_cache(maxsize=1000)
    def get_cached_metrics(self, metric_type: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取缓存的指标数据"""
        cache_key = f"{metric_type}_{start_time.timestamp()}_{end_time.timestamp()}"
        if cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if time.time() - cache_data['timestamp'] < self._cache_ttl:
                return cache_data['data']
        return []

    def cache_metrics(self, metric_type: str, data: List[Dict], start_time: datetime, end_time: datetime):
        """缓存指标数据"""
        cache_key = f"{metric_type}_{start_time.timestamp()}_{end_time.timestamp()}"
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }

    def optimize_query(self, query: str) -> str:
        """优化查询语句"""
        # 添加时间范围限制
        if 'range' not in query:
            query = f"{query} |> range(start: -1h)"
        
        # 添加聚合操作
        if 'aggregate' not in query:
            query = f"{query} |> aggregateWindow(every: 1m, fn: mean)"
        
        return query

    def batch_process(self, data: List[Dict], batch_size: int = 1000) -> List[Dict]:
        """批量处理数据"""
        results = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            processed_batch = self._process_batch(batch)
            results.extend(processed_batch)
        return results

    def _process_batch(self, batch: List[Dict]) -> List[Dict]:
        """处理数据批次"""
        # 使用线程池并行处理
        futures = []
        for item in batch:
            future = self.executor.submit(self._process_item, item)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch item: {str(e)}")
        
        return results

    def _process_item(self, item: Dict) -> Dict:
        """处理单个数据项"""
        # 添加处理时间戳
        item['processed_at'] = datetime.utcnow()
        
        # 数据清洗
        if 'value' in item and isinstance(item['value'], (int, float)):
            item['value'] = round(item['value'], 2)
        
        return item

    def optimize_storage(self, data: List[Dict]) -> List[Dict]:
        """优化存储数据"""
        # 压缩数据
        compressed_data = self._compress_data(data)
        
        # 删除冗余字段
        cleaned_data = self._clean_data(compressed_data)
        
        return cleaned_data

    def _compress_data(self, data: List[Dict]) -> List[Dict]:
        """压缩数据"""
        compressed = []
        for item in data:
            compressed_item = {
                't': item['timestamp'],  # 时间戳
                'v': item['value'],      # 值
                't': item['type']        # 类型
            }
            compressed.append(compressed_item)
        return compressed

    def _clean_data(self, data: List[Dict]) -> List[Dict]:
        """清理数据"""
        cleaned = []
        for item in data:
            # 删除空值字段
            cleaned_item = {k: v for k, v in item.items() if v is not None}
            cleaned.append(cleaned_item)
        return cleaned

    def monitor_resources(self) -> Dict:
        """监控系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': datetime.utcnow()
        }

    def cleanup(self):
        """清理资源"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            # 清理过期缓存
            self._cleanup_cache()
            self._last_cleanup = current_time

    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._cache.items()
            if current_time - data['timestamp'] > self._cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]

    def optimize_performance(self, metrics: Dict) -> Dict:
        """优化性能指标"""
        optimized = {}
        
        # 计算移动平均
        if 'values' in metrics:
            values = np.array(metrics['values'])
            window_size = min(5, len(values))
            if window_size > 1:
                optimized['moving_average'] = np.mean(values[-window_size:])
        
        # 计算趋势
        if 'values' in metrics and len(metrics['values']) > 1:
            values = np.array(metrics['values'])
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            optimized['trend'] = slope
        
        return optimized

    def __del__(self):
        """清理资源"""
        self.executor.shutdown(wait=True) 