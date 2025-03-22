import time
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
import smtplib
from email.mime.text import MIMEText
import requests
import json

class AlertSystem:
    def __init__(self, config: Dict):
        self.config = config
        self.alert_history = []
        self.alert_rules = self._load_alert_rules()
        self.notification_channels = self._init_notification_channels()

    def _load_alert_rules(self) -> Dict:
        """加载告警规则"""
        return {
            'response_time': {
                'threshold': float(self.config['alerts']['thresholds']['response_time'].replace('ms', '')) / 1000,
                'duration': 300,  # 5分钟
                'severity': 'warning'
            },
            'error_rate': {
                'threshold': float(self.config['alerts']['thresholds']['error_rate'].replace('%', '')) / 100,
                'duration': 300,
                'severity': 'critical'
            },
            'connection_count': {
                'threshold': int(self.config['alerts']['thresholds']['connection_count']),
                'duration': 300,
                'severity': 'warning'
            },
            'bandwidth': {
                'threshold': int(self.config['alerts']['thresholds']['bandwidth'].replace('Mbps', '000000')),
                'duration': 300,
                'severity': 'warning'
            }
        }

    def _init_notification_channels(self) -> Dict:
        """初始化通知渠道"""
        channels = {}
        for channel in self.config['alerts']['channels']:
            if channel == 'email':
                channels['email'] = self._send_email
            elif channel == 'webhook':
                channels['webhook'] = self._send_webhook
            elif channel == 'slack':
                channels['slack'] = self._send_slack
        return channels

    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """检查告警条件"""
        alerts = []
        current_time = datetime.utcnow()

        # 检查响应时间
        if metrics['response_time'] > self.alert_rules['response_time']['threshold']:
            alerts.append(self._create_alert(
                'response_time',
                f"响应时间过高: {metrics['response_time']:.2f}s",
                metrics['response_time'],
                current_time
            ))

        # 检查错误率
        if metrics['error_rate'] > self.alert_rules['error_rate']['threshold']:
            alerts.append(self._create_alert(
                'error_rate',
                f"错误率过高: {metrics['error_rate']:.2%}",
                metrics['error_rate'],
                current_time
            ))

        # 检查连接数
        if metrics['connection_count'] > self.alert_rules['connection_count']['threshold']:
            alerts.append(self._create_alert(
                'connection_count',
                f"连接数过高: {metrics['connection_count']}",
                metrics['connection_count'],
                current_time
            ))

        # 检查带宽使用
        total_bandwidth = metrics['bandwidth']['bytes_sent'] + metrics['bandwidth']['bytes_recv']
        if total_bandwidth > self.alert_rules['bandwidth']['threshold']:
            alerts.append(self._create_alert(
                'bandwidth',
                f"带宽使用过高: {total_bandwidth / 1000000:.2f}MB/s",
                total_bandwidth,
                current_time
            ))

        return alerts

    def _create_alert(self, alert_type: str, message: str, value: float, timestamp: datetime) -> Dict:
        """创建告警记录"""
        alert = {
            'id': f"{alert_type}_{int(timestamp.timestamp())}",
            'type': alert_type,
            'message': message,
            'value': value,
            'timestamp': timestamp,
            'severity': self.alert_rules[alert_type]['severity'],
            'status': 'active'
        }
        self.alert_history.append(alert)
        return alert

    def send_notifications(self, alerts: List[Dict]):
        """发送告警通知"""
        for alert in alerts:
            for channel, send_func in self.notification_channels.items():
                try:
                    send_func(alert)
                except Exception as e:
                    logger.error(f"Error sending {channel} notification: {str(e)}")

    def _send_email(self, alert: Dict):
        """发送邮件通知"""
        msg = MIMEText(f"告警类型: {alert['type']}\n"
                      f"告警信息: {alert['message']}\n"
                      f"告警时间: {alert['timestamp']}\n"
                      f"告警级别: {alert['severity']}")
        
        msg['Subject'] = f"[{alert['severity'].upper()}] Nginx监控告警"
        msg['From'] = self.config['alerts']['email']['from']
        msg['To'] = self.config['alerts']['email']['to']

        with smtplib.SMTP(self.config['alerts']['email']['smtp_server']) as server:
            server.starttls()
            server.login(self.config['alerts']['email']['username'],
                        self.config['alerts']['email']['password'])
            server.send_message(msg)

    def _send_webhook(self, alert: Dict):
        """发送Webhook通知"""
        webhook_url = self.config['alerts']['webhook']['url']
        payload = {
            'alert_id': alert['id'],
            'type': alert['type'],
            'message': alert['message'],
            'timestamp': alert['timestamp'].isoformat(),
            'severity': alert['severity']
        }
        
        requests.post(webhook_url, json=payload)

    def _send_slack(self, alert: Dict):
        """发送Slack通知"""
        webhook_url = self.config['alerts']['slack']['webhook_url']
        payload = {
            'text': f"*[{alert['severity'].upper()}] Nginx监控告警*\n"
                   f"类型: {alert['type']}\n"
                   f"信息: {alert['message']}\n"
                   f"时间: {alert['timestamp']}"
        }
        
        requests.post(webhook_url, json=payload)

    def get_alert_history(self, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         alert_type: Optional[str] = None) -> List[Dict]:
        """获取告警历史"""
        filtered_history = self.alert_history

        if start_time:
            filtered_history = [a for a in filtered_history if a['timestamp'] >= start_time]
        if end_time:
            filtered_history = [a for a in filtered_history if a['timestamp'] <= end_time]
        if alert_type:
            filtered_history = [a for a in filtered_history if a['type'] == alert_type]

        return filtered_history

    def clear_alert_history(self, before_time: Optional[datetime] = None):
        """清理告警历史"""
        if before_time:
            self.alert_history = [a for a in self.alert_history if a['timestamp'] > before_time]
        else:
            self.alert_history = [] 