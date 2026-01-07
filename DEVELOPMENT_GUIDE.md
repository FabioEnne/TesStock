# Stock Valuation App - Development Guide

## Business Logic Documentation

This document describes the business logic and domain rules for the Stock Valuation application. It is technology-agnostic and focuses on what the system does, not how it's implemented.

---

## 1. Application Purpose

The application calculates the **intrinsic value** (Fair Value) of stocks using discounted cash flow methods:

- **Dividend Discount Model (DDM)** - For dividend-paying stocks
- **Free Cash Flow Model (FCF)** - For growth stocks that don't pay dividends

### Core Value Proposition
- Help investors determine if a stock is undervalued, fairly valued, or overvalued
- Handle both traditional dividend stocks AND modern growth stocks
- Identify purely speculative stocks that cannot be valued fundamentally
- Demonstrate the impact of interest rate changes on valuations
- Provide educational examples to understand valuation concepts

---

## 2. Stock Classification Decision Tree

Before calculating value, classify the stock into one of three categories:

```
                    ┌─────────────────┐
                    │  Analyze Stock  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Pays Dividends? │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ YES                         │ NO
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │   Use DDM       │           │ Has Positive    │
    │   (Dividends)   │           │ Free Cash Flow? │
    └─────────────────┘           └────────┬────────┘
                                           │
                            ┌──────────────┴──────────────┐
                            │ YES                         │ NO
                            ▼                             ▼
                  ┌─────────────────┐           ┌─────────────────┐
                  │   Use FCF       │           │   SPECULATIVE   │
                  │   Model         │           │   (No Valuation)│
                  └─────────────────┘           └─────────────────┘
```

### Classification Rules

| Category | Condition | Valuation Method |
|----------|-----------|------------------|
| **DIVIDEND** | Annual Dividend > 0 | Dividend Discount Model |
| **GROWTH** | Dividend = 0 AND FCF per share > 0 | Free Cash Flow Model |
| **SPECULATIVE** | Dividend = 0 AND FCF ≤ 0 | Cannot value - pure speculation |

---

## 3. The Dividend Discount Model (DDM)

*Used for: Dividend-paying stocks (JNJ, KO, PG, T, etc.)*

### 3.1 The Formula

```
Fair Value = D₁ / (r - g)
```

Where:
| Symbol | Name | Description |
|--------|------|-------------|
| **D₁** | Expected Dividend | The dividend expected to be paid next year |
| **r** | Required Return | The investor's minimum acceptable annual return |
| **g** | Growth Rate | The expected annual growth rate of dividends |

### 3.2 Calculating D₁ (Next Year's Dividend)

```
D₁ = D₀ × (1 + g)
```

Where D₀ is the most recent annual dividend paid.

### 3.3 Model Constraints

| Constraint | Rule | Reason |
|------------|------|--------|
| r > g | Required return must exceed growth rate | Otherwise formula produces negative/infinite values |
| D₁ > 0 | Dividend must be positive | Model requires cash distributions |
| g ≥ 0 | Growth rate cannot be negative | Negative growth = declining dividends |
| g ≤ 15% | Growth rate capped at 15% | Unrealistically high growth is unsustainable |

---

## 4. The Free Cash Flow Model (FCF)

*Used for: Growth stocks without dividends (AMZN, META, GOOG, etc.)*

### 4.1 What is Free Cash Flow?

**Free Cash Flow (FCF)** = Cash from Operations - Capital Expenditures

In simple terms: The money left over after the company pays all its bills and investments. This is money that *could* be returned to shareholders (as dividends or buybacks) but is instead reinvested for growth.

### 4.2 The Formula

```
Fair Value = FCF₁ / (r - g)
```

Where:
| Symbol | Name | Description |
|--------|------|-------------|
| **FCF₁** | Expected FCF | Free Cash Flow expected next year (per share) |
| **r** | Required Return | The investor's minimum acceptable annual return |
| **g** | Growth Rate | The expected annual growth rate of FCF |

### 4.3 Calculating FCF₁

```
FCF₁ = FCF₀ × (1 + g)
```

Where FCF₀ is the most recent annual Free Cash Flow per share.

### 4.4 Model Constraints

| Constraint | Rule | Reason |
|------------|------|--------|
| r > g | Required return must exceed growth rate | Mathematical requirement |
| FCF₀ > 0 | FCF must be positive | Negative FCF = cash burn |
| g ≥ 0 | Growth rate cannot be negative | Negative growth not sustainable |
| g ≤ 20% | Growth rate capped at 20% | Higher cap than DDM (growth companies) |

### 4.5 Why FCF Works for Growth Stocks

Many modern companies (like Amazon for years, or AI startups today) choose to:
- **Not pay dividends** - reinvest everything
- **Generate positive cash flow** - profitable operations
- **Grow rapidly** - use cash for expansion

For these companies:
- DDM would say "cannot value" (no dividends)
- FCF model captures the value being created

---

## 5. Speculative Stocks

*Companies with no dividends AND no positive Free Cash Flow*

### 5.1 Characteristics

- Burning cash (negative FCF)
- No dividend payments
- Value based purely on future hopes
- Examples: Early-stage startups, pre-revenue companies, "meme stocks"

### 5.2 How to Handle

When a stock is classified as SPECULATIVE:

1. **Do NOT calculate Fair Value** - No fundamental basis exists
2. **Display clear warning** - User should understand the risk
3. **Show available data** - Price, financials, but no valuation

### 5.3 Warning Message

```
⚠️ SPECULATIVE STOCK

This company does not pay dividends and has no positive Free Cash Flow.

Without cash distributions or positive cash generation, there is no
fundamental basis to calculate intrinsic value. The current price is
driven purely by speculation - the hope that future cash flows will
eventually materialize.

Investing in speculative stocks carries significant risk. The price
could go to zero if expected growth never materializes.
```

---

## 6. Data Requirements

### 6.1 Stock Data (from Gemini LLM)

When a user provides a company name or ticker, query Gemini to obtain:

| Field | Description | Example | Used For |
|-------|-------------|---------|----------|
| `ticker` | Stock symbol | "AAPL" | Display |
| `company_name` | Full company name | "Apple Inc." | Display |
| `current_price` | Current market price | 185.50 | All models |
| `currency` | Price currency | "USD" | Display |
| `annual_dividend` | Annual dividend per share | 0.96 | DDM |
| `dividend_yield` | Dividend / Price | 0.52% | Display |
| `fcf_per_share` | Free Cash Flow per share | 6.73 | FCF Model |
| `dividend_growth_rate` | Historical dividend CAGR | 5.2% | DDM |
| `fcf_growth_rate` | Historical FCF CAGR | 12.5% | FCF Model |
| `sector` | Business sector | "Technology" | Display |
| `industry` | Specific industry | "Consumer Electronics" | Display |

### 6.2 Gemini Query Structure

```
For the company [COMPANY_NAME/TICKER], provide the following data:

BASIC INFO:
1. Current stock price and currency
2. Company sector and industry

DIVIDEND DATA:
3. Annual dividend per share (0 if none)
4. Dividend yield percentage
5. 5-year dividend growth rate (CAGR) if applicable

CASH FLOW DATA:
6. Free Cash Flow per share (most recent annual)
7. 5-year FCF growth rate (CAGR) if applicable

Please indicate clearly if:
- The company does not pay dividends
- The company has negative Free Cash Flow
- Data is not available for certain fields
```

### 6.3 Growth Rate Determination

For both models, growth rate (g) is determined in order of preference:

1. **From Gemini** - Historical CAGR (dividend or FCF)
2. **User Override** - Custom rate provided by user
3. **Default Values**:
   - DDM: 2% (conservative for mature dividend payers)
   - FCF: 5% (higher for growth companies)

---

## 7. Valuation Classification

### 7.1 Margin of Safety Calculation

```
Margin = ((Fair Value - Market Price) / Market Price) × 100
```

### 7.2 Classification Rules (Same for DDM and FCF)

| Margin | Classification | Meaning |
|--------|---------------|---------|
| > +10% | **UNDERVALUED** | Stock appears cheap |
| -10% to +10% | **FAIRLY VALUED** | Price aligns with value |
| < -10% | **OVERVALUED** | Stock appears expensive |

### 7.3 Stock Type Verdicts

| Stock Type | Possible Verdicts |
|------------|-------------------|
| DIVIDEND | UNDERVALUED, FAIRLY VALUED, OVERVALUED |
| GROWTH | UNDERVALUED, FAIRLY VALUED, OVERVALUED |
| SPECULATIVE | SPECULATIVE (no valuation possible) |

---

## 8. Sensitivity Analysis

### 8.1 Purpose

Show how Fair Value changes with different assumptions. Critical because:
- Small changes in g dramatically affect value
- Interest rate changes (r) impact all stocks
- Helps users understand model uncertainty

### 8.2 Parameter Ranges by Model

**DDM (Dividend Stocks):**
| Parameter | Range |
|-----------|-------|
| r | 6%, 7%, 8%, 9%, 10% |
| g | 1%, 2%, 3%, 4%, 5% |

**FCF (Growth Stocks):**
| Parameter | Range |
|-----------|-------|
| r | 8%, 9%, 10%, 11%, 12% |
| g | 3%, 5%, 7%, 10%, 12% |

*(Higher ranges for FCF because growth stocks typically have higher expected returns and growth)*

---

## 9. User Input Modes

### 9.1 Automatic Analysis (via Gemini)

**Input:**
- Company name or ticker symbol
- Required return (r) - default 8%
- Growth rate override (optional)

**Process:**
1. Query Gemini for stock data
2. Classify stock (DIVIDEND / GROWTH / SPECULATIVE)
3. If SPECULATIVE: Show warning, no valuation
4. If DIVIDEND: Apply DDM
5. If GROWTH: Apply FCF Model
6. Calculate Fair Value and classification
7. Generate sensitivity analysis

### 9.2 Manual Data Entry

**Input:**
- Company name, ticker
- Current price
- Annual dividend (can be 0)
- FCF per share (can be 0 or negative)
- Required return (r)
- Growth rate (g)

**Process:**
1. Validate inputs
2. Auto-classify based on dividend and FCF values
3. Apply appropriate model
4. Display results

---

## 10. Output Structure

### 10.1 For Dividend Stocks (DDM)

```
Stock Type: DIVIDEND STOCK
Model Used: Dividend Discount Model (DDM)

Stock Information:
  - Ticker: JNJ
  - Company: Johnson & Johnson
  - Sector: Healthcare

Financial Data:
  - Current Price: 155.50 USD
  - Annual Dividend: 4.76 USD
  - Dividend Yield: 3.06%

Model Parameters:
  - Required Return (r): 8.0%
  - Dividend Growth (g): 5.2%
  - Expected Dividend (D₁): 5.01 USD

Valuation Result:
  - Fair Value: 178.93 USD
  - Market Price: 155.50 USD
  - Margin: +15.1%
  - Verdict: UNDERVALUED
```

### 10.2 For Growth Stocks (FCF)

```
Stock Type: GROWTH STOCK
Model Used: Free Cash Flow Model (FCF)

Stock Information:
  - Ticker: AMZN
  - Company: Amazon.com Inc.
  - Sector: Consumer Cyclical

Financial Data:
  - Current Price: 178.25 USD
  - Annual Dividend: None
  - FCF per Share: 4.52 USD

Model Parameters:
  - Required Return (r): 10.0%
  - FCF Growth (g): 8.0%
  - Expected FCF (FCF₁): 4.88 USD

Valuation Result:
  - Fair Value: 244.00 USD
  - Market Price: 178.25 USD
  - Margin: +36.9%
  - Verdict: UNDERVALUED
```

### 10.3 For Speculative Stocks

```
Stock Type: SPECULATIVE
Model Used: None (Cannot Value)

Stock Information:
  - Ticker: RIVN
  - Company: Rivian Automotive
  - Sector: Automotive

Financial Data:
  - Current Price: 12.50 USD
  - Annual Dividend: None
  - FCF per Share: -8.25 USD (Negative)

⚠️ VALUATION NOT POSSIBLE

This company does not pay dividends and is currently burning cash
(negative Free Cash Flow). There is no fundamental basis for valuation.

The stock price is driven by speculation on future profitability.
Invest only what you can afford to lose.
```

---

## 11. Verdict Messages

### 11.1 Valuation Verdicts

| Verdict | Message |
|---------|---------|
| UNDERVALUED | "The stock appears undervalued. Fair Value ({fv}) exceeds Market Price ({mp})." |
| FAIRLY VALUED | "The stock is fairly valued. Price aligns with fundamentals." |
| OVERVALUED | "The stock appears overvalued. Market Price ({mp}) exceeds Fair Value ({fv})." |

### 11.2 Stock Type Messages

| Type | Message |
|------|---------|
| DIVIDEND | "Using Dividend Discount Model - this company returns cash to shareholders via dividends." |
| GROWTH | "Using Free Cash Flow Model - this company reinvests profits instead of paying dividends." |
| SPECULATIVE | "No valuation model applicable - this stock is purely speculative." |

---

## 12. Business Rules Summary

### 12.1 Input Validation

| Field | Rule |
|-------|------|
| Current Price | Must be > 0 |
| Dividend | Must be ≥ 0 |
| FCF per Share | Any value (can be negative) |
| Required Return (r) | Between 1% and 30% |
| Growth Rate (g) | Between 0% and 20% (25% for FCF) |
| r vs g | r must be > g for valuation |

### 12.2 Default Values

| Parameter | DDM Default | FCF Default |
|-----------|-------------|-------------|
| Required Return (r) | 8% | 10% |
| Growth Rate (g) | 2% | 5% |
| Valuation Threshold | 10% | 10% |

### 12.3 Classification Priority

If a company pays dividends AND has positive FCF:
- **Use DDM** (dividend model takes priority)
- Rationale: Actual cash returned to shareholders is more reliable than potential cash

---

## 13. Error Handling

### 13.1 Data Errors

| Scenario | Action |
|----------|--------|
| Company not found | Show error, suggest checking ticker |
| Gemini unavailable | Offer manual entry mode |
| Partial data | Use available data, note limitations |

### 13.2 Calculation Errors

| Scenario | Action |
|----------|--------|
| g ≥ r | Prompt user to adjust (growth too high or return too low) |
| Negative price | Reject input |
| Invalid numbers | Show validation error |

---

## 14. Limitations & Disclaimers

### 14.1 Model Limitations

**DDM assumes:**
- Dividends grow at constant rate forever
- Company continues paying indefinitely

**FCF Model assumes:**
- FCF grows at constant rate forever
- Cash generation continues indefinitely

**Reality:** Growth rates change, companies pivot, disruption happens.

### 14.2 Speculative Stock Warning

For speculative stocks, always emphasize:
- No fundamental floor on price
- Value could go to zero
- Only invest what you can afford to lose
- This is gambling, not investing

### 14.3 Required Disclaimer

Always display:
> "This analysis is for educational purposes only. Valuation models depend heavily on assumptions that may not reflect reality. This does not constitute financial advice. Past performance does not guarantee future results."

---

## 15. Example Stock Classifications

| Company | Dividend | FCF | Classification | Model |
|---------|----------|-----|----------------|-------|
| Johnson & Johnson | $4.76 | $7.50 | DIVIDEND | DDM |
| Coca-Cola | $1.84 | $2.20 | DIVIDEND | DDM |
| Amazon | $0 | $4.52 | GROWTH | FCF |
| Google | $0 | $5.80 | GROWTH | FCF |
| Uber | $0 | -$0.50 | SPECULATIVE | None |
| Rivian | $0 | -$8.25 | SPECULATIVE | None |
| WeWork (pre-crash) | $0 | -$15.00 | SPECULATIVE | None |

---

## 16. Summary: The Three Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                     STOCK VALUATION PATHS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💰 DIVIDEND STOCKS          📈 GROWTH STOCKS                   │
│  ─────────────────          ─────────────────                   │
│  Pay dividends              No dividends                        │
│  Mature companies           Reinvest everything                 │
│  Value = D₁/(r-g)          Value = FCF₁/(r-g)                  │
│  Examples: JNJ, KO, PG      Examples: AMZN, META                │
│                                                                 │
│                    🎲 SPECULATIVE STOCKS                        │
│                    ─────────────────────                        │
│                    No dividends                                 │
│                    Negative cash flow                           │
│                    No fundamental value                         │
│                    Pure speculation                             │
│                    Examples: Pre-profit startups                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
