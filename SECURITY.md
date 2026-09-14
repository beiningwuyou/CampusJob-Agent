# 安全政策与隐私保护规范 (Security & Privacy Policy)

**CampusJob-Agent** 是一款以「Local-First 隐私优先」为核心设计理念的应届生求职协同系统。我们深知求职者的个人简历与投递记录属于高度敏感的个人隐私数据，因此在架构设计层面实施了严格的隐私防护边界。

---

## 1. 核心安全与隐私保障架构

1. **本地私有存储 (Local-First Data Isolation)**：
   - 所有的求职记录、意向岗位、日程事件及配置数据均保存在用户本机的 SQLite (`data/campus_job.db`) 中，绝不经由任何第三方中心化服务器中转。
2. **零明文上云的本地脱敏沙箱 (PrivacySanitizer Sandbox)**：
   - 在将简历发送至大语言模型（LLM）进行岗位契合度匹配或诊断之前，系统在本地通过正则与 AES 密钥算子将候选人姓名、手机号、电子邮箱、身份证号及院校名称替换为抽象混淆占位符（如 `[CANDIDATE_NAME]`, `[PHONE_1]`）。
   - 外部 LLM 提供商仅接收脱敏后的经历与技能摘要，绝无触碰明文个人身份的可能。
3. **敏感凭据本地加密 (Credential Encryption)**：
   - 本地保存的 LLM API Key、SMTP 邮箱密码等凭据，均采用本地派生密钥进行 AES-256 加密存储。

---

## 2. 漏洞报告渠道 (Reporting a Vulnerability)

如果你在项目中发现了安全缺陷、脱敏遗漏或潜在漏洞，请**不要**在 GitHub 公开创建 Issue。

请通过以下方式私下与维护者取得联系：
- 提交邮件至维护者或在项目安全专区发起私密漏洞通告（GitHub Private Vulnerability Reporting）。
- 我们会在 48 小时内确认并评估漏洞，并在修复后发布安全补丁更新。
