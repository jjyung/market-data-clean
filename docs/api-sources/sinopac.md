# 永豐 API (Sinopac) — 期貨即時報價 Input Format

## 概述

使用永豐證券 **shioaji** SDK 訂閱臺灣期貨交易所（TAIFEX）即時行情。  
透過 `api.subscribe()` 可接收三種報價類型：

| 類型 | 物件 | 說明 |
|---|---|---|
| **Tick** | `TickFOPv1` | 每筆成交明細（逐筆洗價） |
| **BidAsk** | `BidAskFOPv1` | 五檔委買委賣即時報價 |
| **Quote** | `QuoteFOPv1` | 綜合報價（含成交 + 五檔） |

訂閱方式：

```python
contract = api.Contracts.Futures.TXF.TXFR1  # 台指期近月
api.subscribe(contract, quote_type=sj.QuoteType.Tick)    # 或 BidAsk / Quote
```

---

## 1. Tick（逐筆成交明細）— `TickFOPv1`

即時推送每一筆成交資料，用於盤中 tick 級分析。

### 欄位

| 欄位 | 型態 | 說明 |
|---|---|---|
| `code` | `str` | 商品代碼（如 `TXFF6`） |
| `exchange` | `Exchange` | 交易所（`TAIFEX`） |
| `date` | `tuple` | 日期 `(year, month, day)` |
| `time` | `tuple` | 時間 `(hour, min, sec, microsec)` |
| `datetime` | `tuple` | 完整日期時間 |
| `open` | `Decimal` | 開盤價 |
| `underlying_price` | `Decimal` | 標的指數現價（大盤即時） |
| `avg_price` | `Decimal` | 當日均價 |
| `close` | `Decimal` | 成交價 |
| `high` | `Decimal` | 當日最高價 |
| `low` | `Decimal` | 當日最低價 |
| `amount` | `Decimal` | 單筆成交額（NTD） |
| `total_amount` | `Decimal` | 當日總成交額（NTD） |
| `volume` | `int` | 單筆成交量（口） |
| `total_volume` | `int` | 當日總成交量（口） |
| `tick_type` | `int` | 內外盤別 `{1: 外盤, 2: 內盤, 0: 無法判定}` |
| `chg_type` | `int` | 漲跌註記 `{1: 漲停, 2: 漲, 3: 平盤, 4: 跌, 5: 跌停}` |
| `price_chg` | `Decimal` | 漲跌點數（相較昨收） |
| `pct_chg` | `Decimal` | 漲跌幅（%） |
| `bid_side_total_vol` | `int` | 買盤成交累計量（口） |
| `ask_side_total_vol` | `int` | 賣盤成交累計量（口） |
| `simtrade` | `bool` | 是否為試撮 |

### JSON 範例

```json
{
  "code": "TXFF6",
  "date": "2026-05-20",
  "time": "18:50:02.981000",
  "open": "40270",
  "underlying_price": "40020.82",
  "bid_side_total_vol": 7498,
  "ask_side_total_vol": 5817,
  "avg_price": "40460.163149",
  "close": "40619",
  "high": "40650",
  "low": "40221",
  "amount": "81238",
  "total_amount": "552038466",
  "volume": 2,
  "total_volume": 13644,
  "tick_type": 1,
  "chg_type": 2,
  "price_chg": "495",
  "pct_chg": "1.233676",
  "simtrade": false
}
```

---

## 2. BidAsk（五檔委買委賣）— `BidAskFOPv1`

即時推送最佳五檔買賣報價。

### 欄位

| 欄位 | 型態 | 說明 |
|---|---|---|
| `code` | `str` | 商品代碼 |
| `exchange` | `Exchange` | 交易所 |
| `date` | `tuple` | 日期 |
| `time` | `tuple` | 時間 |
| `datetime` | `tuple` | 完整日期時間 |
| `bid_total_vol` | `int` | 委買總量（口） |
| `ask_total_vol` | `int` | 委賣總量（口） |
| `bid_price` | `list[Decimal]` | 五檔委買價（由高至低） |
| `bid_volume` | `list[int]` | 五檔委買量（口） |
| `diff_bid_vol` | `list[int]` | 五檔委買增減量（口） |
| `ask_price` | `list[Decimal]` | 五檔委賣價（由低至高） |
| `ask_volume` | `list[int]` | 五檔委賣量（口） |
| `diff_ask_vol` | `list[int]` | 五檔委賣增減量（口） |
| `first_derived_bid_price` | `Decimal` | 衍生一檔委買價 |
| `first_derived_ask_price` | `Decimal` | 衍生一檔委賣價 |
| `first_derived_bid_vol` | `int` | 衍生一檔委買量 |
| `first_derived_ask_vol` | `int` | 衍生一檔委賣量 |
| `underlying_price` | `Decimal` | 標的指數現價 |
| `simtrade` | `bool` | 試撮 |

### JSON 範例

```json
{
  "code": "TXFF6",
  "date": "2026-05-20",
  "time": "19:24:03.012000",
  "bid_total_vol": 8,
  "ask_total_vol": 19,
  "bid_price": ["40615", "40613", "40612", "40611", "40610"],
  "bid_volume": [1, 2, 1, 2, 2],
  "diff_bid_vol": [0, 0, 0, 0, 1],
  "ask_price": ["40618", "40619", "40620", "40621", "40622"],
  "ask_volume": [6, 2, 3, 2, 6],
  "diff_ask_vol": [0, -1, -1, 0, 0],
  "first_derived_bid_price": "0",
  "first_derived_ask_price": "40622",
  "first_derived_bid_vol": 0,
  "first_derived_ask_vol": 1,
  "underlying_price": "40020.82",
  "simtrade": false
}
```

---

## 3. Quote（綜合報價）— `QuoteFOPv1`

結合 Tick + BidAsk 的綜合報價，一次推送所有市場資料。

### 欄位

含 Tick 全部欄位，並加上以下五檔與筆數資訊：

| 額外欄位 | 型態 | 說明 |
|---|---|---|
| `bid_side_total_cnt` | `int` | 買盤成交筆數 |
| `ask_side_total_cnt` | `int` | 賣盤成交筆數 |
| `bid_price` | `list[Decimal]` | 五檔委買價 |
| `bid_volume` | `list[int]` | 五檔委買量 |
| `diff_bid_vol` | `list[int]` | 五檔委買增減量 |
| `ask_price` | `list[Decimal]` | 五檔委賣價 |
| `ask_volume` | `list[int]` | 五檔委賣量 |
| `diff_ask_vol` | `list[int]` | 五檔委賣增減量 |
| `first_derived_bid_price` | `Decimal` | 衍生一檔委買價 |
| `first_derived_ask_price` | `Decimal` | 衍生一檔委賣價 |
| `first_derived_bid_vol` | `int` | 衍生一檔委買量 |
| `first_derived_ask_vol` | `int` | 衍生一檔委賣量 |

其餘同一級 Tick 欄位（`open`、`close`、`high`、`low`、`volume`、`tick_type` 等）。

### JSON 範例

```json
{
  "code": "TXFF6",
  "date": "2026-05-20",
  "time": "19:29:39.887000",
  "underlying_price": "40020.82",
  "open": "40270",
  "avg_price": "40466.730155",
  "close": "40616",
  "high": "40650",
  "low": "40221",
  "amount": "40616",
  "total_amount": "578107707",
  "volume": 0,
  "total_volume": 14286,
  "tick_type": 1,
  "chg_type": 2,
  "price_chg": "492",
  "pct_chg": "1.226199",
  "bid_side_total_vol": 7773,
  "ask_side_total_vol": 6172,
  "bid_side_total_cnt": 9924,
  "ask_side_total_cnt": 10442,
  "bid_price": ["40613", "40612", "40611", "40610", "40609"],
  "bid_volume": [2, 4, 6, 2, 4],
  "diff_bid_vol": [0, 0, 0, 0, 0],
  "ask_price": ["40617", "40618", "40619", "40620", "40621"],
  "ask_volume": [6, 7, 3, 4, 3],
  "diff_ask_vol": [0, 0, 0, 0, 0],
  "first_derived_bid_price": "0",
  "first_derived_ask_price": "0",
  "first_derived_bid_vol": 0,
  "first_derived_ask_vol": 0,
  "simtrade": false
}
```

---

## Adapter 對應規則

### i. Tick → 統一 Raw Input

| 統一欄位 | Tick 來源 | 轉換邏輯 |
|---|---|---|
| `symbol` | `code` | 取 requests 參數（如 `TXFR1`） |
| `timestamp` | `date` + `time` | 組合為 datetime → `tz_localize('Asia/Taipei').tz_convert('UTC')` |
| `open` | `open` | `Decimal` → `float` |
| `high` | `high` | `Decimal` → `float` |
| `low` | `low` | `Decimal` → `float` |
| `close` | `close` | `Decimal` → `float` |
| `volume` | `volume` | 單筆成交量（口），保留 `int` |
| `amount` | `amount` | `Decimal` → `float`（單筆成交額） |
| `source` | — | 固定 `"sinopac"` |
| `tick_type` | `tick_type` | 內外盤別，保留 `int` |
| `price_chg` | `price_chg` | `Decimal` → `float` |

### ii. BidAsk → 統一 Raw Input（order_book）

BidAsk 不經過 OHLCV pipeline，透過獨立 order_book 管道處理。

| 統一欄位 | BidAsk 來源 | 轉換邏輯 |
|---|---|---|
| `symbol` | `code` | 取 requests 參數 |
| `timestamp` | `date` + `time` | 組合為 UTC datetime |
| `bid_prices` | `bid_price` | `list[Decimal]` → `list[float]` |
| `bid_volumes` | `bid_volume` | `list[int]`，保留 |
| `ask_prices` | `ask_price` | `list[Decimal]` → `list[float]` |
| `ask_volumes` | `ask_volume` | `list[int]`，保留 |
| `bid_total_vol` | `bid_total_vol` | 委買總量（口） |
| `ask_total_vol` | `ask_total_vol` | 委賣總量（口） |
| `underlying_price` | `underlying_price` | `Decimal` → `float` |
| `source` | — | 固定 `"sinopac"` |

### iii. Quote → 統一 Raw Input

Quote 是 Tick + BidAsk 的合併，同時對應兩個 pipeline。

---

## 與 Unified Raw Input 的關係

詳見 `raw-input-contract.md`。

```
Sinopac Tick ──→ raw OHLCV fields ──→ Pipeline (parser → validator → canonical)
Sinopac BidAsk ──→ raw order_book fields ──→ separate order book pipeline (optional)
```

---

## 注意事項

- 即時行情只在 **開盤時段** 推送，盤後無資料。
- `TickFOPv1` / `BidAskFOPv1` / `QuoteFOPv1` 的 `date` 與 `time` 為 UTC+8 本地時間，Adapter 需轉 UTC。
- 連續月（`TXFR1` / `TXFR2`）shioaji 自動解析實際代碼（如 `TXFF6`）；HTTP API 需指定 `target_code`。
- 期貨 `volume` 單位為 **口（lot）**，非股數。
- 期貨無 `adj_close`（還權）概念。
