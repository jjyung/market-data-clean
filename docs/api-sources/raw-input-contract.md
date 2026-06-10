# Raw Input Contract — 統一輸入格式

## 定位

本文件定義 **Adapter 層輸出 / Pipeline 核心輸入** 的統一欄位格式，支援兩種資料流：

```
                         ┌── OHLCV Pipeline ──→ Parser → Validator → Canonical Cleaned
                         │                          (data-contract.md)
Sinopac API ──→ Adapter ─┤
FinMind API ──→ Adapter ─┤
                         └── OrderBook Pipeline ──→ separate sink (optional)
```

Adapter 負責將各來源的原始格式正規化為此統一格式，之後的 parsing / validation 只依賴這個統一格式，不直接接觸來源細節。

---

## Pipeline A: OHLCV 市場資料（主要）

用於 K 線分析、回測等場景，支援盤後日資料與即時報價。

### 統一 Schema（OHLCV Pipeline）

| 欄位 | 型態 | 必要 | 說明 |
|---|---|---|---|
| `symbol` | `string` | ✅ | 商品代號，如 `TXFR1`、`2330` |
| `timestamp` | `datetime` (UTC) | ✅ | 時間戳，一律 UTC timezone-aware |
| `open` | `float` | ✅ | 開盤價 |
| `high` | `float` | ✅ | 最高價 |
| `low` | `float` | ✅ | 最低價 |
| `close` | `float` | ✅ | 收盤價 / 最新成交價 |
| `volume` | `int` | ✅ | 成交量（期貨：口，股票：股數） |
| `amount` | `float` | ❌ | 成交金額（元），來源若有則傳入 |
| `tick_type` | `int` | ❌ | 內外盤別 `{1: 外盤, 2: 內盤, 0: 不明}` |
| `price_chg` | `float` | ❌ | 漲跌點數 |
| `source` | `string` | ✅ | 資料來源標籤，如 `"sinopac"`、`"finmind"` |

### 命名規則

- 一律 **snake_case**（Adapter 負責 CamelCase → snake_case）
- `timestamp` 必須是 timezone-aware UTC datetime（`pandas.Timestamp` 或 Python `datetime`）
- `volume` 一律 `int`
- 數值欄位缺失（`None` / `NaN`）表示該筆不完整，由 pipeline 標記 rejected

---

## Pipeline B: OrderBook 即時報價（輔助）

用於盤中五檔分析、市場微結構研究。**不走 OHLCV 驗證 pipeline**，獨立處理。

### 統一 Schema（OrderBook Pipeline）

| 欄位 | 型態 | 必要 | 說明 |
|---|---|---|---|
| `symbol` | `string` | ✅ | 商品代號 |
| `timestamp` | `datetime` (UTC) | ✅ | 時間戳 |
| `bid_prices` | `list[float]` | ✅ | 五檔委買價（由高至低） |
| `bid_volumes` | `list[int]` | ✅ | 五檔委買量 |
| `ask_prices` | `list[float]` | ✅ | 五檔委賣價（由低至高） |
| `ask_volumes` | `list[int]` | ✅ | 五檔委賣量 |
| `bid_total_vol` | `int` | ❌ | 委買總量 |
| `ask_total_vol` | `int` | ❌ | 委賣總量 |
| `underlying_price` | `float` | ❌ | 標的指數現價（期貨專用） |
| `source` | `string` | ✅ | 資料來源標籤 |

---

## 資料來源對照總表 — OHLCV Pipeline

### 來自 Sinopac（永豐期貨即時 Tick / Quote）

| 統一欄位 | Sinopac Tick 來源 | 轉換 | Sinopac Quote 來源 | 轉換 |
|---|---|---|---|---|
| `symbol` | 訂閱參數 (`TXFR1`) | 直接取請求參數 | 同上 | 同上 |
| `timestamp` | `date` + `time` | 組合 → `tz_localize('Asia/Taipei').tz_convert('UTC')` | 同上 | 同上 |
| `open` | `open` | `Decimal` → `float` | `open` | 同上 |
| `high` | `high` | `Decimal` → `float` | `high` | 同上 |
| `low` | `low` | `Decimal` → `float` | `low` | 同上 |
| `close` | `close` | `Decimal` → `float` | `close` | 同上 |
| `volume` | `volume` | 單筆量（口），`int` | `volume` | 同上 |
| `amount` | `amount` | `Decimal` → `float` | `amount` | 同上 |
| `tick_type` | `tick_type` | 保留 `int` | `tick_type` | 同上 |
| `price_chg` | `price_chg` | `Decimal` → `float` | `price_chg` | 同上 |
| `source` | — | 固定 `"sinopac"` | — | 固定 `"sinopac"` |

### 來自 FinMind

| 統一欄位 | TaiwanFuturesDaily | TaiwanFuturesTick | taiwan_futures_snapshot |
|---|---|---|---|
| `symbol` | `futures_id` | `futures_id` | `futures_id` |
| `timestamp` | `date` → UTC | `date` → UTC（無時間） | `date` → UTC |
| `open` | `open` | — | `open` |
| `high` | `max` | — | `high` |
| `low` | `min` | — | `low` |
| `close` | `close` | `price` | `close` |
| `volume` | `volume` | `volume` | `total_volume` |
| `amount` | — | — | `total_amount` |
| `source` | `"finmind"` | `"finmind"` | `"finmind"` |

### 時間戳統一律定

| 來源 | 原始格式 | 時區 | 轉換方式 |
|---|---|---|---|
| Sinopac Tick (`date`+`time`) | `(2026,5,20)` + `(18,50,2,981000)` | UTC+8 本地 | `combine` → `tz_localize('Asia/Taipei')` → `tz_convert('UTC')` |
| FinMind Daily (`date`) | `"YYYY-MM-DD"` | 無時區（臺日） | `pd.to_datetime(date).tz_localize('Asia/Taipei').tz_convert('UTC')` |
| FinMind Tick (`date`) | `"YYYY-MM-DD"` | 無時區（臺日） | 同上（僅日期精度，無時間） |

---

## 與 Canonical Schema 的關係

| 層級 | 文件 | 說明 |
|---|---|---|
| Source Raw | `sinopac.md` / `finmind.md` | API 原始格式，Adapter 吸收差異 |
| **Unified Raw Input** | **`raw-input-contract.md`** | **Adapter 輸出，分 OHLCV 與 OrderBook 兩管道** |
| Canonical Cleaned | `data-contract.md` | Validator 驗證通過後的最終乾淨輸出 |

差異：
- Unified 的 `amount`、`tick_type`、`price_chg` 為 optional，canonical schema 不保證輸出
- OrderBook Pipeline 的資料不經 OHLCV validator，獨立處理
