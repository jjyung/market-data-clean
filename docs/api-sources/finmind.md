# FinMind API — 期貨資料 Input Format

## 概述

使用 [FinMind](https://finmind.github.io/) 開放 API 取得臺灣期貨資料。  
本專案主要使用以下資料集：

| 資料集 | 類型 | 說明 |
|---|---|---|
| `TaiwanFuturesDaily` | 盤後日資料 | 每日開高低收、成交量、結算價、未平倉量 |
| `TaiwanFuturesTick` | 歷史逐筆明細 | 每筆成交價格與數量 |
| `taiwan_futures_snapshot` | 即時快照 | 盤中期貨即時報價快照（Sponsor 方案） |

---

## 1. TaiwanFuturesDaily（期貨日成交資訊）

盤後每日結算資料，含開高低收、成交量、結算價、未平倉量。

### API

```
GET https://api.finmindtrade.com/api/v4/data
  ?dataset=TaiwanFuturesDaily
  &data_id=TX
  &start_date=2020-04-01
  &end_date=2020-04-12
```

### 欄位

| 欄位 | 型態 | 說明 |
|---|---|---|
| `date` | `string` | 日期 `YYYY-MM-DD` |
| `futures_id` | `string` | 期貨代碼（如 `TX`、`MTX`、`TXF`） |
| `contract_date` | `string` | 到期月份（如 `202606`） |
| `open` | `float` | 開盤價 |
| `max` | `float` | 最高價 |
| `min` | `float` | 最低價 |
| `close` | `float` | 收盤價 |
| `spread` | `float` | 漲跌點數 |
| `spread_per` | `float` | 漲跌幅（%） |
| `volume` | `int` | 成交量（口） |
| `settlement_price` | `float` | 結算價 |
| `open_interest` | `int` | 未平倉量（口） |
| `trading_session` | `string` | 交易時段（`Regular` / `AfterHours` / `All`） |

### JSON 範例

```json
{
  "data": [
    {
      "date": "2026-05-20",
      "futures_id": "TX",
      "contract_date": "202606",
      "open": 40270.0,
      "max": 40650.0,
      "min": 40221.0,
      "close": 40629.0,
      "spread": 505.0,
      "spread_per": 1.2586,
      "volume": 14348,
      "settlement_price": 40610.0,
      "open_interest": 98765,
      "trading_session": "Regular"
    }
  ]
}
```

---

## 2. TaiwanFuturesTick（期貨交易明細表）

歷史逐筆成交明細（tick 級），每次查詢單日資料。

### API

```
GET https://api.finmindtrade.com/api/v4/data
  ?dataset=TaiwanFuturesTick
  &data_id=MTX
  &start_date=2020-04-01
```

### 欄位

| 欄位 | 型態 | 說明 |
|---|---|---|
| `date` | `string` | 日期 `YYYY-MM-DD` |
| `futures_id` | `string` | 期貨代碼 |
| `contract_date` | `string` | 到期月份 |
| `price` | `float` | 成交價 |
| `volume` | `int` | 成交量（口） |

### JSON 範例

```json
{
  "data": [
    {
      "date": "2026-05-20",
      "futures_id": "MTX",
      "contract_date": "202606",
      "price": 40600.0,
      "volume": 1
    },
    {
      "date": "2026-05-20",
      "futures_id": "MTX",
      "contract_date": "202606",
      "price": 40605.0,
      "volume": 2
    }
  ]
}
```

---

## 3. taiwan_futures_snapshot（台股期貨即時資訊）

盤中期貨即時快照（Sponsor 方案），含即時五檔資訊。

### API

```
GET https://api.finmindtrade.com/api/v4/data
  ?dataset=taiwan_futures_snapshot
  &data_id=TXF
```

`data_id` 可為空（取得所有期貨快照）。

### 欄位

| 欄位 | 型態 | 說明 |
|---|---|---|
| `date` | `string` | 日期 |
| `futures_id` | `string` | 期貨代碼 |
| `open` | `float` | 開盤價 |
| `high` | `float` | 最高價 |
| `low` | `float` | 最低價 |
| `close` | `float` | 最新成交價 |
| `change_price` | `float` | 漲跌點數 |
| `change_rate` | `float` | 漲跌幅（%） |
| `average_price` | `float` | 均價 |
| `volume` | `int` | 單量（口） |
| `total_volume` | `int` | 總量（口） |
| `amount` | `int` | 單筆成交額（元） |
| `total_amount` | `int` | 總成交額（元） |
| `yesterday_volume` | `float` | 昨量 |
| `buy_price` | `float` | 委買價 |
| `buy_volume` | `float` | 委買量 |
| `sell_price` | `float` | 委賣價 |
| `sell_volume` | `int` | 委賣量 |
| `volume_ratio` | `float` | 昨量比 |
| `TickType` | `string` | 買賣別 |

---

## Adapter 對應規則

### i. TaiwanFuturesDaily → 統一 Raw Input（盤後）

| 統一欄位 | FinMind 來源 | 轉換邏輯 |
|---|---|---|
| `symbol` | `futures_id` | 直接取值 |
| `timestamp` | `date` | `pd.to_datetime(date).tz_localize('Asia/Taipei').tz_convert('UTC')` |
| `open` | `open` | 直接取值 |
| `high` | `max` | 直接取值 |
| `low` | `min` | 直接取值 |
| `close` | `close` | 直接取值 |
| `volume` | `volume` | 確保為 `int` |
| `source` | — | 固定 `"finmind"` |

### ii. TaiwanFuturesTick → 統一 Raw Input（歷史 tick）

| 統一欄位 | FinMind 來源 | 轉換邏輯 |
|---|---|---|
| `symbol` | `futures_id` | 直接取值 |
| `timestamp` | `date` + `time` | 日期 UTC 化（FinMind tick 無時戳細節，僅有日期） |
| `close` | `price` | 成交價 |
| `volume` | `volume` | 單筆成交量（口） |
| `source` | — | 固定 `"finmind"` |

### iii. taiwan_futures_snapshot → 統一 Raw Input（即時）

| 統一欄位 | FinMind 來源 | 轉換邏輯 |
|---|---|---|
| `symbol` | `futures_id` | 直接取值 |
| `timestamp` | `date` | 日期 UTC 化 |
| `open` | `open` | 直接取值 |
| `high` | `high` | 直接取值 |
| `low` | `low` | 直接取值 |
| `close` | `close` | 最新成交價 |
| `volume` | `total_volume` | 累計成交量（口） |
| `amount` | `total_amount` | 累計成交額 |
| `source` | — | 固定 `"finmind"` |

---

## 與 Unified Raw Input 的關係

詳見 `raw-input-contract.md`。

---

## 注意事項

- FinMind `date` 為無時區日期字串（代表臺灣交易日），Adapter 先 `tz_localize('Asia/Taipei')` 再轉 UTC。
- `TaiwanFuturesTick` 無 `time` 欄位（僅有日期），無法對應到 Sinopac Tick 的毫秒級時間精度。
- `taiwan_futures_snapshot` 為 **Sponsor 方案** 才能存取。
- 期貨代碼（`futures_id`）如 `TX`（臺股期貨）、`MTX`（小型臺指期貨）、`TXF`（臺指期貨，snapshot 用）。
