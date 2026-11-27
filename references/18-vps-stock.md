# VPS 库存核对与缺货分流

**当前默认安排：**直接按 `workflow.py policy` 的 `current_recommendation` 推进——搬瓦工 USCA_9、2 GB、89.99 美元／三个月（附五张购买图解）。维护者统一核查库存，客户带做阶段直接进入注册、购买与开通。以下逐家核库存规则供维护检查和恢复 DMIT 优先时使用。

## 常规核对顺序与入口

新购系统统一选 **Debian 12**（见[网络教程「选系统」](01-network.md#二选系统)）：
1. **首选 DMIT**：打开 [DMIT 订购目录](https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3)，核对 **LAX.AS3.Pro.TINY**（月付参考 10.90 美元）。
2. **次选搬瓦工**：DMIT 目标套餐缺货时，查看 [搬瓦工 USCA_9 1 GB 季付](https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9)，有货即首推搬瓦工。

## 页面核对标准与采集

- **判有货**：进入目标套餐实际配置页（`page=configuration`），回读完整型号、线路、计费周期、本次金额与续费金额，且无缺货提示。
- **判缺货／未列出**：目标卡片标示缺货记录 `sold_out`；完整目录无该型号记录 `not_listed`；遇到验证页／超时记录 `unknown`（要求登录记 `login_required`）并可先查下一家。
- **其他有货的 DMIT 套餐**：逐个读取其配置页并验证后列入 `dmit_alternatives`，向客户清晰说明“搬瓦工已有成熟适配经验，仍优先推荐；另外查到 DMIT 的〔型号、线路、月付金额〕可买但尚无交付实践，请您二选一”。

采集步骤：将 `{"vendor":"dmit","url":"..."}` 写入 `.local/vps-page-input.json`，运行：
```bash
python3 scripts/workflow.py run --action vps_capture --input .local/vps-page-input.json
```
若遇浏览器渲染或验证页，由浏览器工具读取实际 `url` 与原始文本存为 `.local/vps-browser.json`，在输入中补充 `browser_file` 重跑采集。

## 控制层提交字段

在 `vps` 阶段先提交 `vps_origin=existing` 或 `purchase`。常规核对模式在 `purchase_checks`（键为 `dmit`、`bandwagon`）中引用本次采集 `receipt_id`、实际 `url`、`checked_at`、`page`、`status`、`evidence`（可购买时另附 `cycle`、`amount`、`renewal_amount`、`currency` 及 `billing_evidence`）。由 `purchase_decision` 返回下一家或 `can_purchase=true` 后再给付款指引；其他 DMIT 套餐与搬瓦工并存时由客户明确回复后以 `source.kind=user` 提交 `purchase_choice`。服务器开通且 SSH 就绪后提交 `access_ready=true`。
