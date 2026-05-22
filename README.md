
# AI Technology English Reading Coach

一个专为AI产品经理打造的科技英语阅读教练，帮助你在100天内突破科技英语阅读障碍。

## 功能特性

- 📚 **单词本管理** - 自动记录陌生单词，支持5次正确后自动淘汰
- 📰 **每日阅读推送** - 从GitHub Blog等平台精选科技文章
- 🎯 **阅读训练** - 分段学习 + 实时单词查询 + 长难句解析
- 📊 **学习统计** - 自动生成周度学习报告
- 🔗 **多端支持** - 支持飞书机器人和Trae IDE Agent两种使用方式

## 快速开始

### 环境要求

- Python 3.10+
- 飞书账号（用于Bitable存储）
- 豆包API Key

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/your-username/english-reading-agent.git
cd english-reading-agent
```

2. **安装依赖**

```bash
pip install -e .
```

3. **配置环境变量**

复制 `.env.example` 为 `.env` 并填写相关配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 豆包 API 配置
DOUBAO_API_KEY=your_doubao_api_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=ep-20240422225026-7lw7k

# 飞书应用配置
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_VERIFICATION_TOKEN=your_verification_token
FEISHU_ENCRYPT_KEY=your_encrypt_key

# 飞书多维表格配置
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_WORDBOOK_TABLE_ID=your_wordbook_table_id
FEISHU_READING_TABLE_ID=your_reading_table_id
FEISHU_CONFIG_TABLE_ID=your_config_table_id
```

### 使用方式

#### 1. 作为Trae IDE Agent使用

1. 在Trae中打开项目目录
2. Trae会自动识别 `.trae/mcp.json` 配置并启动MCP服务
3. 在Trae中创建自定义智能体，绑定 `english-reading-coach` skill和MCP工具
4. 开始对话使用！

#### 2. 作为飞书机器人使用

```bash
python -m src.main
```

然后配置飞书机器人的事件订阅地址为：`https://your-domain.com/webhook/feishu`

## 飞书多维表格配置

你需要在飞书中创建3个多维表格：

### 1. 单词本 (wordbook)

字段：
- `user_id` (多行文本) - 用户唯一标识
- `word` (多行文本) - 单词
- `definition` (多行文本) - 释义
- `phonetic` (多行文本) - 音标
- `correct_count` (数字) - 正确次数
- `wrong_count` (数字) - 错误次数
- `created_at` (日期) - 创建时间
- `reviewed_at` (日期) - 最后复习时间
- `status` (单选) - 状态 (active/eliminated)

### 2. 阅读记录 (reading_records)

字段：
- `user_id` (多行文本) - 用户唯一标识
- `content_title` (多行文本) - 文章标题
- `content_url` (多行文本) - 文章链接
- `read_date` (日期) - 阅读日期
- `new_words` (多行文本) - 新学单词
- `understanding_score` (数字) - 理解评分
- `completed` (复选) - 是否完成
- `created_at` (日期) - 创建时间

### 3. 用户配置 (user_config)

字段：
- `user_id` (多行文本) - 用户唯一标识
- `daily_reading_enabled` (复选) - 是否启用每日推送
- `daily_push_time` (多行文本) - 每日推送时间
- `reading_level` (单选) - 阅读水平 (beginner/intermediate/advanced)
- `interest_topics` (多选) - 感兴趣话题
- `created_at` (日期) - 创建时间
- `updated_at` (日期) - 更新时间

## 项目结构

```
english-reading-agent/
├── src/
│   ├── core/              # 核心业务逻辑
│   ├── storage/           # 存储层（Bitable）
│   ├── adapters/          # 适配器（飞书Bot、Trae）
│   ├── scheduler/         # 定时任务
│   ├── config/            # 配置管理
│   ├── main.py            # FastAPI入口
│   └── mcp_server.py      # MCP服务
├── config/prompts/        # LLM提示词模板
├── .trae/                 # Trae配置
├── pyproject.toml         # 项目配置
└── README.md
```

## 开发计划

- [ ] 支持更多LLM（OpenAI GPT、Claude等）
- [ ] 支持更多RSS源（Medium、Hacker News等）
- [ ] 增加单词听写功能
- [ ] 增加阅读笔记功能
- [ ] 支持多人学习小组
- [ ] 增加数据导出功能

## 贡献指南

欢迎提交 Issue 和 Pull Request！详细请参考 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](./LICENSE) 文件。

## 联系方式

如有问题，欢迎提交 Issue 或联系作者。
