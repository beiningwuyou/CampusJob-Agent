# 贡献指南 (Contributing Guide)

感谢你关注并愿意为 **CampusJob-Agent** 贡献力量！无论是修复 Bug、完善文档、改进算法，还是增加新的招聘源解析适配器，我们都非常欢迎。

---

## 1. 本地开发环境准备

项目采用 [uv](https://github.com/astral-sh/uv) 进行高效的 Python 虚拟环境与依赖管理。

1. **Fork 并克隆仓库**：
   ```bash
   git clone https://github.com/beiningwuyou/CampusJob-Agent.git
   cd CampusJob-Agent
   ```

2. **安装依赖与同步环境**：
   ```bash
   uv sync
   ```

3. **配置本地开发环境变量**：
   ```bash
   cp .env.example .env
   ```

4. **一键导入开箱即用的脱敏演示数据**：
   ```bash
   uv run python scripts/seed_demo_data.py
   ```

5. **启动开发服务**：
   - 启动 FastAPI 后端及 Web 工作台：
     ```bash
     uv run uvicorn app.main:app --reload --port 8000
     ```
   - 或启动轻量原生桌面应用：
     ```bash
     ./run_desktop.sh
     ```

---

## 2. 代码规范与质量保障

为了保证项目代码整洁与质量一致，请在提交代码前遵守以下约定：

1. **代码检查与格式化**：
   项目采用 [Ruff](https://github.com/astral-sh/ruff) 进行代码检查：
   ```bash
   uv run ruff check .
   ```

2. **运行全量自动化测试**：
   确保所有单元测试与集成测试通过：
   ```bash
   uv run pytest -v
   ```

3. **发布前安全看门狗核验**：
   在执行提交前，务必运行项目内置的隐私与脱敏检查脚本：
   ```bash
   bash scripts/pre_publish_check.sh
   ```

---

## 3. 隐私与数据隔离原则 (Strict Privacy Rules)

**请严格注意**：
- 严禁将包含真实姓名、联系方式或特定个人身份的简历、数据库文件 (`data/*.db`) 提交至 Git。
- 涉及测试的数据请严格使用虚拟人物（如“张小明”）与脱敏样例。
- 严禁在代码或脚本中硬编码任何绝对私有路径（如 `/Users/xxx`）或真实的 API Key / 邮箱授权码。

---

## 4. 提交 Pull Request 流程

1. 基于 `main` 分支创建功能分支：
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. 提交清晰规范的 Commit 信息：
   ```bash
   git commit -m "feat: 添加某高校就业网双轨公告解析适配器"
   ```
3. 推送至你的远端仓库：
   ```bash
   git push origin feature/amazing-feature
   ```
4. 在 GitHub 提出 Pull Request，并在描述中详述改动动机与测试结果。
