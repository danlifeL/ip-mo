import os
import yaml
import time
import threading
from datetime import datetime
from loguru import logger
from flask import Flask, jsonify
from prometheus_client import start_http_server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import metrics

from core.monitor import NetworkMonitor
from core.alert import AlertSystem
from core.optimizer import PerformanceOptimizer

# 配置日志
logger.add(
    "logs/monitor.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# 加载配置
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/app/config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 创建Flask应用
app = Flask(__name__)

# 全局变量
config = load_config()
monitor = NetworkMonitor(config)
alert_system = AlertSystem(config)
optimizer = PerformanceOptimizer(config)

def monitor_loop():
    """监控循环"""
    while True:
        try:
            # 收集指标
            metrics = monitor.collect_metrics()
            
            # 优化性能
            optimized_metrics = optimizer.optimize_performance(metrics)
            
            # 检查告警
            alerts = alert_system.check_alerts(optimized_metrics)
            
            # 发送告警通知
            if alerts:
                alert_system.send_notifications(alerts)
            
            # 清理资源
            optimizer.cleanup()
            
            # 等待下一次检查
            time.sleep(config['monitoring']['interval'])
            
        except Exception as e:
            logger.error(f"Error in monitor loop: {str(e)}")
            time.sleep(5)  # 发生错误时等待5秒

@app.route('/api/metrics')
def get_metrics():
    """获取当前指标"""
    try:
        metrics = monitor.collect_metrics()
        optimized_metrics = optimizer.optimize_performance(metrics)
        return jsonify(optimized_metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """获取告警历史"""
    try:
        alerts = alert_system.get_alert_history()
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        status = {
            'monitor': {
                'is_running': True,
                'last_check': datetime.utcnow().isoformat()
            },
            'alerts': {
                'active_count': len([a for a in alert_system.get_alert_history() if a['status'] == 'active'])
            },
            'resources': optimizer.monitor_resources()
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def main():
    """主函数"""
    try:
        # 启动Prometheus指标服务器
        start_http_server(9090)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 启动Flask应用
        app.run(
            host=config['api']['host'],
            port=config['api']['port'],
            debug=config['api']['debug']
        )
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == '__main__':
    main()

# 创建FastAPI主应用文件
app = FastAPI(
    title="IP监控系统",
    description="实时监控网络性能和安全的API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(metrics.router, prefix="/api", tags=["metrics"])

@app.get("/")
async def root():
    return {
        "message": "IP监控系统API服务",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 