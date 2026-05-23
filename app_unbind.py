#!/usr/bin/env python3
"""
Unbind and Reinstate operations - extracted and simplified
"""

import json
import time
import hashlib
import logging
import config as cfg

log = logging.getLogger("unbind")

DEFAULT_HANDLER = cfg.DEFAULT_HANDLER
_HANDLER_FALLBACK = cfg._HANDLER_FALLBACK


def _get_handler(crm, cust_id):
    """Get handler info: API → fallback → hardcoded"""
    handler_name = ""
    handler_cert = ""
    handler_addr = ""
    handler_cert_type = "1"
    contact_name = ""
    contact_num = ""
    
    # Try API
    cdtm = crm.old_post("/cust/qryCustDetailTM", {
        "qryType": "custId", "qryValue1": cust_id, "qryValue2": cust_id,
    })
    if cdtm.get("resultCode") == "200":
        ch = cdtm.get("data", {}).get("custHandler", {})
        if ch:
            handler_name = ch.get("name", "")
            handler_cert = ch.get("certNum", "")
            handler_cert_type = str(ch.get("certType", "1"))
            handler_addr = ch.get("certAddr", "")
    
    # Contact info
    cdt = crm.old_post("/cust/qryCustDetail", {
        "qryType": "custId", "qryValue1": cust_id, "qryValue2": cust_id,
    })
    if cdt.get("resultCode") == "200":
        contacts = cdt.get("data", {}).get("partyDetail", {}).get("contactsInfoDtls", [])
        for ct in (contacts or []):
            ci = ct.get("contactsInfo", {})
            if ci and ci.get("contactName"):
                contact_name = ci.get("contactName", "")
                contact_num = ci.get("phoneNbr", "")
                break
    
    # Fallback
    h = DEFAULT_HANDLER
    return {
        "handler": handler_name or h.get("handler") or _HANDLER_FALLBACK["handler"],
        "certType": handler_cert_type or h.get("certType") or _HANDLER_FALLBACK["certType"],
        "certNbr": handler_cert or h.get("certNbr") or _HANDLER_FALLBACK.get("certNbr", ""),
        "handlerCertAddr": handler_addr or h.get("handlerCertAddr") or _HANDLER_FALLBACK.get("handlerCertAddr", ""),
        "contactName": contact_name or h.get("contactName", ""),
        "contactNum": contact_num or h.get("contactNum", ""),
    }


def do_unbind(acc_num, reason, crm):
    """
    Unbind flow (old system, 9 steps):
    1. Query customer
    2. Query products
    3. Query business actions → get busiActId
    4. Pre-accept (preacpt) → MUST or backend rejects
    5. Get sequence ID
    6. Query product detail
    7. Get handler
    8. Rule check
    9. Submit + confirm order
    """
    log.info(f"[Unbind] Starting for {acc_num}")
    
    # Step 1: Query customer
    cust_resp = crm.old_post("/cust/qryCustListTM", {
        "qryType": "accNum", "qryValue1": acc_num, "qryValue2": None,
        "isFuzzy": False, "isCaseSensitive": False,
        "pageIndex": 0, "pageSize": 10,
    })
    if cust_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询客户失败: {cust_resp.get('resultMsg')}"}
    
    cust_list = cust_resp.get("data", {}).get("custDetailList", [])
    if not cust_list:
        return {"ok": False, "msg": "未找到客户"}
    
    cust = cust_list[0].get("customer", {})
    cust_id = cust.get("custId", "")
    party_id = cust.get("partyId", "")
    shard2 = cust.get("shard2", "")
    
    # Step 2: Query products
    prod_resp = crm.old_post("/cust/qryProdOfferInstList", {
        "qryType": "custId", "qryValue1": cust_id,
        "regionId": 8331000, "regionType": "1300",
        "accNums": [acc_num], "pageIndex": 1, "pageSize": 10,
    })
    if prod_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询产品失败: {prod_resp.get('resultMsg')}"}
    
    prod_results = prod_resp.get("data", {}).get("result", [])
    if not prod_results:
        return {"ok": False, "msg": "未找到产品实例"}
    
    target_prod = None
    for p in prod_results:
        if str(p.get("accNum")) == acc_num:
            target_prod = p
            break
    if not target_prod:
        target_prod = prod_results[0]
    
    prod_id = str(target_prod.get("prodId", ""))
    offer_id = str(target_prod.get("offerId", ""))
    prod_inst_id = target_prod.get("prodInstId", "")
    shard1 = str(target_prod.get("shard1", "14"))
    
    # Step 3: Query business actions
    busi_resp = crm.old_post("/busiact/qryBusiActList", {
        "accNum": acc_num, "prodId": prod_id,
    })
    busi_act_id = 87  # default
    if busi_resp.get("resultCode") == "200":
        acts = busi_resp.get("data", [])
        if acts:
            busi_act_id = acts[0].get("busiActId", 87)
    
    # Step 4: Pre-accept
    preacpt_resp = crm.old_post("/busiact/preacpt", {
        "accNum": acc_num, "prodId": prod_id,
        "busiActId": busi_act_id, "offerId": offer_id,
    })
    if preacpt_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"预受理失败: {preacpt_resp.get('resultMsg')}"}
    
    # Step 5: Get sequence ID
    seq_resp = crm.old_post("/pub/geneSeqId", {})
    if seq_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"获取序列号失败: {seq_resp.get('resultMsg')}"}
    seq_id = seq_resp.get("data", "")
    
    # Step 6: Query product detail
    detail_resp = crm.old_post("/order/qryOrdProdInstDetailInfo", {
        "prodInstId": str(prod_inst_id), "shard1": shard1, "accNum": acc_num,
    })
    if detail_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询产品详情失败: {detail_resp.get('resultMsg')}"}
    
    app_details = detail_resp.get("data", {}).get("appDetails", [])
    
    # Build subordinate products
    sub_prods = []
    for detail in app_details:
        sub = detail.get("ordProdInst") or {}
        sub_prod_id = str(sub.get("prodId", ""))
        sub_offer_id = str(sub.get("offerId", ""))
        sub_prod_inst_id = sub.get("prodInstId", "")
        sub_shard1 = str(sub.get("shard1", shard1))
        
        attrs = []
        for attr in detail.get("ordProdInstAttrs", []):
            oper_type = str(attr.get("operType", "1300"))
            attr_id = str(attr.get("attrId", ""))
            current_val = attr.get("value", "")
            
            if oper_type == "1200" and attr_id == "10020152":
                try:
                    current_val = str(int(current_val) + 1)
                except (ValueError, TypeError):
                    current_val = "1"
            
            attrs.append({
                "prodInstAttrId": attr.get("prodInstAttrId"),
                "attrId": attr_id,
                "attrName": attr.get("attrName", ""),
                "value": current_val,
                "operType": oper_type,
            })
        
        sub_prods.append({
            "prodId": sub_prod_id,
            "offerId": sub_offer_id,
            "prodInstId": str(sub_prod_inst_id),
            "shard1": sub_shard1,
            "accNum": acc_num,
            "attrs": attrs,
            "state": "100000",
        })
    
    # Step 7: Get handler
    handler = _get_handler(crm, cust_id)
    
    # Step 8: Rule check
    rule_resp = crm.old_post("/busirule/preAcpRule", {
        "accNum": acc_num, "custId": cust_id, "prodId": prod_id,
        "offerId": offer_id, "busiActId": busi_act_id,
        "partyId": party_id, "shard2": shard2,
    })
    if rule_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"规则校验失败: {rule_resp.get('resultMsg')}"}
    
    # Step 9: Submit order
    order_body = {
        "custOrderId": seq_id,
        "custId": cust_id,
        "partyId": party_id,
        "shard2": shard2,
        "accNum": acc_num,
        "prodId": prod_id,
        "offerId": offer_id,
        "busiActId": busi_act_id,
        "staffId": cfg.DEFAULT_HANDLER.get("staffId", ""),
        "regionId": 8331000,
        "remark": reason,
        "subProds": sub_prods,
        "handler": handler["handler"],
        "certType": handler["certType"],
        "certNbr": handler["certNbr"],
        "handlerCertAddr": handler["handlerCertAddr"],
        "contactName": handler["contactName"],
        "contactNum": handler["contactNum"],
    }
    
    order_resp = crm.old_post("/order/acceptCustomerOrder", order_body)
    if order_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"提交订单失败: {order_resp.get('resultMsg')}"}
    
    # Confirm
    order_id = order_resp.get("data", {}).get("custOrderId", seq_id)
    confirm_resp = crm.old_post("/order/confirmCustomerOrder", {
        "custOrderId": order_id, "remark": reason,
    })
    
    if confirm_resp.get("resultCode") == "200":
        return {"ok": True, "msg": "解绑成功", "orderId": order_id}
    
    return {"ok": False, "msg": f"确认订单失败: {confirm_resp.get('resultMsg')}"}


def do_reinstate(acc_num, reason, crm):
    """
    Reinstate (违章复机) - similar to unbind but with different busiActId (98)
    and serviceOfferId (4070200000), needs to read ordProdInstStates
    """
    log.info(f"[Reinstate] Starting for {acc_num}")
    
    # Step 1: Query customer
    cust_resp = crm.old_post("/cust/qryCustListTM", {
        "qryType": "accNum", "qryValue1": acc_num, "qryValue2": None,
        "isFuzzy": False, "isCaseSensitive": False,
        "pageIndex": 0, "pageSize": 10,
    })
    if cust_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询客户失败: {cust_resp.get('resultMsg')}"}
    
    cust_list = cust_resp.get("data", {}).get("custDetailList", [])
    if not cust_list:
        return {"ok": False, "msg": "未找到客户"}
    
    cust = cust_list[0].get("customer", {})
    cust_id = cust.get("custId", "")
    party_id = cust.get("partyId", "")
    shard2 = cust.get("shard2", "")
    
    # Step 2: Query products
    prod_resp = crm.old_post("/cust/qryProdOfferInstList", {
        "qryType": "custId", "qryValue1": cust_id,
        "regionId": 8331000, "regionType": "1300",
        "accNums": [acc_num], "pageIndex": 1, "pageSize": 10,
    })
    if prod_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询产品失败: {prod_resp.get('resultMsg')}"}
    
    prod_results = prod_resp.get("data", {}).get("result", [])
    if not prod_results:
        return {"ok": False, "msg": "未找到产品实例"}
    
    target_prod = None
    for p in prod_results:
        if str(p.get("accNum")) == acc_num:
            target_prod = p
            break
    if not target_prod:
        target_prod = prod_results[0]
    
    prod_id = str(target_prod.get("prodId", ""))
    offer_id = str(target_prod.get("offerId", ""))
    prod_inst_id = target_prod.get("prodInstId", "")
    shard1 = str(target_prod.get("shard1", "14"))
    
    busi_act_id = 98  # Reinstate specific
    service_offer_id = "4070200000"
    
    # Step 3: Pre-accept
    preacpt_resp = crm.old_post("/busiact/preacpt", {
        "accNum": acc_num, "prodId": prod_id,
        "busiActId": busi_act_id, "offerId": offer_id,
    })
    if preacpt_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"预受理失败: {preacpt_resp.get('resultMsg')}"}
    
    # Step 4: Get sequence ID
    seq_resp = crm.old_post("/pub/geneSeqId", {})
    if seq_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"获取序列号失败: {seq_resp.get('resultMsg')}"}
    seq_id = seq_resp.get("data", "")
    
    # Step 5: Query product detail
    detail_resp = crm.old_post("/order/qryOrdProdInstDetailInfo", {
        "prodInstId": str(prod_inst_id), "shard1": shard1, "accNum": acc_num,
    })
    if detail_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"查询产品详情失败: {detail_resp.get('resultMsg')}"}
    
    app_details = detail_resp.get("data", {}).get("appDetails", [])
    
    # Build subordinate products (reinstate needs ordProdInstStates)
    sub_prods = []
    for detail in app_details:
        sub = detail.get("ordProdInst") or {}
        sub_prod_id = str(sub.get("prodId", ""))
        sub_offer_id = str(sub.get("offerId", ""))
        sub_prod_inst_id = sub.get("prodInstId", "")
        sub_shard1 = str(sub.get("shard1", shard1))
        
        attrs = []
        for attr in detail.get("ordProdInstAttrs", []):
            oper_type = str(attr.get("operType", "1300"))
            attr_id = str(attr.get("attrId", ""))
            current_val = attr.get("value", "")
            attrs.append({
                "prodInstAttrId": attr.get("prodInstAttrId"),
                "attrId": attr_id,
                "attrName": attr.get("attrName", ""),
                "value": current_val,
                "operType": oper_type,
            })
        
        # ordProdInstStates for reinstate
        states = []
        for state in detail.get("ordProdInstStates", []):
            states.append({
                "stateId": state.get("stateId", ""),
                "stateType": state.get("stateType", ""),
                "stateValue": state.get("stateValue", ""),
            })
        
        sub_prods.append({
            "prodId": sub_prod_id,
            "offerId": sub_offer_id,
            "prodInstId": str(sub_prod_inst_id),
            "shard1": sub_shard1,
            "accNum": acc_num,
            "attrs": attrs,
            "states": states,
            "state": "100000",
        })
    
    # Step 6: Get handler
    handler = _get_handler(crm, cust_id)
    
    # Step 7: Submit order
    order_body = {
        "custOrderId": seq_id,
        "custId": cust_id,
        "partyId": party_id,
        "shard2": shard2,
        "accNum": acc_num,
        "prodId": prod_id,
        "offerId": offer_id,
        "busiActId": busi_act_id,
        "serviceOfferId": service_offer_id,
        "staffId": cfg.DEFAULT_HANDLER.get("staffId", ""),
        "regionId": 8331000,
        "remark": reason,
        "subProds": sub_prods,
        "handler": handler["handler"],
        "certType": handler["certType"],
        "certNbr": handler["certNbr"],
        "handlerCertAddr": handler["handlerCertAddr"],
        "contactName": handler["contactName"],
        "contactNum": handler["contactNum"],
    }
    
    order_resp = crm.old_post("/order/acceptCustomizedInfoOrder", order_body)
    if order_resp.get("resultCode") != "200":
        return {"ok": False, "msg": f"提交订单失败: {order_resp.get('resultMsg')}"}
    
    # Confirm
    order_id = order_resp.get("data", {}).get("custOrderId", seq_id)
    
    # Check if province audit needed
    crm.old_post("/orderdeal/judgeIfHasProvinceAduit", {
        "orderId": order_id, "orderType": busi_act_id,
    })
    
    confirm_resp = crm.old_post("/order/confirmCustomerOrder", {
        "custOrderId": order_id, "remark": reason,
    })
    
    if confirm_resp.get("resultCode") == "200":
        return {"ok": True, "msg": "复机成功", "orderId": order_id}
    
    return {"ok": False, "msg": f"确认订单失败: {confirm_resp.get('resultMsg')}"}
