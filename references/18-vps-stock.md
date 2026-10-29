# VPS 库存核对与缺货分流

## 固定入口与推荐顺序

系统选择统一沿用 [网络教程「选系统」](01-network.md#二选系统) 的 Debian 12 规则，三家商家一致；付款前核对所选系统，首次脚本部署读取实际系统验证。

1. 打开 [DMIT 实际订购目录](https://www.dmit.io/cart.php)，选 **Los Angeles → Premium → AS3 → LAX.AS3.Pro.TINY**。这是已成功交付的默认套餐，参考价 **10.90 美元/月**；本次金额读取实际页面。可直接打开 [已选分类](https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3)，打开后回读所选分类和完整型号。
2. 默认套餐缺货就查看 [搬瓦工 USCA_9、1 GB、季付](https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9)，这是有成熟适配经验的第二顺位，有货就首推搬瓦工。
3. 搬瓦工目标套餐也缺货，再看 [AKILE](https://akile.ai/) 的 LAX Premium → LAXPremium-Mini，默认月付。

原教程的 AN5、9.99 美元截图保留作界面操作示例；当前默认套餐按本章。原图、系统选择、SSH 和后续部署教学继续使用，图中价格与库存不覆盖当前查验。

## 实际页面怎样判断

- `cart.php` 的**当前目标套餐卡片**明确写“缺貨中／缺货／Out of Stock／Sold Out”，记录缺货；直接进入下一商家核对。
- 对应机房、线路、世代的**完整目录**没有目标套餐，记录“当前未列出”，进入下一商家；只加载了一部分页面时继续读取。
- 要说“有货、可以购买”，进入**同一套餐实际配置页**，回读完整型号、线路、月付或季付、本次金额、续费金额；当前页正常提供配置且没有缺货提示才成立。停在目录的购买按钮不算完成这一检查。
- 价格页 `pages/pricing`、首页、搜索结果摘要、历史截图只能介绍产品，不能作为库存证据。以同一时间的实际订购目录／配置页为准。
- Cloudflare 安全验证、403、超时记录“尚未核实”；只有页面明确要求登录才记录“要求登录”。打开普通浏览器，等自动检查结束再读页面；可复用客户已有登录页，或请客户提供当前目标套餐区域截图。若需要本人操作验证，让客户完成该动作后继续。仍未取得结果时可先核对下一家，前一家仍表述为“库存尚未核实”。
- 付款前重新读取同一页面。出现缺货或价格变化就更新检查结果、重新说明费用。

**本次验证：2026-10-29。**未登录浏览器右上角显示 Login，仍能在 `cart.php` 看到套餐及缺货；此前等待页是 Cloudflare 自动安全检查。登录浏览器与未登录浏览器中，LAX.AN5.T1.V2C2G 均明确缺货，尽管公开价格页显示 Order Now；默认 LAX.AS3.Pro.TINY 也显示缺货。这是回归案例，后续交付每次重查。

## 其他 DMIT 套餐确实有货时

先完成默认 DMIT 和搬瓦工的库存核对。其他 DMIT 套餐逐个读取其实际配置页；核对通过后才加入选项。DMIT 的其他世代、容量、Eyeball 和 Tier 1 都不自动替代已交付的默认套餐。

当搬瓦工有货，同时其他 DMIT 套餐也核实有货时，对客户这样说（型号和费用填本次实际结果）：

> DMIT 默认的 10.90 美元套餐目前缺货。搬瓦工这档已经核实可买，我们有成熟的适配经验，仍推荐您选搬瓦工。
>
> 另外，DMIT 的〔完整型号、线路、实际月付金额〕也核实可买，但这个套餐我们目前没有交付实践。您选推荐的搬瓦工，还是这档 DMIT？

如果其他套餐是 Tier 1，直接说明“这是 Tier 1，和默认的 Premium 优化线路不同”；Eyeball、其他世代或更高价档也按实际差异说明。客户选择以后沿用选择，原教程后续步骤保留。未核实的其他套餐不进入“有货”的选项。

## 控制层记录

在 `vps` 阶段先提交 `vps_origin=existing`（已有 VPS）或 `purchase`（本次购买）。客户说没有 VPS、提交 `access_ready=false` 时程序按本次购买处理。已有和旧版已完成服务器复用。

本次购买通过常规 `workflow.py submit --input ...` 提交 `purchase_checks`，键依次为 `dmit`、`bandwagon`、`akile`。每项取实际页面观察：

```json
{
  "plan": "LAX.AS3.Pro.TINY",
  "network": "Premium",
  "url": "https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3",
  "checked_at": "填写本次带时区的 ISO 时间",
  "page": "catalog",
  "status": "sold_out",
  "evidence": "LAX.AS3.Pro.TINY Out of Stock"
}
```

- `page`：`catalog`、`configuration`、`challenge`、`error`、`login`。
- `status`：`sold_out`、`not_listed`、`available`、`unknown`、`login_required`。`not_listed` 需 `catalog_complete=true`；`available` 需 `page=configuration`，并提供 `cycle`（`monthly`／`quarterly`）、正数 `amount`、正数 `renewal_amount`、`currency`（DMIT／搬瓦工 USD，AKILE CNY）。
- `evidence` 摘录当前目标套餐区域和配置页可见结果，包含完整套餐身份；搬瓦工的规范标识为 `USCA_9-1GB`（对应页面 USCA_9 与 1 GB），AKILE 为 `LAXPremium-Mini`。只记录产品信息，不记录账号、Cookie、令牌或付款资料。若页面跳转，`url` 使用跳转后的实际 URL；不能把价格页内容改标为购物车证据。
- 每次提交 `purchase_checks` 为完整检查映射，保留本轮仍有效的前序检查；商品身份、URL、缺货标签、周期和时间由 `scripts/vps_purchase.py` 核对。观察由 Codex 实际读取页面或客户截图取得，程序不代替浏览器读取实时库存。
- `purchase_decision` 返回下一家、检查原因、默认推荐和可购买状态。只有 `can_purchase=true` 才继续当前选定套餐的付款指引；随后确认 VPS 开通及 SSH 访问再提交 `access_ready=true`。
- 其他 DMIT 套餐放入 `dmit_alternatives` 列表，字段同上，状态必须为 `available`。程序独立校验实际配置页、完整型号、线路、月付费用与观察时间；仅通过核对的套餐出现在选项中。
- 默认 DMIT 缺货且存在已验证的其他 DMIT 选项时，程序保留搬瓦工优先级并等待选择。客户回复以后，以 `source.kind=user`、`source.reference` 记录原话，提交 `purchase_choice` 为完整套餐标识（例如推荐的 `USCA_9-1GB`，或已验证的 DMIT 其他型号）。程序不接受工具替客户选择；刷新页面后沿用客户选定型号，所选套餐缺货则重新选择，费用变化先说明当前金额。

三家均未取得可购买结果时，分别报告缺货与未核实的实际情况，再确认等待或其他已核实选项。完成购买后的库存变化不会把已交付的服务器退回购买阶段。
