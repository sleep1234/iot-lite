# IoT Lite - 物联网卡管理工具（精简版）

> 中国电信物联网 CRM 系统的精简管理工具，核心理念：**智能输入 + API 自动串联 = 最少操作步骤**

---

## ✨ 核心特性

### 🔍 智能查询（一步到位）

传统方式需要 6 步：复制 ICCID → 打开 ICCID 查询 → 查询 → 复制接入号 → 打开通用查询 → 粘贴查询。

**IoT Lite 只需 1 步**：粘贴 ICCID 或接入号，系统自动识别并串联查询，一步展示全部信息。

| 输入格式 | 自动识别 | 处理流程 |
|----------|----------|----------|
| `8986...` 19-20位 | ICCID | → 查接入号 → 查客户 → 查产品 → 查详情 |
| `141...` 13位 | 接入号 | → 直接查客户 → 查产品 → 查详情 |
| 多行（换行/逗号分隔） | 批量 | → 自动切换批量模式 |

### 📱 完整卡片信息

一次查询返回所有信息：

- **客户信息** — 名称、编号、地址
- **卡片状态** — 在用/停机/未激活
- **套餐信息** — 产品名称、offer 信息
- **网络信息** — IP 地址、DNN 名称、SA 模式
- **设备信息** — IMEI、UIM 号
- **绑定状态** — 机卡绑定状态
- **已订购服务** — 所有子服务及属性（切片、VPDN、定向等）
- **扩展属性** — 集团编号、联系号码、白名单类型、流量上限
- **定向编码** — 4G/5G 定向编码、APN

### ⚡ 快捷操作

查询完成后直接执行：

- 🔓 **机卡解绑** — 完整 9 步流程（预受理→序列号→规则校验→提交→确认）
- 🔄 **违章复机** — 违章停机卡恢复
- 📋 **一键复制** — 接入号 / ICCID / 全部 JSON

### 📋 批量操作

- **批量查询** — 多个号码一行一个，批量查全部信息
- **批量解绑** — 粘贴多个 ICCID/接入号，一键批量解绑（自动 ICCID→接入号转换）

### 📦 工单查询

- 按天数筛选（今天 / 3天 / 7天 / 30天）
- 按员工姓名筛选
- 显示工单号、业务名称、客户、状态、时间、经办人

### 🔐 Session 自动管理

```
PSESSIONNEWID 过期
    → TGT 刷新（自动，无感）
        → 失败 → 全自动登录（图形验证码 OCR → 短信 → 登录）
            → 失败 → 提示手动连接
```

---

## 📊 API 使用情况

IoT Lite 当前调用了 **16 个 CRM API 端点**，覆盖查询、解绑、复机的完整业务流程。

### 查询流程（6 个 API）

| # | API | 用途 | 调用时机 |
|---|-----|------|----------|
| 1 | `/resmgr/card/qryNumCardInfoList` | ICCID → 接入号转换 | 输入 ICCID 时 |
| 2 | `/cust/qryCustListTM` | 查询客户列表 | 每次查询 |
| 3 | `/cust/qryCustDetailTM` | 查询客户详情（经办人） | 每次查询 |
| 4 | `/cust/qryProdOfferInstList` | 查询产品实例列表 | 每次查询 |
| 5 | `/order/qryOrdProdInstDetailInfo` | 查询产品详情（子服务、IP、DNN） | 每次查询 |
| 6 | `/order/qryProdInstExtInfos` | 查询扩展属性（集团编号、流量上限等） | 每次查询 |

### 解绑流程（9 个 API）

| # | API | 用途 |
|---|-----|------|
| 1 | `/cust/qryCustListTM` | 查客户 |
| 2 | `/cust/qryProdOfferInstList` | 查产品实例 |
| 3 | `/busiact/qryBusiActList` | 查业务功能列表 → 获取 busiActId |
| 4 | `/busiact/preacpt` | **预受理**（老系统必须，否则后端拒绝） |
| 5 | `/pub/geneSeqId` | 获取订单序列号 |
| 6 | `/order/qryOrdProdInstDetailInfo` | 查产品详情（附属产品和属性） |
| 7 | `/cust/qryCustDetail` + `/cust/qryCustDetailTM` | 获取经办人信息 |
| 8 | `/busirule/preAcpRule` | 规则校验 |
| 9 | `/order/acceptCustomerOrder` + `/order/confirmCustomerOrder` | 提交 + 确认订单 |

### 复机流程（9 个 API）

与解绑类似，但使用不同的 `busiActId`（98）和 `serviceOfferId`（4070200000），并额外调用：

- `/orderdeal/judgeIfHasProvinceAduit` — 判断是否需要省级审核
- `/order/acceptCustomizedInfoOrder` — 提交自定义订单

### 工单查询（1 个 API）

| API | 用途 |
|-----|------|
| `/pubquery/qryByComplexConditionNew` | 复合条件查询订单列表 |

### Session 管理（1 个 API）

| API | 用途 |
|-----|------|
| `/pub/queryCurrentStaff` | 验证 Session 有效性 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│                IoT Lite (Flask)                  │
│              http://localhost:10001              │
│                                                 │
│   智能输入 → 自动识别类型 → API 串联查询         │
│                                                 │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│   │ ICCID   │──→│ 接入号  │──→│ 客户    │      │
│   │ 识别    │   │ 转换    │   │ 查询    │      │
│   └─────────┘   └─────────┘   └────┬────┘      │
│                                     │           │
│   ┌─────────┐   ┌─────────┐   ┌────▼────┐      │
│   │ 详情    │←──│ 产品    │←──│ 产品    │      │
│   │ 展示    │   │ 详情    │   │ 列表    │      │
│   └─────────┘   └─────────┘   └─────────┘      │
│                                                 │
│   解绑/复机 → 9步完整流程自动执行                │
│        │                                        │
│        ▼                                        │
│   CRM API (MD5签名 + Session管理)               │
│   ctc-ctiot.crm.189.cn:8043                    │
└─────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 内网环境（能访问 CRM 系统）

### 安装

```bash
# 从原项目复制必要文件
cp /path/to/merged_app/xsign.py .
cp /path/to/merged_app/config.py .
cp /path/to/merged_app/auto_login.py .
cp /path/to/merged_app/des_crypto.py .
cp -r /path/to/merged_app/static/ .

# 安装依赖
pip install -r requirements.txt
```

### 配置

编辑 `config.py` 或设置环境变量：

```env
IOT_SECRET_KEY=your-secret-key
AI_CAPTCHA_API=http://your-ai-api/v1
AI_CAPTCHA_KEY=your-api-key
CRM_PHONE=1xxxxxxxxxx
```

### 启动

```bash
python app.py
```

访问 `http://localhost:10001`

---

## 📁 文件结构

```
iot_lite/
├── app.py              # 主程序（智能查询+API串联，16个CRM API调用）
├── app_unbind.py       # 解绑/复机操作（完整9步流程）
├── templates/
│   └── index.html      # 前端界面（暗色主题，响应式）
├── docs/
│   └── CRM_API_REFERENCE.md  # CRM API 完整文档（103个端点）
├── config.py           # 配置
├── xsign.py            # X-Sign 签名算法
├── auto_login.py       # 自动登录
├── des_crypto.py       # DES加密
├── static/             # 静态文件
├── requirements.txt    # 依赖
├── README.md           # 本文档
└── .gitignore          # Git忽略规则
```

---

## 📚 API 文档

CRM 系统共发现 **103 个 API 端点**，IoT Lite 使用了其中 16 个。

完整 API 文档详见 [docs/CRM_API_REFERENCE.md](docs/CRM_API_REFERENCE.md)

涵盖模块：
- 认证与 Session（17个）
- 客户管理（14个）
- 产品与订单（11个）
- 业务受理（8个）
- 订单查询（8个）
- 工单管理（7个）
- 号码管理（7个）
- 附件管理（17个）
- 订单审核（4个）
- 公告与系统（12个）
- 查询统计（4个）
- 其他（10个）

---

## 🔐 认证说明

### 老系统签名 (MD5)

```
X-Sign = MD5(body + timestamp)
X-Request-Time = 毫秒时间戳
Cookie: PSESSIONNEWID=<session_id>
```

### Session 生命周期

```
PSESSIONNEWID 过期 → TGT 刷新（自动）→ 全自动登录（验证码OCR+短信）→ 手动连接
```

---

## ⚠️ 注意事项

1. **内网环境** — 必须在能访问 CRM 系统的内网环境运行
2. **Session 有效期** — PSESSIONNEWID 通常 8 小时有效
3. **操作风险** — 解绑/复机操作不可撤销，请确认后再执行
4. **并发安全** — Flask 多线程环境下 Session 管理已做线程安全处理

---

## 📝 更新日志

### v1.0 (2026-05-23)

- 智能查询（ICCID/接入号自动识别，串联 6 个 API 一步查完）
- 完整详情查询（IP/DNN/IMEI/服务/属性/定向编码）
- 机卡解绑（完整 9 步流程，调用 9 个 API）
- 违章复机（完整流程，含省级审核判断）
- 批量查询 / 批量解绑
- 工单查询
- Session 自动管理
- CRM API 完整文档（103 个端点）

---

*基于 [merged_app](../merged_app/) 项目重构*
