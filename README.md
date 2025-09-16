# Telegram 消息转发工具

使用 Pyrogram 实现的 Telegram 消息转发工具，支持通过 Bot 接收消息链接并原样转发消息内容。

## 功能特点

- 🔗 支持多种 Telegram 消息链接格式
- 📨 原样转发完整消息（保持格式和媒体）
- 🤖 通过 Bot 界面操作，简单易用
- 📱 支持各种媒体类型（图片、视频、文档、音频等）
- 🔄 完美保持原消息的所有属性
- ⚡ 快速响应，即时转发

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置设置

1. 复制配置文件模板：
```bash
copy env_example.txt .env
```

2. 编辑 `.env` 文件，填入您的配置：
```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
```

### 获取配置信息

#### API_ID 和 API_HASH
1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 使用您的手机号登录
3. 点击 "API development tools"
4. 创建新应用，获取 `api_id` 和 `api_hash`

#### BOT_TOKEN
1. 在 Telegram 中搜索 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取机器人的 Token

## 使用方法

### 启动程序

**首次运行或迁移session文件**:
```bash
# 迁移现有的session文件到sessions目录
python migrate_sessions.py

# 启动程序
python main.py
```

**正常启动**:
```bash
python main.py
```

### 使用 Bot
1. 在 Telegram 中找到您的 Bot
2. 发送 `/start` 开始使用
3. 直接发送消息链接，Bot 会自动转发原消息

### 支持的链接格式
- `https://t.me/channel_name/123`
- `https://t.me/c/123456789/123`
- `t.me/channel_name/123`

### Bot 命令
- `/start` - 开始使用
- `/help` - 显示帮助信息
- `/status` - 检查服务状态

## 支持的消息类型

- 📝 文本消息（保持原始格式）
- 🖼️ 图片消息（包含说明文字）
- 🎥 视频消息（保持画质和时长）
- 📄 文档文件（保持原文件名和大小）
- 🎵 音频文件（保持标题和演唱者信息）
- 🎙️ 语音消息（保持时长）
- 🎭 贴纸和表情包
- 🎬 GIF 动画
- 📹 视频笔记（圆形视频）

## 注意事项

⚠️ **权限要求**
- 只能转发您有权限访问的消息
- 私人聊天的消息可能无法访问
- 某些受限频道可能需要额外权限
- 转发的消息会失去原始的转发标记

⚠️ **使用限制**
- 请遵守 Telegram 的使用条款
- 不要用于恶意目的
- 尊重他人隐私

## 文件结构

```
tg-forward/
├── main.py              # 主程序入口
├── bot_handler.py       # Bot 消息处理器
├── message_extractor.py # 消息提取核心逻辑
├── config.py           # 配置管理
├── requirements.txt    # Python 依赖
├── env_example.txt     # 配置文件模板
├── migrate_sessions.py # Session文件迁移脚本
├── ARCHITECTURE.md     # 架构说明文档
├── README.md          # 说明文档
├── sessions/           # Session文件目录（自动创建）
│   ├── message_extractor.session
│   ├── message_extractor.session-journal
│   ├── extractor_bot.session
│   └── extractor_bot.session-journal
└── extractor.log      # 日志文件（运行时生成）
```

## 故障排除

### 常见问题

**Q: 提示 "无法解析消息链接"**
A: 请检查链接格式是否正确，确保包含 `t.me`

**Q: 提示 "没有权限访问该消息"**
A: 确保您的账号可以访问该频道或群组

**Q: Bot 无响应**
A: 检查 Bot Token 是否正确，网络连接是否正常

**Q: 提取失败**
A: 查看日志文件 `extractor.log` 获取详细错误信息

### 日志查看
程序运行时会生成 `extractor.log` 文件，包含详细的运行日志。

### Session文件管理

**Session文件位置**:
- 所有session文件保存在 `sessions/` 目录中
- 包含用户账户和Bot的登录状态
- 自动创建目录，无需手动操作

**清理session文件**（重新登录）:
```bash
# 删除sessions目录重新开始
rm -rf sessions/
```

**备份session文件**:
```bash
# 备份整个sessions目录
cp -r sessions/ sessions_backup/
```

## 开发说明

### 核心组件
- `MessageExtractor`: 消息提取核心类
- `MessageExtractorBot`: Bot 处理器类
- 支持异步操作，性能优秀

### 扩展功能
您可以基于现有代码扩展更多功能：
- 批量消息提取
- 消息导出功能
- 更多媒体类型支持
- 数据库存储

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## 支持

如有问题或建议，请提交 Issue 或联系开发者。
