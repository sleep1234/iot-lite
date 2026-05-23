#!/usr/bin/env python3
"""
IoT Lite - 物联网卡管理工具（完整版）
=====================================
功能：智能查询、机卡解绑、违章复机、批量操作、工单查询、定向编码查询
"""

import json
import os
import time
import hashlib
import logging
import re
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, g
import requests as req_lib

import config as cfg
from xsign import build_headers as xsign_build_headers

# ============================================================
# Config
# ============================================================
OLD_BASE = cfg.OLD_BASE_URL
NEW_BASE = cfg.NEW_BASE_URL
PSession_FILE = os.path.join(os.path.dirname(__file__), ".psession")
TGT_FILE = os.path.join(os.path.dirname(__file__), ".tgt_token")

logging.basicConfig(
    level=logging.DEBUG if cfg.DEBUG else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("iot-lite")

app = Flask(__name__)
app.secret_key = cfg.SECRET_KEY

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# Product/Attr Name Maps (from original project)
# ============================================================
_PROD_NAME_MAP = {
    "13409800": "天翼对讲（语音）", "13409902": "乐通-定向", "13409920": "达量断网",
    "13409921": "乐通-区域限制", "13410485": "VoLTE", "13410506": "强制激活",
    "13410507": "VPDN-L2TP（可访问公网）", "13410508": "VPDN-GRE（可访问公网）",
    "13410609": "关闭语音", "13410610": "乐通-机卡绑定",
    "13410686": "短信-定向访问", "13411406": "多APN（成员）",
    "13411407": "平台类定向", "13411446": "自主限速", "13411605": "定向访问黑名单",
    "13413085": "5G-平台类定向", "13414750": "IPv6安全微标识",
    "13415745": "5G数据通信（SA）", "13416005": "区域限制黑名单",
    "13416110": "5G-定向访问", "13416111": "5G-公网",
    "13416112": "5G-定向访问黑名单", "13416113": "5G-区域限制",
    "13416114": "5G-机卡绑定", "13416115": "5G-VPDN-L2TP",
    "13416116": "5G-VPDN-GRE", "13416693": "5G-定制专网DNN",
    "13417008": "定制APN（成员）", "13417028": "5G-QOS优享加速",
    "23421540": "5G-多DNN（成员）", "23428920": "车联网卡生命安全定向",
    "23433200": "5G双域快网成员产品", "23434060": "5G区域限制黑名单",
    "23542240": "物联网国际/港澳台漫游数据", "80007079": "车管专家",
    "235010003": "3G（EVDO）上网", "235010006": "短信",
    "235010008": "2G（1X）上网", "280000020": "4G（LTE）上网",
    "280000030": "外勤助手", "280000034": "物流E通",
    "381000632": "VPDN-L2TP", "381000634": "VPDN-GRE",
    "381002183": "流量共享池成员产品",
    "381003325": "NB公共APN参数配置（成员）", "13416452": "NB辅助产品",
    "13410708": "NB公共APN参数配置", "13411448": "物联网5G定制网",
}

_ATTR_NAME_MAP = {
    "10010076": "断网阀值(M)", "10020086": "断网类型",
    "10020096": "VPDN域名", "10020097": "APN", "10020098": "物联网VPDN AAA",
    "10020099": "无线接入制式", "10020101": "APN模板号",
    "10020102": "用户名", "10020103": "用户密码",
    "10020104": "固定IP地址", "10020105": "账号密码免校验功能",
    "10020106": "公网访问限制功能", "10020107": "关闭eHRPD功能",
    "10020108": "APN自动纠错", "900000418": "群号码",
    "10020140": "激活标志",
    "10020743": "区域限制类型", "10010063": "区域编码",
    "10020681": "区域限制模式",
    "10020615": "绑定模式", "10020152": "重绑定次数",
    "10010078": "定向编码", "10020113": "APN名称",
    "10020226": "定向编码",
    "10020662": "计费周期", "10020663": "集团编号",
    "10020664": "联系号码", "10020677": "白名单类型",
    "10020720": "绑定状态", "10020729": "流量上限(M)",
    "10005008": "用户标签", "10005019": "QCI",
    "10005028": "IP地址", "10005027": "IPv6地址",
    "10020703": "切片名称", "10020704": "切片ID",
    "10005048": "SA模式", "10000000121": "业务类型",
    "10005007": "DNN名称",
    "10020088": "定向编码", "10020606": "定向内容",
    "10005001": "接入类型", "10005002": "网络切片",
    "10005003": "DNN类型", "10020731": "SA标志",
    "900000419": "池成员标志",
    "10020073": "绑定号码",
    "10005044": "区域名称", "10005045": "区域类型",
    "10010003": "省代码", "10010004": "地市代码", "10020003": "区域标识",
    "10020210": "接入方式", "10020616": "IMEI编码(附属)",
    "10020080": "IMSI", "10020745": "备注", "10020085": "产品规格",
    "10020175": "激活时间", "10010148": "归属地市",
}

_ATTR_VALUE_MAP = {
    "10020086": {"10": "用户总使用量", "20": "用户漫游使用量"},
    "10020099": {"1": "2G", "2": "3G", "3": "4G", "4": "5G"},
    "10020098": {"1": "是", "2": "否"}, "10020105": {"1": "是", "2": "否"},
    "10020106": {"1": "是", "2": "否"}, "10020107": {"1": "是", "2": "否"},
    "10020108": {"1": "是", "2": "否"}, "10020210": {"1": "自动", "2": "手动"},
    "10005048": {"1": "NSA", "2": "SA"},
    "10020743": {"1": "省", "2": "市", "3": "自定义"},
    "10020681": {"0": "白名单", "1": "黑名单"},
    "10020615": {"1000": "自动", "2000": "手动"},
    "10000000121": {"1001": "普通上网", "1002": "VPDN专网", "1003": "定向访问"},
}

CARD_STATUS_MAP = {"100000": "在用", "110000": "未激活", "120000": "停机", "1104": "在用"}


# ============================================================
# Input Detection
# ============================================================
def detect_input_type(text):
    text = text.strip()
    if not text:
        return None, None
    if re.match(r'^8986\d{15,16}$', text):
        return 'iccid', text
    if re.match(r'^141\d{10}$', text):
        return 'accnum', text
    if re.match(r'^\d{13}$', text) and text.startswith('1'):
        return 'accnum', text
    if re.match(r'^1[3-9]\d{9}$', text):
        return 'phone', text
    if re.match(r'^\d{10,20}$', text):
        return 'iccid_or_accnum', text
    return 'unknown', text


# ============================================================
# CRM Client
# ============================================================
class CRMClient:
    def __init__(self):
        self._session_id = None
        self._tgt = None
        self._lock = threading.Lock()
        self._load_tokens()
    
    def _load_tokens(self):
        try:
            if os.path.exists(PSession_FILE):
                with open(PSession_FILE) as f:
                    self._session_id = f.read().strip() or None
            if os.path.exists(TGT_FILE):
                with open(TGT_FILE) as f:
                    self._tgt = f.read().strip() or None
        except Exception:
            pass
    
    def _save_tokens(self):
        try:
            if self._session_id:
                with open(PSession_FILE, 'w') as f:
                    f.write(self._session_id)
            if self._tgt:
                with open(TGT_FILE, 'w') as f:
                    f.write(self._tgt)
        except Exception as e:
            log.error(f"Save tokens failed: {e}")
    
    def _old_headers(self, body_str=""):
        ts = str(int(time.time() * 1000))
        sign_input = (body_str + ts) if body_str else ts
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": OLD_BASE,
            "Referer": f"{OLD_BASE}/m2m/index.html?iframe",
            "Cookie": f"PSESSIONNEWID={self._session_id}",
            "X-Sign": hashlib.md5(sign_input.encode()).hexdigest(),
            "X-Request-Time": ts,
        }
    
    def old_post(self, path, body_dict, timeout=30):
        body_str = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False)
        headers = self._old_headers(body_str)
        url = f"{OLD_BASE}{path}"
        try:
            resp = req_lib.post(url, data=body_str.encode("utf-8"),
                               headers=headers, verify=False, timeout=timeout)
            result = resp.json()
        except Exception as e:
            log.exception(f"Old API error: {path}")
            return {"resultCode": "500", "resultMsg": str(e)}
        
        msg = result.get("resultMsg", "")
        code = str(result.get("resultCode", ""))
        if code != "200" and ("登录" in msg or "session" in msg.lower() or "过期" in msg):
            log.warning(f"Session expired on {path}, trying refresh...")
            if self._refresh_session():
                body_str = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False)
                headers = self._old_headers(body_str)
                try:
                    resp = req_lib.post(url, data=body_str.encode("utf-8"),
                                       headers=headers, verify=False, timeout=timeout)
                    result = resp.json()
                except Exception as e:
                    return {"resultCode": "500", "resultMsg": str(e)}
        return result
    
    def _refresh_session(self):
        from auto_login import get_psession_quick, full_auto_login
        if self._tgt:
            result = get_psession_quick(self._tgt)
            if result.get("ok"):
                self._session_id = result["psession_id"]
                self._tgt = result.get("tgt", self._tgt)
                self._save_tokens()
                log.info("TGT refresh success")
                return True
        phone = cfg.CRM_PHONE
        if phone:
            log.info(f"Trying full auto login with {phone}...")
            result = full_auto_login(phone)
            if result.get("ok"):
                self._session_id = result["psession_id"]
                self._tgt = result.get("tgt")
                self._save_tokens()
                log.info("Full auto login success")
                return True
        return False
    
    def check_session(self):
        if not self._session_id:
            return self._refresh_session()
        try:
            body_str = json.dumps({}, separators=(",", ":"))
            headers = self._old_headers(body_str)
            resp = req_lib.post(f"{OLD_BASE}/pub/queryCurrentStaff",
                               data=body_str.encode("utf-8"),
                               headers=headers, verify=False, timeout=15)
            return resp.json().get("resultCode") == "200"
        except Exception:
            return False
    
    def get_staff_info(self):
        try:
            body_str = json.dumps({}, separators=(",", ":"))
            headers = self._old_headers(body_str)
            resp = req_lib.post(f"{OLD_BASE}/pub/queryCurrentStaff",
                               data=body_str.encode("utf-8"),
                               headers=headers, verify=False, timeout=15)
            result = resp.json()
            if result.get("resultCode") == "200":
                return result.get("data", {})
        except Exception:
            pass
        return None


crm = CRMClient()


# ============================================================
# Smart Query - Full Detail
# ============================================================
def smart_query(text):
    """
    Smart query with full detail:
    ICCID → /resmgr/card/qryNumCardInfoList → accNum → full query
    accNum → direct full query
    """
    input_type, value = detect_input_type(text)
    if input_type is None:
        return {"ok": False, "msg": "请输入查询内容"}
    
    acc_num = None
    iccid = None
    
    # Resolve to access number
    if input_type == 'iccid':
        iccid = value
        result = crm.old_post("/resmgr/card/qryNumCardInfoList", {"mktResInstNbrs": [iccid]})
        if result.get("resultCode") == "200" and result.get("data", {}).get("rspResult"):
            cards = result["data"]["rspResult"]
            if cards and cards[0].get("accNum"):
                acc_num = cards[0]["accNum"]
            else:
                return {"ok": False, "msg": f"ICCID {iccid} 未找到接入号"}
        else:
            return {"ok": False, "msg": f"ICCID查询失败: {result.get('resultMsg', '未知错误')}"}
    
    elif input_type == 'accnum':
        acc_num = value
    
    elif input_type == 'iccid_or_accnum':
        iccid = value
        result = crm.old_post("/resmgr/card/qryNumCardInfoList", {"mktResInstNbrs": [iccid]})
        if result.get("resultCode") == "200" and result.get("data", {}).get("rspResult"):
            cards = result["data"]["rspResult"]
            if cards and cards[0].get("accNum"):
                acc_num = cards[0]["accNum"]
        if not acc_num:
            acc_num = value
            iccid = None
    
    if not acc_num:
        return {"ok": False, "msg": "无法识别输入"}
    
    # === Query Customer ===
    cust_resp = crm.old_post("/cust/qryCustListTM", {
        "qryType": "accNum", "qryValue1": acc_num, "qryValue2": None,
        "isFuzzy": False, "isCaseSensitive": False,
        "pageIndex": 0, "pageSize": 10,
    })
    if cust_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询客户失败: {cust_resp.get('resultMsg')}"}
    
    cust_list = cust_resp.get("data", {}).get("custDetailList", [])
    if not cust_list:
        return {"ok": False, "msg": f"接入号 {acc_num} 未找到客户"}
    
    cust = cust_list[0].get("customer", {})
    cust_id = cust.get("custId", "")
    party_id = cust.get("partyId", "")
    shard2 = cust.get("shard2", "")
    cust_name = cust.get("custName", "")
    cust_number = cust.get("custNumber", "")
    cust_addr = cust.get("custAddr", "")
    
    # === Query Customer Detail (for region, bookId) ===
    region_id = 8331000
    book_id = 24
    cdtm_resp = crm.old_post("/cust/qryCustDetailTM", {
        "qryType": "custId", "qryValue1": cust_id, "qryValue2": party_id,
    })
    if cdtm_resp.get("resultCode") == "200":
        dc = cdtm_resp.get("data", {}).get("customer", {})
        cust_name = dc.get("custName", cust_name)
        cust_addr = dc.get("custAddr", cust_addr)
        if dc.get("regionId"):
            region_id = dc["regionId"]
        if dc.get("bookId"):
            book_id = dc["bookId"]
    
    # === Query Products ===
    prod_resp = crm.old_post("/cust/qryProdOfferInstList", {
        "qryType": "custId", "qryValue1": cust_id,
        "regionId": region_id, "regionType": "1300",
        "accNums": [acc_num], "pageIndex": 1, "pageSize": 10,
    })
    products = []
    target_prod = None
    if prod_resp.get("resultCode") == "200":
        products = prod_resp.get("data", {}).get("result", [])
        for p in products:
            if str(p.get("accNum")) == acc_num:
                target_prod = p
                break
        if not target_prod and products:
            target_prod = products[0]
    
    if not target_prod:
        return {
            "ok": True, "source": "old", "accNum": acc_num, "iccid": iccid,
            "customer": {"custId": cust_id, "custName": cust_name, "custNumber": cust_number,
                        "custAddr": cust_addr, "partyId": party_id, "shard2": shard2},
            "products": [], "cardInfo": {}, "orderedServices": [], "dirCodeInfo": None,
        }
    
    prod_inst_id = target_prod.get("prodInstId")
    prod_id = str(target_prod.get("prodId", ""))
    offer_id = target_prod.get("offerId")
    offer_name = target_prod.get("offerName", "")
    prod_name = target_prod.get("prodName", "")
    status_cd = target_prod.get("statusCd", "")
    status_desc = target_prod.get("statusCdDesc", "")
    uim_num = target_prod.get("uimNum", "") or ""
    prod_shard1 = str(target_prod.get("shard1", "") or "")
    
    # === Query Extended Attributes ===
    ext_attrs = {}
    ext_resp = crm.old_post("/order/qryProdInstExtInfos", {
        "prodInstId": prod_inst_id, "custId": cust_id, "bookId": int(book_id),
    })
    if ext_resp.get("resultCode") == "200":
        for attr in ext_resp.get("data", []):
            aid = str(attr.get("attrId", ""))
            aval = attr.get("attrValue", "")
            aname = _ATTR_NAME_MAP.get(aid, f"attr_{aid}")
            display_val = aval
            val_map = _ATTR_VALUE_MAP.get(aid, {})
            if val_map and str(aval) in val_map:
                display_val = f"{val_map[str(aval)]}({aval})"
            ext_attrs[aid] = {"name": aname, "value": aval, "displayValue": display_val}
    
    # === Query Product Detail (sub-products, IP, DNN, IMEI) ===
    ip_address = ""
    dnn_name = ""
    ordered_services = []
    imei = ""
    bind_status = ""
    
    detail_resp = crm.old_post("/order/qryOrdProdInstDetailInfo", {
        "qryValue1": str(prod_inst_id), "qryValue2": cust_id,
        "qryValue3": prod_shard1, "prodId": prod_id,
        "busiActQryParam": {"busiActId": 87},
        "queryScopes": ["40011001", "40017003", "subProd", "40011013", "40011003", "40017004"],
    })
    if detail_resp.get("resultCode") == "200":
        origin = detail_resp.get("data", {}).get("origin", [{}])
        if origin:
            for app_d in origin[0].get("appBaseOrdProdInstDetails", []):
                # Main attrs
                for attr in (app_d.get("ordProdInstAttrs") or []):
                    aid = attr.get("attrId")
                    aval = str(attr.get("attrValue", "") or "")
                    if aid == 10005028:
                        ip_address = aval
                    elif aid == 10005007:
                        dnn_name = aval
                    elif aid == 10020720:
                        bind_status = aval
                    elif aid == 10020616:
                        imei = aval
                
                # Sub-products (ordered services)
                sub = app_d.get("ordProdInst") or {}
                sub_pid = str(sub.get("prodId", ""))
                if sub_pid:
                    sub_attrs = []
                    for a in (app_d.get("ordProdInstAttrs") or []):
                        aid = str(a.get("attrId", ""))
                        aval = a.get("attrValue", "")
                        aname = _ATTR_NAME_MAP.get(aid, f"attr_{aid}")
                        display_val = aval
                        val_map = _ATTR_VALUE_MAP.get(aid, {})
                        if val_map and str(aval) in val_map:
                            display_val = f"{val_map[str(aval)]}({aval})"
                        sub_attrs.append({
                            "attrId": aid, "attrName": aname,
                            "value": aval, "displayValue": display_val,
                        })
                    ordered_services.append({
                        "prodId": sub_pid,
                        "prodName": _PROD_NAME_MAP.get(sub_pid, f"产品{sub_pid}"),
                        "prodInstId": sub.get("prodInstId"),
                        "attrs": sub_attrs,
                    })
    
    # === Get ICCID if not provided ===
    if not iccid:
        card_resp = crm.old_post("/resmgr/card/qryNumCardInfoList", {"mktResInstNbrs": [acc_num]})
        if card_resp.get("resultCode") == "200" and card_resp.get("data", {}).get("rspResult"):
            cards = card_resp["data"]["rspResult"]
            if cards:
                iccid = cards[0].get("iccid", "")
                if not uim_num:
                    uim_num = cards[0].get("limsi", "")
    
    # === Direction Code Info ===
    dir_code_info = _extract_dir_code(ordered_services, cust_id)
    
    # === Build result ===
    card_status = CARD_STATUS_MAP.get(status_cd, status_cd)
    
    return {
        "ok": True, "source": "old", "accNum": acc_num, "iccid": iccid,
        "customer": {
            "custId": cust_id, "custName": cust_name, "custNumber": cust_number,
            "custAddr": cust_addr, "partyId": party_id, "shard2": shard2,
        },
        "products": [{
            "offerName": p.get("offerName", ""), "prodName": p.get("prodName", ""),
            "accNum": str(p.get("accNum", "")), "statusCd": p.get("statusCd", ""),
            "statusCdDesc": p.get("statusCdDesc", ""), "prodId": str(p.get("prodId", "")),
        } for p in products],
        "cardInfo": {
            "statusCd": status_cd, "status": card_status,
            "offerName": offer_name, "prodName": prod_name,
            "prodId": prod_id, "prodInstId": str(prod_inst_id),
            "uimNum": uim_num, "imei": imei,
            "ipAddress": ip_address, "dnnName": dnn_name,
            "bindStatus": bind_status,
            "regionId": str(region_id), "bookId": str(book_id),
        },
        "orderedServices": ordered_services,
        "extAttrs": ext_attrs,
        "dirCodeInfo": dir_code_info,
    }


def _extract_dir_code(ordered_services, cust_id):
    """Extract direction code info from ordered services"""
    dir_code = ""
    apn_name = ""
    dir_type = ""
    
    for svc in ordered_services:
        pid = str(svc.get("prodId", ""))
        if pid == "13409902":  # 4G定向
            dir_type = "4G定向"
            for a in svc.get("attrs", []):
                if str(a.get("attrId")) == "10010078":
                    dir_code = str(a.get("value", ""))
                if str(a.get("attrId")) == "10020113":
                    apn_name = str(a.get("value", ""))
        elif pid == "13416110":  # 5G定向
            dir_type = "5G定向"
            for a in svc.get("attrs", []):
                if str(a.get("attrId")) == "10020088":
                    dir_code = str(a.get("value", ""))
        elif pid == "13416693":  # 5G定制专网DNN
            dir_type = "5G定制网"
            for a in svc.get("attrs", []):
                if str(a.get("attrId")) == "10010078":
                    dir_code = str(a.get("value", ""))
    
    if not dir_code:
        return None
    
    return {"dirCode": dir_code, "dirType": dir_type, "apnName": apn_name}


# ============================================================
# Unbind / Reinstate (imported from app_unbind.py)
# ============================================================
def _do_unbind(acc_num, reason):
    from app_unbind import do_unbind
    return do_unbind(acc_num, reason, crm)

def _do_reinstate(acc_num, reason):
    from app_unbind import do_reinstate
    return do_reinstate(acc_num, reason, crm)


# ============================================================
# API Routes
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "msg": "请输入查询内容"})
    return jsonify(smart_query(text))


@app.route("/api/batch_query", methods=["POST"])
def api_batch_query():
    data = request.json or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"ok": False, "msg": "请输入查询内容"})
    results = []
    for item in items:
        item = str(item).strip()
        if item:
            results.append(smart_query(item))
    return jsonify({"ok": True, "data": results})


@app.route("/api/unbind", methods=["POST"])
def api_unbind():
    data = request.json or {}
    acc_num = data.get("accNum", "").strip()
    reason = data.get("reason", "机卡解绑").strip()
    if not acc_num:
        return jsonify({"ok": False, "msg": "请输入接入号"})
    return jsonify(_do_unbind(acc_num, reason))


@app.route("/api/reinstate", methods=["POST"])
def api_reinstate():
    data = request.json or {}
    acc_num = data.get("accNum", "").strip()
    reason = data.get("reason", "违章复机").strip()
    if not acc_num:
        return jsonify({"ok": False, "msg": "请输入接入号"})
    return jsonify(_do_reinstate(acc_num, reason))


@app.route("/api/batch_unbind", methods=["POST"])
def api_batch_unbind():
    data = request.json or {}
    items = data.get("items", [])
    reason = data.get("reason", "批量解绑").strip()
    if not items:
        return jsonify({"ok": False, "msg": "请输入内容"})
    
    results = []
    for item in items:
        item = str(item).strip()
        if not item:
            continue
        # Auto-detect: ICCID → resolve → unbind
        input_type, value = detect_input_type(item)
        acc_num = None
        if input_type == 'iccid':
            r = crm.old_post("/resmgr/card/qryNumCardInfoList", {"mktResInstNbrs": [value]})
            if r.get("resultCode") == "200" and r.get("data", {}).get("rspResult"):
                cards = r["data"]["rspResult"]
                if cards and cards[0].get("accNum"):
                    acc_num = cards[0]["accNum"]
        elif input_type in ('accnum', 'iccid_or_accnum'):
            acc_num = value
        
        if not acc_num:
            results.append({"input": item, "ok": False, "msg": "无法识别"})
            continue
        
        r = _do_unbind(acc_num, reason)
        results.append({"input": item, "accNum": acc_num, **r})
    
    return jsonify({"ok": True, "data": results})


@app.route("/api/orders", methods=["POST"])
def api_orders():
    data = request.json or {}
    days = data.get("days", 3)
    staff_name = data.get("staffName", "").strip()
    page = data.get("page", 1)
    page_size = data.get("pageSize", 20)
    
    now = datetime.now()
    start = (now - timedelta(days=days)).strftime("%Y%m%d") + "000000"
    end = now.strftime("%Y%m%d") + "235959"
    
    body = {
        "pageIndex": page, "pageSize": page_size, "isNeedCount": 1,
        "custOrderStatusCd": None,
        "acceptStartDate": start, "acceptEndDate": end,
        "acceptProvinceId": 8330000, "acceptLanId": 8331000,
        "isGetMyOrder": 0, "createStaff": None,
        "belongCustId": "", "seletId": "combination",
    }
    
    result = crm.old_post("/pubquery/qryByComplexConditionNew", body, timeout=60)
    if result.get("resultCode") != "200":
        return jsonify({"ok": False, "msg": f"查询失败: {result.get('resultMsg')}"})
    
    resp_data = result.get("data", {})
    orders = resp_data.get("result", [])
    if staff_name:
        orders = [o for o in orders if staff_name in (o.get("createStaffName") or "")]
    
    status_map = {
        "100000": "待处理", "301200": "已完成", "401700": "已取消",
        "401300": "已取消", "301100": "处理中", "201100": "审核中",
    }
    
    return jsonify({
        "ok": True,
        "data": [{
            "orderNbr": str(o.get("custOrderNbr", "")),
            "orderId": o.get("custOrderId"),
            "statusCd": str(o.get("custOrderStatusCd", "")),
            "statusDesc": status_map.get(str(o.get("custOrderStatusCd", "")), str(o.get("custOrderStatusCd", ""))),
            "businessName": str(o.get("businessName", "")),
            "custName": str(o.get("custName", "")),
            "acceptDate": str(o.get("acceptDate", "")),
            "staffName": str(o.get("createStaffName", "")),
            "prodName": str(o.get("applyObjName", "")),
        } for o in orders],
        "total": resp_data.get("rowCount", 0),
        "page": page,
    })


@app.route("/api/session/status", methods=["GET"])
def api_session_status():
    staff = crm.get_staff_info()
    if staff:
        return jsonify({"ok": True, "loggedIn": True, "staff": staff})
    return jsonify({"ok": True, "loggedIn": False})


@app.route("/api/session/login", methods=["POST"])
def api_session_login():
    data = request.json or {}
    psession = data.get("psession", "").strip()
    if not psession:
        return jsonify({"ok": False, "msg": "请输入PSESSIONNEWID"})
    crm._session_id = psession
    crm._save_tokens()
    staff = crm.get_staff_info()
    if staff:
        return jsonify({"ok": True, "msg": "登录成功", "staff": staff})
    return jsonify({"ok": False, "msg": "Session无效或已过期"})


@app.route("/api/session/auto_login", methods=["POST"])
def api_auto_login():
    if crm._refresh_session():
        staff = crm.get_staff_info()
        return jsonify({"ok": True, "msg": "登录成功", "staff": staff})
    return jsonify({"ok": False, "msg": "自动登录失败"})


if __name__ == "__main__":
    log.info(f"IoT Lite starting on {cfg.HOST}:{cfg.PORT + 1}")
    app.run(host=cfg.HOST, port=cfg.PORT + 1, debug=cfg.DEBUG)
