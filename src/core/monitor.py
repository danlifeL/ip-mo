import time
import psutil
import requests
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
from prometheus_client import Counter, Gauge, Histogram
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class NetworkMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.influx_client = InfluxDBClient(
            url=f"http://{config['database']['influxdb']['host']}:{config['database']['influxdb']['port']}",
            token=config['database']['influxdb']['password'],
            org="myorg"
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        
        # Prometheus指标
        self.response_time = Histogram('nginx_response_time_seconds', 'Response time in seconds')
        self.error_rate = Counter('nginx_error_total', 'Total number of errors')
        self.connection_count = Gauge('nginx_connections', 'Number of active connections')
        self.bandwidth_usage = Gauge('nginx_bandwidth_bytes', 'Bandwidth usage in bytes')
        
        # 性能缓存
        self._cache = {}
        self._cache_ttl = 60  # 缓存有效期（秒）

    def collect_metrics(self) -> Dict:
        """收集网络性能指标"""
        try:
            # 获取Nginx状态
            nginx_status = self._get_nginx_status()
            
            # 获取系统网络统计
            net_stats = psutil.net_io_counters()
            
            # 获取SSL证书状态
            ssl_status = self._check_ssl_status()
            
            metrics = {
                'timestamp': datetime.utcnow(),
                'response_time': nginx_status.get('response_time', 0),
                'connection_count': nginx_status.get('active_connections', 0),
                'error_rate': nginx_status.get('error_count', 0),
                'bandwidth': {
                    'bytes_sent': net_stats.bytes_sent,
                    'bytes_recv': net_stats.bytes_recv,
                    'packets_sent': net_stats.packets_sent,
                    'packets_recv': net_stats.packets_recv
                },
                'ssl_status': ssl_status
            }
            
            # 更新Prometheus指标
            self.response_time.observe(metrics['response_time'])
            self.error_rate.inc(metrics['error_rate'])
            self.connection_count.set(metrics['connection_count'])
            self.bandwidth_usage.set(metrics['bandwidth']['bytes_sent'] + metrics['bandwidth']['bytes_recv'])
            
            # 存储到InfluxDB
            self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {}

    def _get_nginx_status(self) -> Dict:
        """获取Nginx状态信息"""
        try:
            response = requests.get('http://localhost/status')
            if response.status_code == 200:
                return self._parse_nginx_status(response.text)
            return {}
        except Exception as e:
            logger.error(f"Error getting Nginx status: {str(e)}")
            return {}

    def _parse_nginx_status(self, status_text: str) -> Dict:
        """解析Nginx状态文本"""
        status = {}
        for line in status_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                status[key.strip()] = value.strip()
        return status

    def _check_ssl_status(self) -> Dict:
        """检查SSL证书状态"""
        try:
            # 实现SSL证书检查逻辑
            return {
                'valid': True,
                'expiry_date': None,
                'issuer': None
            }
        except Exception as e:
            logger.error(f"Error checking SSL status: {str(e)}")
            return {}

    def _store_metrics(self, metrics: Dict):
        """存储指标到InfluxDB"""
        try:
            point = Point("nginx_metrics") \
                .time(metrics['timestamp']) \
                .field("response_time", metrics['response_time']) \
                .field("connection_count", metrics['connection_count']) \
                .field("error_rate", metrics['error_rate']) \
                .field("bytes_sent", metrics['bandwidth']['bytes_sent']) \
                .field("bytes_recv", metrics['bandwidth']['bytes_recv'])
            
            self.write_api.write(bucket="nginx_monitor", record=point)
            
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")

    def get_historical_metrics(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史指标数据"""
        try:
            query = f'''
            from(bucket: "nginx_monitor")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "nginx_metrics")
            '''
            
            result = self.influx_client.query_api().query(query)
            return self._format_query_result(result)
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {str(e)}")
            return []

    def _format_query_result(self, result) -> List[Dict]:
        """格式化查询结果"""
        formatted_data = []
        for table in result:
            for record in table.records:
                formatted_data.append({
                    'timestamp': record.get_time(),
                    'field': record.get_field(),
                    'value': record.get_value()
                })
        return formatted_data

    def cleanup(self):
        """清理资源"""
        self.write_api.close()
        self.influx_client.close() 