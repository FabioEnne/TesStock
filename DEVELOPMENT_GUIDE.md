# Stock Valuation App - Development Guide

## Business Logic Documentation

This document describes the business logic and domain rules for the Stock Valuation application. It is technology-agnostic and focuses on what the system does, not how it's implemented.

---

## 1. Application Purpose

The application calculates the **intrinsic value** (Fair Value) of dividend-paying stocks using the **Dividend Discount Model (DDM)**, specifically the **Gordon Growth Model (GGM)**.

### Core Value Proposition
- Help investors determine if a stock is undervalued, fairly valued, or overvalued
- Demonstrate the impact of interest rate changes on stock valuations
- Provide educational examples to understand valuation concepts

---

## 2. The Gordon Growth Model

### 2.1 The Formula

```
Fair Value = D₁ / (r - g)
```

Where:
| Symbol | Name | Description |
|--------|------|-------------|
| **D₁** | Expected Dividend | The dividend expected to be paid next year |
| **r** | Required Return | The investor's minimum acceptable annual return (discount rate) |
| **g** | Growth Rate | The expected annual growth rate of dividends |

### 2.2 Calculating D₁ (Next Year's Dividend)

```
D₁ = D₀ × (1 + g)
```

Where D₀ is the most recent annual dividend paid.

### 2.3 Model Constraints

The model has mathematical constraints that must be enforced:

| Constraint | Rule | Reason |
|------------|------|--------|
| r > g | Required return must exceed growth rate | Otherwise formula produces negative or infinite values |
| D₁ > 0 | Dividend must be positive | Model only works for dividend-paying stocks |
| g ≥ 0 | Growth rate cannot be negative | Negative growth means declining dividends |
| g ≤ 15% | Growth rate capped at 15% | Unrealistically high growth is unsustainable |

### 2.4 When the Model is Not Applicable

Return "Not Applicable" status when:
- Company does not pay dividends (D₀ = 0)
- Growth rate equals or exceeds required return (g ≥ r)
- Insufficient data to calculate parameters

---

## 3. Data Requirements

### 3.1 Stock Data (from Gemini LLM)

When a user provides a company name or ticker, query Gemini to obtain:

| Field | Description | Example |
|-------|-------------|---------|
| `ticker` | Stock symbol | "JNJ" |
| `company_name` | Full company name | "Johnson & Johnson" |
| `current_price` | Current market price per share | 155.50 |
| `currency` | Price currency | "USD" |
| `annual_dividend` | Most recent annual dividend per share (D₀) | 4.76 |
| `dividend_yield` | Annual dividend / Current price | 0.0306 (3.06%) |
| `sector` | Business sector | "Healthcare" |
| `industry` | Specific industry | "Drug Manufacturers" |

### 3.2 Dividend Growth Rate Calculation

The growth rate (g) can be obtained in three ways, in order of preference:

1. **From Gemini**: Ask for historical dividend growth rate (CAGR)
2. **User Override**: User provides a custom growth rate
3. **Default Value**: Use conservative 2% if no data available

#### CAGR Calculation (if historical data available)

```
CAGR = (Final Dividend / Initial Dividend)^(1/years) - 1
```

Requirements:
- Minimum 3 years of dividend history
- Filter out years with zero dividends
- Cap result between 0% and 15%

### 3.3 Gemini Query Structure

When querying Gemini for stock data, request:

```
For the company [COMPANY_NAME/TICKER], provide:
1. Current stock price
2. Annual dividend per share (most recent)
3. Dividend yield percentage
4. Historical dividend growth rate (5-year CAGR if available)
5. Company sector and industry
6. Currency

If the company does not pay dividends, indicate this clearly.
```

---

## 4. Valuation Classification

### 4.1 Margin of Safety Calculation

```
Margin = ((Fair Value - Market Price) / Market Price) × 100
```

### 4.2 Classification Rules

| Margin | Classification | Meaning |
|--------|---------------|---------|
| > +10% | **UNDERVALUED** | Stock appears cheap relative to intrinsic value |
| -10% to +10% | **FAIRLY VALUED** | Stock price aligns with intrinsic value |
| < -10% | **OVERVALUED** | Stock appears expensive relative to intrinsic value |

The 10% threshold is configurable and represents a "margin of safety" buffer.

---

## 5. Sensitivity Analysis

### 5.1 Purpose

Show users how the Fair Value changes with different assumptions for r and g. This demonstrates:
- Model sensitivity to input parameters
- Range of possible valuations
- Impact of interest rate changes

### 5.2 Default Parameter Ranges

| Parameter | Default Range |
|-----------|---------------|
| Required Return (r) | 6%, 7%, 8%, 9%, 10% |
| Growth Rate (g) | 1%, 2%, 3%, 4%, 5% |

### 5.3 Output Format

Generate a matrix showing Fair Value for each (r, g) combination:

```
         g →    1%     2%     3%     4%     5%
    r ↓
    6%        42.42  44.90  47.64  50.67  54.05
    7%        35.35  36.73  38.25  39.92  41.78
    8%        30.30  31.11  32.00  33.00  34.10
    9%        26.52  27.00  27.53  28.11  28.74
   10%        23.57  23.85  24.16  24.50  24.87
```

Highlight the cell matching current parameters.

---

## 6. User Input Modes

### 6.1 Ticker/Company Search

**Input:**
- Company name or ticker symbol
- Required return (r) - default 8%
- Growth rate override (optional)

**Process:**
1. Query Gemini for stock data
2. Calculate growth rate if not provided
3. Compute Fair Value
4. Determine valuation classification
5. Generate sensitivity analysis

### 6.2 Manual Data Entry

**Input:**
- Company name (free text)
- Ticker (free text)
- Current price
- Annual dividend (D₀)
- Required return (r)
- Growth rate (g)

**Process:**
1. Validate inputs (positive numbers, r > g)
2. Calculate D₁ from D₀ and g
3. Compute Fair Value
4. Determine valuation classification
5. Generate sensitivity analysis

### 6.3 Educational Demo

Pre-configured example demonstrating:
- Basic calculation with fixed values
- Comparison at different market prices
- Impact of interest rate changes

**Demo Parameters:**
- D₁ = 2.00
- g = 3%
- r = 7%
- Test prices: 40, 50, 70

---

## 7. Interest Rate Impact Analysis

### 7.1 Purpose

Demonstrate why stock markets fall when interest rates rise.

### 7.2 Calculation

For a fixed dividend and growth rate, show Fair Value at different required returns:

| Required Return | Fair Value | Change from Base |
|-----------------|------------|------------------|
| 5% | 100.00 | - |
| 6% | 66.67 | -33% |
| 7% | 50.00 | -50% |
| 8% | 40.00 | -60% |
| 9% | 33.33 | -67% |
| 10% | 28.57 | -71% |

### 7.3 Display

Show as comparison to current market price:
- If Fair Value > Market Price (+10%): Indicate upside potential
- If Fair Value < Market Price (-10%): Indicate downside risk

---

## 8. Business Rules Summary

### 8.1 Input Validation

| Field | Rule |
|-------|------|
| Ticker | Non-empty, uppercase |
| Current Price | Must be > 0 |
| Dividend | Must be ≥ 0 (0 = non-dividend stock) |
| Required Return (r) | Must be between 1% and 30% |
| Growth Rate (g) | Must be between 0% and 20% |
| r vs g | r must be > g |

### 8.2 Default Values

| Parameter | Default |
|-----------|---------|
| Required Return | 8% |
| Growth Rate | 2% (if not calculable) |
| Valuation Threshold | 10% |

### 8.3 Rounding Rules

| Value | Precision |
|-------|-----------|
| Prices | 2 decimal places |
| Percentages (display) | 1-2 decimal places |
| Percentages (calculation) | Full precision |

---

## 9. Error Handling

### 9.1 Data Retrieval Errors

| Scenario | User Message |
|----------|--------------|
| Company not found | "Could not find data for [TICKER]. Please verify the ticker symbol." |
| Gemini unavailable | "Unable to retrieve stock data. Please try again or use manual entry." |
| Invalid ticker format | "Please enter a valid ticker symbol (e.g., AAPL, JNJ)." |

### 9.2 Calculation Errors

| Scenario | User Message |
|----------|--------------|
| No dividends | "This company does not pay dividends. The DDM model is not applicable." |
| g ≥ r | "Growth rate must be lower than required return. Please adjust parameters." |
| Invalid inputs | "Please enter valid positive numbers for all fields." |

---

## 10. Output Structure

### 10.1 Valuation Result

```
Stock Information:
  - Ticker: JNJ
  - Company: Johnson & Johnson
  - Sector: Healthcare
  - Industry: Drug Manufacturers

Financial Data:
  - Current Price: 155.50 USD
  - Annual Dividend: 4.76 USD
  - Dividend Yield: 3.06%
  - Dividend Growth Rate: 5.2%

Model Parameters:
  - Required Return (r): 8.0%
  - Growth Rate (g): 5.2%
  - Expected Dividend (D₁): 5.01 USD

Valuation Result:
  - Fair Value: 178.93 USD
  - Market Price: 155.50 USD
  - Margin of Safety: +15.1%
  - Verdict: UNDERVALUED
```

### 10.2 Verdict Messages

| Verdict | Message |
|---------|---------|
| UNDERVALUED | "The stock appears to be a good value. You're buying at [price] something worth [fair_value]." |
| FAIRLY VALUED | "The price is in line with fundamental value." |
| OVERVALUED | "The stock appears expensive. The market may be too optimistic." |
| NOT APPLICABLE | "This company doesn't pay dividends. Consider using DCF or other valuation methods." |

---

## 11. Limitations & Disclaimers

### 11.1 Model Limitations

The Gordon Growth Model assumes:
- Dividends grow at a constant rate forever
- The company will continue paying dividends indefinitely
- Growth rate remains below required return

These assumptions rarely hold perfectly in reality.

### 11.2 When NOT to Use DDM

- **Growth stocks** that reinvest earnings (no dividends)
- **Cyclical companies** with variable dividends
- **Startups** or companies with uncertain futures
- **Companies reducing dividends**

### 11.3 Required Disclaimer

Always display:
> "This analysis is for educational purposes only. Results depend heavily on input assumptions. This does not constitute financial advice."

---

## 12. Future Enhancements (Out of Scope)

These features are not part of current scope but could be added:

1. **Multi-stage DDM** - Different growth rates for different periods
2. **DCF Model** - For non-dividend stocks using Free Cash Flow
3. **Comparative Analysis** - Compare multiple stocks
4. **Historical Tracking** - Track valuations over time
5. **Portfolio Integration** - Analyze entire portfolios
