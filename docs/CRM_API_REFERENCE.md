# 中国电信物联网 CRM 系统 API 文档

> 基于 `ctc-ctiot.crm.189.cn:8043` 老系统逆向分析，共发现 **98+ 个 API 端点**。

---

## 目录

- [认证与签名](#认证与签名)
- [Session 管理](#session-管理)
- [客户管理](#客户管理)
- [产品与订单](#产品与订单)
- [业务受理](#业务受理)
- [订单管理](#订单管理)
- [号码管理](#号码管理)
- [附件管理](#附件管理)
- [公告与系统](#公告与系统)
- [查询统计](#查询统计)
- [其他](#其他)

---

## 认证与签名

### 老系统签名 (MD5)

```
X-Sign = MD5(body + timestamp)
X-Request-Time = 毫秒时间戳
Cookie: PSESSIONNEWID=<session_id>
```

### 新系统签名 (HMAC, aiiot.crm.189.cn:8011)

```
签名串: t=<timestamp>&k=<key>&tk=<body_sha256>&m=<method>&pp=<params>
密钥: q92hjua9z
算法: 6种随机选一 (HmacSHA256/512/MD5, SHA256/512/MD5)
签名第3位 = 算法索引 (0-5)
```

---

## Session 管理

### `/pub/queryCurrentStaff` ⭐ 常用
查询当前登录用户信息。

**请求**: `{}`  
**响应**:
```json
{
  "resultCode": "200",
  "data": {
    "sysUserId": 1106375045,
    "staffId": 1000099128,
    "staffCode": "zhouhongpeng",
    "staffName": "周鸿鹏",
    "sysPostId": 1273,
    "sysPostName": "省市受理人员-台州市",
    "orgId": 1944728,
    "orgName": "台州市电信公司",
    "provinceId": 8330000,
    "provinceName": "浙江省",
    "cityId": 8331000,
    "cityName": "台州市",
    "sysRoleIds": [400, 9999],
    "iotrole": true
  }
}
```

### `/authsys/qryPostList`
查询用户可选岗位列表。

**请求**: `{"userId": 1106375045}`

### `/authsys/setPost`
选择岗位（必须先选岗位才能使用其他功能）。

**请求**: `{"userId": 1106375045, "postId": 1273, "organId": 1944728}`

### `/authsys/qryMenuTree`
获取菜单树。

**响应**: 菜单节点数组 (9个顶级节点)

### `/authsys/loginEncry`
SSO 登录入口，返回跳转 URL。

### `/authsys/ssoLocallogin`
新系统 SSO 本地登录。

**请求**: `{"tokenUser": "<token>"}`

### `/authsys/login`
标准登录。

### `/authsys/logout`
退出登录。

### `/authsys/extLogin`
外部登录。

### `/authsys/newLogin`
新登录接口。

### `/authsys/getSysUserCodeEncrypt`
获取加密的用户编码。

### `/authsys/getExternalUserInfo`
获取外部用户信息。

### `/authsys/update/password`
修改密码。

**请求**: `{"oldPassword": "", "newPassword": ""}`

### `/authsys/update/extPassword`
修改外部密码。

### `/authsso/login`
SSO 登录。

### `/authsso/cloudLogin`
云登录。

### `/authsso/cloudAuthRedirect`
云认证跳转。

---

## 客户管理

### `/cust/qryCustListTM` ⭐ 核心
查询客户列表（按接入号/客户名等）。

**请求**:
```json
{
  "qryType": "accNum",
  "qryValue1": "1410389574995",
  "qryValue2": null,
  "isFuzzy": false,
  "isCaseSensitive": false,
  "pageIndex": 0,
  "pageSize": 10
}
```

**qryType 可选值**: `accNum`, `custName`, `custNumber`

**响应**:
```json
{
  "resultCode": "200",
  "data": {
    "custDetailList": [{
      "customer": {
        "custId": 980001292010,
        "partyId": 960407643709,
        "shard2": 960407643709,
        "custName": "台州市公安局交通管理支*",
        "custNumber": "C2019092400001583855",
        "custAddr": "浙江省台州市椒江区机场北*****"
      }
    }],
    "pageInfo": {"rowCount": 1, "pageCount": 1}
  }
}
```

### `/cust/qryCustList`
查询客户列表（另一个版本）。

### `/cust/qryCustDetail` ⭐
查询客户详情（联系人信息）。

**请求**: `{"qryType": "custId", "qryValue1": 980001292010, "qryValue2": 980001292010}`

### `/cust/qryCustDetailTM` ⭐
查询客户详情（经办人信息）。

**请求**: `{"qryType": "custId", "qryValue1": 980001292010, "qryValue2": 960407643709}`

**响应**:
```json
{
  "data": {
    "custHandler": {
      "name": "李知巧",
      "certType": 1,
      "certNum": "331004198812011821",
      "certAddr": "浙江省台州市路桥区..."
    },
    "customer": { "custName": "...", "custAddr": "..." }
  }
}
```

### `/cust/qryProdOfferInstList` ⭐ 核心
查询客户的产品实例列表。

**请求**:
```json
{
  "qryType": "custId",
  "qryValue1": 980001292010,
  "regionId": 8331000,
  "regionType": "1300",
  "accNums": ["1410389574995"],
  "pageIndex": 1,
  "pageSize": 10
}
```

**响应**:
```json
{
  "data": {
    "result": [{
      "prodInstId": 914273007866,
      "prodId": "280000026",
      "offerId": "290081184",
      "offerName": "物联网5G无流量包-流量池成员0元专用",
      "prodName": "乐通（流量）",
      "accNum": "1410389574995",
      "statusCd": "100000",
      "statusCdDesc": "在用",
      "shard1": "14",
      "uimNum": ""
    }]
  }
}
```

### `/cust/qryProdInstList`
查询产品实例列表（另一版本）。

### `/cust/qryUserList`
查询用户列表。

### `/cust/qryDcpCustList`
查询 DCP 客户列表。

### `/cust/qryMigCust`
查询迁移客户。

### `/cust/qryOfferInstListByCust`
查询客户在用销售品。

**请求**: 需要 `custId`

### `/cust/qryOrderItemListByCust`
查询客户在线订单。

### `/cust/qryHisOrderItemListByCust`
查询客户历史订单。

### `/cust/qryWlwAppliPackList`
查询订购了物联网应用套件的客户。

**请求**: 需要 `regionId`, `custId`

### `/cust/createUser`
创建用户。

---

## 产品与订单

### `/order/qryOrdProdInstDetailInfo` ⭐ 核心
查询产品实例最新详情信息。

**请求**:
```json
{
  "qryValue1": "914273007866",
  "qryValue2": 980001292010,
  "qryValue3": "14",
  "prodId": "280000026",
  "busiActQryParam": {"busiActId": 87},
  "queryScopes": ["40011001", "40017003", "subProd", "40011013", "40011003", "40017004"]
}
```

**响应**:
```json
{
  "data": {
    "origin": [{
      "appBaseOrdProdInstDetails": [{
        "ordProdInst": {"prodId": 13416693, "prodInstId": 914273007867, "shard1": "14"},
        "ordProdInstAttrs": [
          {"attrId": 10005028, "attrValue": "10.95.5.224", "attrName": "IP地址"},
          {"attrId": 10005007, "attrValue": "tzgajj.zj.iot", "attrName": "DNN名称"}
        ],
        "ordProdInstStates": [
          {"stateId": "...", "stateType": "...", "stateValue": "..."}
        ]
      }]
    }]
  }
}
```

### `/order/qryProdInstExtInfos` ⭐
查询产品实例扩展属性。

**请求**: `{"prodInstId": 914273007866, "custId": 980001292010, "bookId": 14}`

**响应**:
```json
{
  "data": [
    {"attrId": "10020663", "attrValue": "Y33100110902", "remark": "集团编号"},
    {"attrId": "10020729", "attrValue": "1048576", "remark": "流量上限(M)"},
    {"attrId": "10020664", "attrValue": "18005868521", "remark": "联系号码"}
  ]
}
```

### `/order/acceptCustomerOrder` ⭐ 核心
提交订单（解绑等）。

**请求**:
```json
{
  "custOrderId": "<seq_id>",
  "custId": 980001292010,
  "partyId": 960407643709,
  "shard2": 960407643709,
  "accNum": "1410389574995",
  "prodId": "280000026",
  "offerId": "290081184",
  "busiActId": 87,
  "staffId": "...",
  "regionId": 8331000,
  "remark": "解绑",
  "subProds": [...],
  "handler": "李知巧",
  "certType": "1",
  "certNbr": "331004198812011821",
  "handlerCertAddr": "...",
  "contactName": "...",
  "contactNum": "..."
}
```

### `/order/acceptCustomizedInfoOrder`
提交自定义信息订单（违章复机用）。

### `/order/confirmCustomerOrder` ⭐
确认订单。

**请求**: `{"custOrderId": "<order_id>", "remark": "确认"}`

### `/order/qryCertInfoByAccNumOrCard`
按接入号或卡号查询证件信息。

### `/order/qryCertInfoByNum`
按号码查询证件信息。

### `/order/oneCardFiveNumQry`
一卡五号查询。

### `/order/oneCardFiveNumDataRecover`
一卡五号数据恢复。

### `/order/getOSSTaches`
获取 OSS 工序。

### `/order/getOSSRecvReqAndResp`
获取 OSS 接收请求和响应。

---

## 业务受理

### `/busiact/qryBusiActList` ⭐
查询业务功能列表。

**请求**: `{"accNum": "1410389574995", "prodId": "280000026"}`

**响应**:
```json
{
  "data": [{"busiActId": 87, "busiActName": "机卡分离"}]
}
```

### `/busiact/preacpt` ⭐ 必须
预受理（老系统解绑必须步骤）。

**请求**: `{"accNum": "...", "prodId": "...", "busiActId": 87, "offerId": "..."}`

### `/busiact/qryBusiOppList`
查询商机列表。

### `/busiact/qryBusiOppDtl`
查询商机详情。

### `/busiact/qryBusiOpportunity`
查询商机。

### `/busiact/qrySaleOrgDef`
查询销售组织定义。

**响应**: 353 条销售组织数据

### `/busiact/qrySaleOrgDefByRegionId`
按区域查询销售组织。

### `/busiact/returnBusiOpp`
退回商机。

---

## 订单管理

### `/pubquery/qryByComplexConditionNew` ⭐ 核心
复合条件查询订单。

**请求**:
```json
{
  "pageIndex": 0,
  "pageSize": 20,
  "isNeedCount": 1,
  "custOrderStatusCd": null,
  "acceptStartDate": "20260520000000",
  "acceptEndDate": "20260523235959",
  "acceptProvinceId": 8330000,
  "acceptLanId": 8331000,
  "isGetMyOrder": 0,
  "createStaff": null,
  "belongCustId": "",
  "seletId": "combination"
}
```

**注意**: 客户名称与受理员工为空时，时间范围必须在3天之内。

### `/pubquery/qryOrderDetail`
查询订单详情。

### `/pubquery/qryOrderDetailTM`
查询订单详情(TM版)。

### `/pubquery/qryOrdFlowTacheList`
查询订单流程环节列表。

### `/pubquery/qryOrdFlowTacheListDumb`
查询订单流程环节列表(简版)。

### `/pubquery/qryNewAuthorityCustList`
查询新权限客户列表。

### `/pubquery/qryOldAuthorityCustList`
查询旧权限客户列表。

### `/pubquery/qryOriAuthorityCustList`
查询原始权限客户列表。

### `/orderdeal/submitOrderCancel`
提交订单作废。

### `/orderdeal/reStartOrderProcess`
重启订单流程。

### `/orderdeal/reStartOrderOpen`
重启订单开放。

### `/orderdeal/takeCheckOrders`
领取审核工单。

### `/orderdeal/releaseCheckOrders`
释放审核工单。

### `/orderdeal/judgeIfHasProvinceAduit`
判断是否需要省级审核。

**请求**: `{"orderId": "0", "orderType": 0}`

### `/orderdeal/updateIotState`
更新 IoT 状态。

---

## 号码管理

### `/resmgr/card/qryNumCardInfoList` ⭐ 核心
按 ICCID 或接入号查询卡信息。

**请求**: `{"mktResInstNbrs": ["8986112321603583182"]}`

**响应**:
```json
{
  "resultCode": "200",
  "data": {
    "rspResult": [{
      "iccid": "8986112321603583182",
      "accNum": "1410389574995",
      "custName": "台州市公安局交通管理支*",
      "statusCd": "100000",
      "prodInstStatusCd": "100000",
      "limsi": "...",
      "firstFinishDate": "..."
    }]
  }
}
```

### `/numsel/search`
号码搜索。

**请求**: 需要 `orgId` 或 `paltId`

### `/numsel/searchNumHeadByProdId`
按产品ID查询号头。

### `/numsel/searchNBNumHeadByProdId`
查询 NB 号头。

### `/numsel/searchNumList`
查询号码列表。

### `/numsel/searchRandomNumList`
随机选号。

### `/numsel/submitNum`
提交选号。

### `/numsel/submmit`
提交（旧接口）。

---

## 附件管理

### `/orderAttachment/qryAttachmentType`
查询附件类型。

**请求**: 需要 `busiActId`, `productId`

### `/orderAttachment/qryAttachment`
查询附件。

### `/orderAttachment/qryAttachmentByCustId`
按客户ID查询附件。

### `/orderAttachment/qryAttachmentSatisfy`
查询满足条件的附件。

### `/orderAttachment/qryAttachmentTypeByServOfferId`
按服务销售品ID查询附件类型。

### `/orderAttachment/uploadAttachment`
上传附件。

### `/orderAttachment/uploadImage`
上传图片。

### `/orderAttachment/uploadCustImage`
上传客户图片。

### `/orderAttachment/viewAttachment`
查看附件。

### `/orderAttachment/deleteAttachment`
删除附件。

### `/orderAttachment/customUpload`
自定义上传。

### `/orderAttachment/saveAgtTplAttachment`
保存代理模板附件。

### `/orderAttachment/updateAttacheImgMsgs`
更新附件图片信息。

### `/orderAttachment/updateHandlerImgMsg`
更新经办人图片信息。

### `/orderAttachment/qryHandlerImg`
查询经办人图片。

### `/orderAttachment/qryHandlerAttachmentFromCache`
从缓存查询经办人附件。

### `/orderAttachment/uploadOldOrderAttachments`
上传旧订单附件。

---

## 订单审核

### `/orderCheckResult/qrySingleOrdCheckResult`
查询单个订单审核结果。

**请求**: 需要 `orderId`

### `/orderCheckResult/qryAttachment`
审核附件查询。

### `/orderHandler/recordHandlerInfo`
记录经办人信息。

### `/orderHandler/updateOrderHandlerInfo`
更新订单经办人信息。

---

## 公告与系统

### `/bulletin/qryBulletinList` ⭐
查询公告列表。

**请求**: `{"pageIndex": 0, "pageSize": 10}`

### `/bulletin/qryBulletinInfo`
查询公告详情。

### `/bulletin/qryMoreBulletin`
查询更多公告。

### `/bulletin/batchDeleteBulletin`
批量删除公告。

### `/bulletin/qryBullRemindListForRestPwd`
查询密码重置提醒。

### `/bulletin/restPwd`
重置密码。

### `/bulletin/finishRestPwd`
完成密码重置。

### `/pub/geneSeqId` ⭐
获取订单序列号。

**响应**: `{"resultCode": "200", "data": "ORD202605230001"}`

### `/pub/qryCommonRegionByName`
按名称查询区域。

### `/pub/qrySysParamList`
查询系统参数列表。

### `/pub/qryOperateQueueList`
查询操作队列。

### `/pub/qryAttrValueList`
查询属性值列表。

**请求**: 需要属性编码

### `/pub/qryAttrValueByIds`
按ID查询属性值。

### `/pub/queryPublished`
查询已发布内容。

### `/pub/aiAssistant`
AI 助手。

**请求**: `{"question": "..."}`

### `/pubCust/syncContactsInfo`
同步联系人信息。

---

## 查询统计

### `/querystat/orgTree`
组织架构树。

### `/querystat/queryStaffComplex`
复合查询员工。

### `/querystat/queryStaffComplexNew`
新版复合查询员工。

### `/querystat/qryMobilePhoneFromGovEnterpriseCRM`
从政企 CRM 查询手机号。

### `/sqlQry/execSql`
执行 SQL。

**请求**: `{"dbName": "...", "sql": "SELECT ..."}`

### `/sysParamCfg/qrySysParamList`
查询系统参数配置列表。

### `/survey/qrySurveyStaff`
查询问卷员工。

### `/survey/qrySurveyTerm`
查询问卷条件。

### `/survey/submitSurvey`
提交问卷。

### `/survey/getDcpUrl`
获取 DCP URL。

---

## 政企客户

### `/goverCust/qryGoverCustList` ⭐
查询政企客户列表。

**请求**: `{"pageIndex": 0, "pageSize": 10}`

**响应**:
```json
{
  "data": {
    "result": [...],
    "rowCount": 100,
    "pageCount": 10
  }
}
```

---

## 人脸认证

### `/authFace/faceVerify`
人脸验证。

**响应** (无身份证照片时):
```json
{
  "resultCode": "200",
  "requestId": "...",
  "timeUsed": 123,
  "confidence": 0,
  "errorCode": "..."
}
```

---

## 完整 API 清单

| # | 路径 | 模块 | 说明 |
|---|------|------|------|
| 1 | `/pub/queryCurrentStaff` | 认证 | 查询当前员工 |
| 2 | `/authsys/qryPostList` | 认证 | 查询岗位列表 |
| 3 | `/authsys/setPost` | 认证 | 选择岗位 |
| 4 | `/authsys/qryMenuTree` | 认证 | 菜单树 |
| 5 | `/authsys/loginEncry` | 认证 | SSO登录 |
| 6 | `/authsys/ssoLocallogin` | 认证 | 新系统SSO |
| 7 | `/authsys/login` | 认证 | 标准登录 |
| 8 | `/authsys/logout` | 认证 | 退出 |
| 9 | `/authsys/extLogin` | 认证 | 外部登录 |
| 10 | `/authsys/newLogin` | 认证 | 新登录 |
| 11 | `/authsys/getSysUserCodeEncrypt` | 认证 | 加密用户编码 |
| 12 | `/authsys/getExternalUserInfo` | 认证 | 外部用户信息 |
| 13 | `/authsys/update/password` | 认证 | 修改密码 |
| 14 | `/authsys/update/extPassword` | 认证 | 修改外部密码 |
| 15 | `/authsso/login` | 认证 | SSO登录 |
| 16 | `/authsso/cloudLogin` | 认证 | 云登录 |
| 17 | `/authsso/cloudAuthRedirect` | 认证 | 云认证跳转 |
| 18 | `/cust/qryCustListTM` | 客户 | 查询客户(TM) |
| 19 | `/cust/qryCustList` | 客户 | 查询客户 |
| 20 | `/cust/qryCustDetail` | 客户 | 客户详情(联系人) |
| 21 | `/cust/qryCustDetailTM` | 客户 | 客户详情(经办人) |
| 22 | `/cust/qryProdOfferInstList` | 客户 | 产品实例列表 |
| 23 | `/cust/qryProdInstList` | 客户 | 产品实例列表 |
| 24 | `/cust/qryUserList` | 客户 | 用户列表 |
| 25 | `/cust/qryDcpCustList` | 客户 | DCP客户 |
| 26 | `/cust/qryMigCust` | 客户 | 迁移客户 |
| 27 | `/cust/qryOfferInstListByCust` | 客户 | 客户销售品 |
| 28 | `/cust/qryOrderItemListByCust` | 客户 | 客户在线订单 |
| 29 | `/cust/qryHisOrderItemListByCust` | 客户 | 客户历史订单 |
| 30 | `/cust/qryWlwAppliPackList` | 客户 | 物联网套件 |
| 31 | `/cust/createUser` | 客户 | 创建用户 |
| 32 | `/order/qryOrdProdInstDetailInfo` | 订单 | 产品详情 |
| 33 | `/order/qryProdInstExtInfos` | 订单 | 扩展属性 |
| 34 | `/order/acceptCustomerOrder` | 订单 | 提交订单 |
| 35 | `/order/acceptCustomizedInfoOrder` | 订单 | 自定义订单 |
| 36 | `/order/confirmCustomerOrder` | 订单 | 确认订单 |
| 37 | `/order/qryCertInfoByAccNumOrCard` | 订单 | 证件查询 |
| 38 | `/order/qryCertInfoByNum` | 订单 | 按号码查证件 |
| 39 | `/order/oneCardFiveNumQry` | 订单 | 一卡五号 |
| 40 | `/order/oneCardFiveNumDataRecover` | 订单 | 数据恢复 |
| 41 | `/order/getOSSTaches` | 订单 | OSS工序 |
| 42 | `/order/getOSSRecvReqAndResp` | 订单 | OSS请求响应 |
| 43 | `/busiact/qryBusiActList` | 业务 | 业务功能列表 |
| 44 | `/busiact/preacpt` | 业务 | 预受理 |
| 45 | `/busiact/qryBusiOppList` | 业务 | 商机列表 |
| 46 | `/busiact/qryBusiOppDtl` | 业务 | 商机详情 |
| 47 | `/busiact/qryBusiOpportunity` | 业务 | 商机 |
| 48 | `/busiact/qrySaleOrgDef` | 业务 | 销售组织 |
| 49 | `/busiact/qrySaleOrgDefByRegionId` | 业务 | 区域销售组织 |
| 50 | `/busiact/returnBusiOpp` | 业务 | 退回商机 |
| 51 | `/pubquery/qryByComplexConditionNew` | 查询 | 复合查询订单 |
| 52 | `/pubquery/qryOrderDetail` | 查询 | 订单详情 |
| 53 | `/pubquery/qryOrderDetailTM` | 查询 | 订单详情(TM) |
| 54 | `/pubquery/qryOrdFlowTacheList` | 查询 | 流程环节 |
| 55 | `/pubquery/qryOrdFlowTacheListDumb` | 查询 | 流程环节(简) |
| 56 | `/pubquery/qryNewAuthorityCustList` | 查询 | 新权限客户 |
| 57 | `/pubquery/qryOldAuthorityCustList` | 查询 | 旧权限客户 |
| 58 | `/pubquery/qryOriAuthorityCustList` | 查询 | 原始权限客户 |
| 59 | `/orderdeal/submitOrderCancel` | 工单 | 作废订单 |
| 60 | `/orderdeal/reStartOrderProcess` | 工单 | 重启流程 |
| 61 | `/orderdeal/reStartOrderOpen` | 工单 | 重启开放 |
| 62 | `/orderdeal/takeCheckOrders` | 工单 | 领取审核 |
| 63 | `/orderdeal/releaseCheckOrders` | 工单 | 释放审核 |
| 64 | `/orderdeal/judgeIfHasProvinceAduit` | 工单 | 省级审核判断 |
| 65 | `/orderdeal/updateIotState` | 工单 | 更新IoT状态 |
| 66 | `/resmgr/card/qryNumCardInfoList` | 资源 | ICCID/接入号查卡 |
| 67 | `/numsel/search` | 号码 | 号码搜索 |
| 68 | `/numsel/searchNumHeadByProdId` | 号码 | 号头查询 |
| 69 | `/numsel/searchNBNumHeadByProdId` | 号码 | NB号头 |
| 70 | `/numsel/searchNumList` | 号码 | 号码列表 |
| 71 | `/numsel/searchRandomNumList` | 号码 | 随机选号 |
| 72 | `/numsel/submitNum` | 号码 | 提交选号 |
| 73 | `/numsel/submmit` | 号码 | 提交(旧) |
| 74 | `/orderAttachment/qryAttachmentType` | 附件 | 附件类型 |
| 75 | `/orderAttachment/qryAttachment` | 附件 | 查询附件 |
| 76 | `/orderAttachment/qryAttachmentByCustId` | 附件 | 按客户查附件 |
| 77 | `/orderAttachment/qryAttachmentSatisfy` | 附件 | 满足条件附件 |
| 78 | `/orderAttachment/qryAttachmentTypeByServOfferId` | 附件 | 按销售品查类型 |
| 79 | `/orderAttachment/uploadAttachment` | 附件 | 上传附件 |
| 80 | `/orderAttachment/uploadImage` | 附件 | 上传图片 |
| 81 | `/orderAttachment/uploadCustImage` | 附件 | 上传客户图片 |
| 82 | `/orderAttachment/viewAttachment` | 附件 | 查看附件 |
| 83 | `/orderAttachment/deleteAttachment` | 附件 | 删除附件 |
| 84 | `/orderAttachment/customUpload` | 附件 | 自定义上传 |
| 85 | `/orderAttachment/saveAgtTplAttachment` | 附件 | 代理模板 |
| 86 | `/orderAttachment/updateAttacheImgMsgs` | 附件 | 更新图片信息 |
| 87 | `/orderAttachment/updateHandlerImgMsg` | 附件 | 更新经办人图片 |
| 88 | `/orderAttachment/qryHandlerImg` | 附件 | 经办人图片 |
| 89 | `/orderAttachment/qryHandlerAttachmentFromCache` | 附件 | 缓存附件 |
| 90 | `/orderAttachment/uploadOldOrderAttachments` | 附件 | 旧订单附件 |
| 91 | `/orderCheckResult/qrySingleOrdCheckResult` | 审核 | 审核结果 |
| 92 | `/orderCheckResult/qryAttachment` | 审核 | 审核附件 |
| 93 | `/orderHandler/recordHandlerInfo` | 审核 | 记录经办人 |
| 94 | `/orderHandler/updateOrderHandlerInfo` | 审核 | 更新经办人 |
| 95 | `/bulletin/*` | 公告 | 公告管理(7个) |
| 96 | `/pub/geneSeqId` | 公共 | 获取序列号 |
| 97 | `/pub/*` | 公共 | 公共服务(7个) |
| 98 | `/querystat/*` | 统计 | 查询统计(4个) |
| 99 | `/goverCust/qryGoverCustList` | 政企 | 政企客户 |
| 100 | `/authFace/faceVerify` | 认证 | 人脸验证 |
| 101 | `/survey/*` | 问卷 | 调查问卷(4个) |
| 102 | `/sqlQry/execSql` | 系统 | SQL查询 |
| 103 | `/sysParamCfg/qrySysParamList` | 系统 | 系统参数 |

---

## 业务类型识别表

| 类型 | prodId | offerId | shard1 | busiActId |
|------|--------|---------|--------|-----------|
| NB卡 | 13410706 | 84687/84684/84686 | 24 | 209 |
| 4G VPDN | 280000026 | 84229 | 15 | 87 |
| 5G VPDN | 280000026 | 290081184 | 13 | 87 |
| 5G定向 | 280000026 | 290081188 | 13 | 87 |
| 5G定制网 | 280000026 | 290081188 | 14 | 87 |

## 卡状态码

| 状态码 | 含义 |
|--------|------|
| 100000 | 在用 |
| 110000 | 未激活 |
| 120000 | 停机 |

## 订单状态码

| 状态码 | 含义 |
|--------|------|
| 100000 | 待处理 |
| 201100 | 审核中 |
| 301100 | 处理中 |
| 301200 | 已完成 |
| 401300 | 已取消 |
| 401700 | 已取消 |

---

*文档生成时间: 2026-05-23*
*数据来源: ctc-ctiot.crm.189.cn:8043 前端 JS 逆向分析 + API 实测*
