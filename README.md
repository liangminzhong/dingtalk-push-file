# dingtalk-push-file

一个 90 行的 Python 脚本：把本地文件（PDF / 压缩包 / 文档等）通过钉钉机器人群发到指定用户的**单聊**。零依赖框架，只需 `requests`。

典型场景：
- 服务器上定时任务生成的报表，跑完直接推到你手机钉钉
- AI Agent（Hermes / OpenClaw 等）生成报告后自动送达
- CI 构建产物（安装包、测试报告）即时分发

## 快速开始

### 1. 准备钉钉机器人凭证

1. 登录 [钉钉开放平台](https://open-dev.dingtalk.com/) → 创建**企业内部应用**
2. 在「应用功能 → 机器人」中启用机器人
3. 获取 `AppKey`（Client ID）和 `AppSecret`（Client Secret）
4. 确认应用已开通「企业内机器人发送单聊消息」权限

### 2. 安装

```bash
git clone https://github.com/raymondzhong/dingtalk-file-sender.git
cd dingtalk-file-sender
pip install -r requirements.txt
```

### 3. 配置凭证

```bash
cp .env.example .env
# 编辑 .env，填入你的 Client ID / Secret 和接收人 userId
```

获取接收人 userId：钉钉管理后台 → 通讯录 → 成员详情 → 「userId」；
或用通讯录部门用户详情接口查询。

### 4. 发送

```bash
python3 dingtalk_send_file.py /path/to/report.pdf

# 完整参数
python3 dingtalk_send_file.py /path/to/report.pdf \
    --user YOUR_USER_ID \
    --display-name "9月财务报告.pdf"
```

收到效果：钉钉单聊窗口出现一张文件卡片，点击可下载/预览。

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `file`（位置参数） | 必填 | 本地文件路径 |
| `--user` | 环境变量 `DINGTALK_NOTIFY_USERID` 或 `YOUR_USER_ID` | 接收人钉钉 userId |
| `--display-name` | 文件原名 | 钉钉里显示的文件名 |
| `--profile` | `default` | 凭证组名（多机器人场景，见下） |

## 凭证查找顺序

脚本依次尝试，找到即用：

1. 环境变量 `DINGTALK_CLIENT_ID` + `DINGTALK_CLIENT_SECRET`
2. `.env`（脚本同目录，或 `~/.hermes/profiles/<profile>/.env`）

多机器人：把不同凭证放到不同 `.env`，用 `--profile` 切换。

## 工作原理

```
gettoken → media/upload (type=file) → robot/oToMessages/batchSend (sampleFile)
```

1. 用 AppKey/Secret 换取 `access_token`
2. 文件上传到钉钉媒体库，得到 `media_id`（有效期 3 天）
3. 以机器人身份向 userId 单聊发送 `sampleFile` 消息

## 限制与注意

- 钉钉不支持直接发送 `.html` 附件（errcode 40005），复杂报告请先转 PDF：
  ```bash
  chromium --headless --no-sandbox --disable-gpu \
      --print-to-pdf=out.pdf --print-to-pdf-no-header "file://$(pwd)/in.html"
  ```
- 单文件上传上限约 20MB（钉钉媒体库限制）
- 机器人单聊要求接收人在应用可见范围内，且未关闭机器人消息

## License

MIT
