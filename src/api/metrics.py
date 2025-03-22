from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from ..core.monitor import NetworkMonitor
from ..core.optimizer import PerformanceOptimizer
from ..models.metrics import MetricsResponse, MetricsHistoryResponse

router = APIRouter()
monitor = NetworkMonitor()
optimizer = PerformanceOptimizer()

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    获取实时监控指标
    """
    try:
        # 收集指标数据
        metrics = await monitor.collect_metrics()
        
        # 优化数据
        optimized_metrics = optimizer.optimize_data(metrics)
        
        # 缓存数据
        optimizer.cache_metrics(optimized_metrics)
        
        return optimized_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/history", response_model=List[MetricsHistoryResponse])
async def get_metrics_history(
    start_time: int,
    end_time: int,
    interval: Optional[int] = 60
):
    """
    获取历史监控指标
    
    Args:
        start_time: 开始时间戳(毫秒)
        end_time: 结束时间戳(毫秒)
        interval: 数据间隔(秒),默认60秒
    """
    try:
        # 从InfluxDB获取历史数据
        history_data = await monitor.get_historical_metrics(
            start_time=datetime.fromtimestamp(start_time/1000),
            end_time=datetime.fromtimestamp(end_time/1000),
            interval=interval
        )
        
        # 优化查询结果
        optimized_data = optimizer.optimize_query(history_data)
        
        return optimized_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/export")
async def export_metrics(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    format: str = "csv"
):
    """
    导出监控指标数据
    
    Args:
        start_time: 开始时间戳(毫秒)
        end_time: 结束时间戳(毫秒)
        format: 导出格式(csv/excel)
    """
    try:
        # 如果没有指定时间范围,默认导出最近24小时的数据
        if not start_time or not end_time:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - 24 * 60 * 60 * 1000
            
        # 获取历史数据
        history_data = await monitor.get_historical_metrics(
            start_time=datetime.fromtimestamp(start_time/1000),
            end_time=datetime.fromtimestamp(end_time/1000)
        )
        
        # 优化数据
        optimized_data = optimizer.optimize_query(history_data)
        
        # 根据格式处理数据
        if format == "csv":
            return await export_to_csv(optimized_data)
        elif format == "excel":
            return await export_to_excel(optimized_data)
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def export_to_csv(data: List[dict]):
    """
    导出为CSV格式
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    headers = [
        "时间",
        "响应时间(ms)",
        "连接数",
        "错误率(%)",
        "带宽使用(MB/s)",
        "SSL状态",
        "CPU使用率(%)",
        "内存使用率(%)",
        "磁盘使用率(%)"
    ]
    writer.writerow(headers)
    
    # 写入数据
    for item in data:
        writer.writerow([
            item["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            item["response_time"],
            item["connection_count"],
            f"{item['error_rate']*100:.2f}",
            f"{item['bandwidth']/1000000:.2f}",
            "正常" if item["ssl_status"]["valid"] else "异常",
            item["resources"]["cpu_percent"],
            item["resources"]["memory_percent"],
            item["resources"]["disk_percent"]
        ])
    
    return output.getvalue()

async def export_to_excel(data: List[dict]):
    """
    导出为Excel格式
    """
    import pandas as pd
    from io import BytesIO
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    # 处理数据格式
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["error_rate"] = df["error_rate"].apply(lambda x: f"{x*100:.2f}%")
    df["bandwidth"] = df["bandwidth"].apply(lambda x: f"{x/1000000:.2f}")
    df["ssl_status"] = df["ssl_status"].apply(lambda x: "正常" if x["valid"] else "异常")
    
    # 重命名列
    df.columns = [
        "时间",
        "响应时间(ms)",
        "连接数",
        "错误率",
        "带宽使用(MB/s)",
        "SSL状态",
        "CPU使用率(%)",
        "内存使用率(%)",
        "磁盘使用率(%)"
    ]
    
    # 导出为Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="监控数据")
        
        # 获取工作表
        worksheet = writer.sheets["监控数据"]
        
        # 调整列宽
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.set_column(idx, idx, max_length + 2)
    
    output.seek(0)
    return output.getvalue() 