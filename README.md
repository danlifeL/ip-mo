# IP 监控系统

一个基于 FastAPI 和 Vue.js 的实时 IP 监控系统，提供全面的网络性能监控、资源使用监控和告警管理功能。

## 功能特点

- 实时监控
  - 响应时间监控
  - 连接数统计
  - 错误率分析
  - 带宽使用监控
  - 资源使用监控（CPU、内存、磁盘）
  - SSL 证书状态监控

- 数据可视化
  - 实时数据图表
  - 历史数据趋势
  - 资源使用分布
  - 多维度数据分析

- 告警管理
  - 多级别告警（警告、严重、紧急）
  - 告警规则配置
  - 告警通知（邮件、Webhook、Slack）
  - 告警历史记录

- 系统设置
  - 监控参数配置
  - 告警阈值设置
  - 通知渠道配置
  - 系统日志管理

## 技术栈

### 后端
- Python 3.8+
- FastAPI
- SQLAlchemy
- APScheduler
- psutil
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- aiofiles
- uvicorn

### 前端
- Vue 3
- Element Plus
- ECharts
- Axios
- Moment.js
- XLSX

## 系统要求

- Python 3.8 或更高版本
- Node.js 14 或更高版本
- MySQL 5.7 或更高版本
- Redis 6.0 或更高版本

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/danlifeL/ip-mo.git
cd ip-mo
```

### 2. 后端设置

1. 创建并激活虚拟环境：

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

2. 安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

3. 配置环境变量：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=ip_monitor

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT配置
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 邮件配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
```

4. 初始化数据库：

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE ip_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行数据库迁移
alembic upgrade head
```

### 3. 前端设置

1. 安装依赖：

```bash
cd frontend
npm install
```

2. 配置环境变量：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置API地址
VITE_API_BASE_URL=http://localhost:8000/api
```

### 4. 启动服务

1. 启动后端服务：

```bash
# 开发环境
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

2. 启动前端服务：

```bash
# 开发环境
npm run dev

# 生产环境
npm run build
npm run preview
```

## 部署说明

### Docker 部署

1. 构建镜像：

```bash
# 构建后端镜像
docker build -t ip-monitor-backend -f backend/Dockerfile .

# 构建前端镜像
docker build -t ip-monitor-frontend -f frontend/Dockerfile .
```

2. 使用 Docker Compose 启动服务：

```bash
docker-compose up -d
```

### Nginx 配置

```nginx
# /etc/nginx/conf.d/ip-monitor.conf

server {
    listen 80;
    server_name your_domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 使用说明

### 1. 访问系统

- 开发环境：http://localhost:5173
- 生产环境：http://your_domain.com

### 2. 默认账号

- 管理员账号：admin
- 默认密码：admin123

### 3. 主要功能

1. 监控面板
   - 实时数据概览
   - 性能指标图表
   - 资源使用统计

2. 告警管理
   - 告警规则配置
   - 告警通知设置
   - 告警历史查看

3. 系统设置
   - 监控参数配置
   - 系统日志查看
   - 用户权限管理

## 开发指南

### 目录结构

```
ip-monitor/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── alembic.ini
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── router/
│   │   ├── store/
│   │   ├── utils/
│   │   ├── views/
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

### 开发流程

1. 后端开发
   - 在 `backend/app/api` 中添加新的 API 路由
   - 在 `backend/app/models` 中定义数据模型
   - 在 `backend/app/services` 中实现业务逻辑
   - 在 `backend/tests` 中编写单元测试

2. 前端开发
   - 在 `frontend/src/views` 中添加新的页面组件
   - 在 `frontend/src/components` 中添加可复用组件
   - 在 `frontend/src/api` 中添加 API 调用方法
   - 在 `frontend/src/store` 中管理状态

## 常见问题

1. 数据库连接失败
   - 检查数据库配置是否正确
   - 确保数据库服务正在运行
   - 验证数据库用户权限

2. Redis 连接失败
   - 检查 Redis 服务是否运行
   - 验证 Redis 密码是否正确
   - 确认 Redis 端口是否开放

3. 前端 API 请求失败
   - 检查 API 地址配置
   - 确认后端服务是否运行
   - 验证跨域配置是否正确

## 更新日志

### v1.0.0 (2024-03-20)
- 初始版本发布
- 实现基本监控功能
- 支持告警管理
- 提供系统设置

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License 
