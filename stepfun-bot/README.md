
# Stepfun Bot with Wanda Tools

这是一个基于 Stepfun Realtime API 的 Node.js 机器人示例，实现了万达双塔相关工具调用功能。

## 功能

- 支持文本对话。
- 自动识别意图并调用以下工具：
  - `get_activities`: 获取活动列表
  - `get_listings`: 获取房源列表
  - `get_merchants`: 获取商户列表
  - `get_registration`: 查询报名信息

## 安装

```bash
cd stepfun-bot
npm install
```

## 运行

你需要设置 `STEP_SECRET` 环境变量 (你的 Stepfun API Key)。

### Windows PowerShell

```powershell
$env:STEP_SECRET='your_api_key_here'; node main.js
```

### CMD

```cmd
set STEP_SECRET=your_api_key_here && node main.js
```

### Linux / Mac

```bash
export STEP_SECRET=your_api_key_here
node main.js
```

## 使用

运行后，在控制台输入你的问题，例如：
- "最近有什么活动？"
- "帮我查一下南塔8栋的房源"
- "查询一下肯德基在哪里"
- "我的手机号是13800000000，帮我查下报名信息"
