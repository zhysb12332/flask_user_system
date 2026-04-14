# Flask 用户系统（移动端友好 + 100% 测试覆盖 + VPS 自动部署）

## 功能说明
- 用户注册：`POST /api/v1/auth/register`
- 用户登录：`POST /api/v1/auth/login`
- 当前用户信息：`GET /api/v1/auth/me`
- 退出登录：`POST /api/v1/auth/logout`
- 健康检查：`GET /api/v1/health`

接口全部返回 JSON，适合 Android/iOS/H5 小程序直接调用；同时支持：
- Cookie 会话（Web 端）
- Bearer Token（移动端/前后端分离）

## 在 PyCharm 使用虚拟环境（推荐）
1. 打开项目 `flask_user_system`
2. 进入 `Settings -> Project -> Python Interpreter`
3. 点击 `Add Interpreter -> Add Local Interpreter -> Virtualenv`
4. 选择 `New`，例如 `.venv`，并确认创建
5. 在 PyCharm Terminal 执行：
```bash
python -m pip install -r requirements.txt
```

## 本地运行
```bash
pip install -r requirements.txt
python run.py
```

## 运行测试（100% 覆盖率）
```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
pytest
```

如果你在 PyCharm 的 Run Configuration 里运行 `pytest`，建议在 `Environment variables` 增加：
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`

`pytest.ini` 已启用：
- `--cov=app`
- `--cov-fail-under=100`

## Docker 部署
```bash
docker compose up -d --build
```

## AI 自动化部署到 VPS
### 1) VPS 首次准备
```bash
sudo mkdir -p /opt/flask_user_system
sudo chown -R $USER:$USER /opt/flask_user_system
```

把本项目上传后，确保有可执行权限：
```bash
chmod +x scripts/deploy_vps.sh
```

### 2) GitHub Secrets 配置
- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `REPO_URL`

### 3) 自动流程
`main` 分支 push 时：
1. GitHub Actions 先执行测试并校验覆盖率 100%
2. 测试通过后自动 SSH 到 VPS
3. 执行 `scripts/deploy_vps.sh` 拉最新代码并重建容器

### 4) AI 决策式部署（可选）
在 VPS 项目目录执行：
```bash
python scripts/ai_deploy.py --changed-files 12
```
脚本会根据变更规模自动选择重启策略，并在健康检查失败时自动回滚重建。

## 什么是 VPS 服务器？
VPS（Virtual Private Server，虚拟专用服务器）是云厂商把一台物理服务器虚拟成多台“独立小服务器”后分配给你的实例。  
它有独立公网 IP、独立系统环境、可远程 SSH 登录，像一台你自己的 Linux 服务器。  
通常用来部署网站、后端 API、数据库、定时任务等。
auto-deploy-test
