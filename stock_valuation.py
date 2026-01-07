#!/usr/bin/env python3
"""
Stock Valuation App using Dividend Discount Model (DDM)
Gordon Growth Model (GGM) implementation

Formula: P = D₁ / (r - g)
Where:
    P  = Fair Value (intrinsic price)
    D₁ = Expected dividend next year
    r  = Required rate of return (discount rate)
    g  = Dividend growth rate
"""

import requests
import urllib3
import json
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Disable SSL warnings for environments with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Valuation(Enum):
    UNDERVALUED = "SOTTOVALUTATA (Undervalued)"
    FAIRLY_VALUED = "FAIRLY VALUED (Prezzo Corretto)"
    OVERVALUED = "SOPRAVVALUTATA (Overvalued)"
    NOT_APPLICABLE = "NON APPLICABILE (No Dividends)"


@dataclass
class StockData:
    """Container for stock financial data"""
    ticker: str
    company_name: str
    current_price: float
    currency: str
    last_dividend: float  # Annual dividend per share
    dividend_yield: float
    dividend_growth_rate: Optional[float]  # Historical growth rate
    sector: str
    industry: str


@dataclass
class ValuationResult:
    """Container for valuation results"""
    stock_data: StockData
    fair_value: Optional[float]
    required_return: float
    growth_rate: float
    valuation: Valuation
    margin_of_safety: Optional[float]  # Percentage difference from fair value


def fetch_stock_data_yahoo(ticker: str) -> Optional[StockData]:
    """
    Fetch stock data from Yahoo Finance via direct HTTP request

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        StockData object or None if fetch fails
    """
    try:
        # Yahoo Finance API endpoint
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
        params = {
            "modules": "price,summaryDetail,defaultKeyStatistics,assetProfile"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)

        if response.status_code != 200:
            return None

        data = response.json()

        if "quoteSummary" not in data or data["quoteSummary"]["result"] is None:
            return None

        result = data["quoteSummary"]["result"][0]

        # Extract price data
        price_data = result.get("price", {})
        summary_detail = result.get("summaryDetail", {})
        asset_profile = result.get("assetProfile", {})

        current_price = price_data.get("regularMarketPrice", {}).get("raw", 0)
        currency = price_data.get("currency", "USD")
        company_name = price_data.get("longName") or price_data.get("shortName", ticker)

        # Extract dividend data
        dividend_rate = summary_detail.get("dividendRate", {}).get("raw", 0) or 0
        dividend_yield = summary_detail.get("dividendYield", {}).get("raw", 0) or 0

        # Calculate dividend growth from 5-year avg yield if available
        five_year_avg_yield = summary_detail.get("fiveYearAvgDividendYield", {}).get("raw")
        dividend_growth = None

        if dividend_yield > 0 and five_year_avg_yield and five_year_avg_yield > 0:
            # Rough estimate of growth based on yield changes
            # If current yield is lower than average, dividends likely grew
            if dividend_yield < five_year_avg_yield:
                dividend_growth = (five_year_avg_yield - dividend_yield) / 5 / dividend_yield
                dividend_growth = min(max(dividend_growth, 0), 0.15)

        return StockData(
            ticker=ticker.upper(),
            company_name=company_name,
            current_price=current_price,
            currency=currency,
            last_dividend=dividend_rate,
            dividend_yield=dividend_yield,
            dividend_growth_rate=dividend_growth,
            sector=asset_profile.get("sector", "N/A"),
            industry=asset_profile.get("industry", "N/A")
        )
    except Exception as e:
        print(f"Errore nel recupero dati per {ticker}: {e}")
        return None


def fetch_dividend_history(ticker: str) -> Optional[List[Tuple[int, float]]]:
    """
    Fetch dividend history to calculate growth rate

    Returns:
        List of (year, annual_dividend) tuples, or None if not available
    """
    try:
        # Fetch historical dividend data
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "period1": "0",
            "period2": str(int(datetime.now().timestamp())),
            "interval": "1mo",
            "events": "div"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)

        if response.status_code != 200:
            return None

        data = response.json()
        chart = data.get("chart", {}).get("result", [{}])[0]
        events = chart.get("events", {}).get("dividends", {})

        if not events:
            return None

        # Group dividends by year
        yearly_dividends = {}
        for timestamp, div_data in events.items():
            date = datetime.fromtimestamp(int(timestamp))
            year = date.year
            amount = div_data.get("amount", 0)
            yearly_dividends[year] = yearly_dividends.get(year, 0) + amount

        # Convert to sorted list
        result = sorted(yearly_dividends.items())

        # Only return if we have at least 3 years of data
        if len(result) >= 3:
            return result

        return None

    except Exception:
        return None


def calculate_dividend_growth_rate(dividend_history: List[Tuple[int, float]]) -> Optional[float]:
    """
    Calculate CAGR (Compound Annual Growth Rate) from dividend history

    Args:
        dividend_history: List of (year, annual_dividend) tuples

    Returns:
        CAGR as a decimal, or None if cannot be calculated
    """
    if not dividend_history or len(dividend_history) < 3:
        return None

    # Filter out zero or negative values
    valid_history = [(y, d) for y, d in dividend_history if d > 0]

    if len(valid_history) < 3:
        return None

    first_year, first_dividend = valid_history[0]
    last_year, last_dividend = valid_history[-1]

    years = last_year - first_year

    if years <= 0 or first_dividend <= 0:
        return None

    # Calculate CAGR
    cagr = (last_dividend / first_dividend) ** (1 / years) - 1

    # Cap between 0% and 15%
    return min(max(cagr, 0), 0.15)


def fetch_stock_data(ticker: str) -> Optional[StockData]:
    """
    Fetch stock data with dividend growth calculation

    Args:
        ticker: Stock ticker symbol

    Returns:
        StockData object or None if fetch fails
    """
    stock_data = fetch_stock_data_yahoo(ticker)

    if stock_data is None:
        return None

    # Try to calculate dividend growth from history
    if stock_data.dividend_growth_rate is None:
        history = fetch_dividend_history(ticker)
        if history:
            growth_rate = calculate_dividend_growth_rate(history)
            if growth_rate is not None:
                stock_data = StockData(
                    ticker=stock_data.ticker,
                    company_name=stock_data.company_name,
                    current_price=stock_data.current_price,
                    currency=stock_data.currency,
                    last_dividend=stock_data.last_dividend,
                    dividend_yield=stock_data.dividend_yield,
                    dividend_growth_rate=growth_rate,
                    sector=stock_data.sector,
                    industry=stock_data.industry
                )

    return stock_data


def gordon_growth_model(d1: float, r: float, g: float) -> Optional[float]:
    """
    Calculate fair value using Gordon Growth Model

    Formula: P = D₁ / (r - g)

    Args:
        d1: Expected dividend next year
        r: Required rate of return (e.g., 0.08 for 8%)
        g: Dividend growth rate (e.g., 0.03 for 3%)

    Returns:
        Fair value per share, or None if invalid inputs
    """
    # Validate inputs
    if r <= g:
        # Model doesn't work when growth rate >= required return
        return None

    if d1 <= 0:
        return None

    return d1 / (r - g)


def calculate_valuation(
    stock_data: StockData,
    required_return: float = 0.08,
    custom_growth_rate: Optional[float] = None
) -> ValuationResult:
    """
    Calculate stock valuation using DDM/GGM

    Args:
        stock_data: Stock financial data
        required_return: Required rate of return (default 8%)
        custom_growth_rate: Override the calculated growth rate

    Returns:
        ValuationResult with fair value and assessment
    """
    # Check if stock pays dividends
    if stock_data.last_dividend <= 0:
        return ValuationResult(
            stock_data=stock_data,
            fair_value=None,
            required_return=required_return,
            growth_rate=0,
            valuation=Valuation.NOT_APPLICABLE,
            margin_of_safety=None
        )

    # Determine growth rate
    if custom_growth_rate is not None:
        growth_rate = custom_growth_rate
    elif stock_data.dividend_growth_rate is not None:
        growth_rate = stock_data.dividend_growth_rate
    else:
        # Default conservative growth rate of 2%
        growth_rate = 0.02

    # Ensure growth rate is less than required return
    if growth_rate >= required_return:
        growth_rate = required_return - 0.01

    # Calculate D1 (next year's expected dividend)
    d1 = stock_data.last_dividend * (1 + growth_rate)

    # Calculate fair value
    fair_value = gordon_growth_model(d1, required_return, growth_rate)

    if fair_value is None:
        return ValuationResult(
            stock_data=stock_data,
            fair_value=None,
            required_return=required_return,
            growth_rate=growth_rate,
            valuation=Valuation.NOT_APPLICABLE,
            margin_of_safety=None
        )

    # Determine valuation status
    current_price = stock_data.current_price
    margin = (fair_value - current_price) / current_price * 100

    # Use 10% threshold for valuation classification
    if margin > 10:
        valuation = Valuation.UNDERVALUED
    elif margin < -10:
        valuation = Valuation.OVERVALUED
    else:
        valuation = Valuation.FAIRLY_VALUED

    return ValuationResult(
        stock_data=stock_data,
        fair_value=fair_value,
        required_return=required_return,
        growth_rate=growth_rate,
        valuation=valuation,
        margin_of_safety=margin
    )


def sensitivity_analysis(
    stock_data: StockData,
    required_returns: list = None,
    growth_rates: list = None
) -> Dict[Tuple[float, float], float]:
    """
    Perform sensitivity analysis on fair value

    Shows how fair value changes with different r and g assumptions
    """
    if required_returns is None:
        required_returns = [0.06, 0.07, 0.08, 0.09, 0.10]

    if growth_rates is None:
        growth_rates = [0.01, 0.02, 0.03, 0.04, 0.05]

    results = {}

    for r in required_returns:
        for g in growth_rates:
            if r > g and stock_data.last_dividend > 0:
                d1 = stock_data.last_dividend * (1 + g)
                fair_value = gordon_growth_model(d1, r, g)
                results[(r, g)] = fair_value

    return results


def print_valuation_report(result: ValuationResult, show_sensitivity: bool = True):
    """Print a formatted valuation report"""
    stock = result.stock_data

    print("\n" + "=" * 60)
    print(f"  REPORT DI VALUTAZIONE: {stock.company_name}")
    print("=" * 60)

    print(f"\n{'='*20} DATI AZIENDA {'='*20}")
    print(f"   Ticker:        {stock.ticker}")
    print(f"   Settore:       {stock.sector}")
    print(f"   Industria:     {stock.industry}")

    print(f"\n{'='*18} DATI FINANZIARI {'='*18}")
    print(f"   Prezzo Attuale:        {stock.current_price:.2f} {stock.currency}")
    print(f"   Dividendo Annuale:     {stock.last_dividend:.2f} {stock.currency}")
    print(f"   Dividend Yield:        {stock.dividend_yield * 100:.2f}%")

    if stock.dividend_growth_rate:
        print(f"   Crescita Dividendi:    {stock.dividend_growth_rate * 100:.2f}% (storico)")

    print(f"\n{'='*12} PARAMETRI MODELLO (Gordon Growth Model) {'='*5}")
    print(f"   Tasso Rendimento (r):  {result.required_return * 100:.1f}%")
    print(f"   Tasso Crescita (g):    {result.growth_rate * 100:.2f}%")

    if result.valuation == Valuation.NOT_APPLICABLE:
        print(f"\n   VALUTAZIONE: {result.valuation.value}")
        print("   Questa azienda non paga dividendi o i dati sono insufficienti.")
        print("   Il Dividend Discount Model non e' applicabile.")
        print("   Considera di usare altri metodi (DCF, multipli, ecc.)")
    else:
        d1 = stock.last_dividend * (1 + result.growth_rate)
        print(f"   D1 (Dividendo Atteso): {d1:.2f} {stock.currency}")

        print(f"\n{'='*17} RISULTATO VALUTAZIONE {'='*17}")
        print(f"   +---------------------------------------------+")
        print(f"   |  Fair Value (Valore Equo): {result.fair_value:>10.2f} {stock.currency}   |")
        print(f"   |  Prezzo di Mercato:        {stock.current_price:>10.2f} {stock.currency}   |")
        print(f"   |  Margine di Sicurezza:     {result.margin_of_safety:>+10.1f}%      |")
        print(f"   +---------------------------------------------+")

        print(f"\n   VERDETTO: {result.valuation.value}")

        if result.valuation == Valuation.UNDERVALUED:
            print("   --> L'azione sembra un buon affare!")
            print(f"   Stai comprando a {stock.current_price:.2f} qualcosa che vale {result.fair_value:.2f}")
        elif result.valuation == Valuation.OVERVALUED:
            print("   --> L'azione sembra troppo cara!")
            print("   Il mercato potrebbe essere troppo ottimista.")
        else:
            print("   --> Il prezzo e' in linea con il valore fondamentale.")

    # Sensitivity Analysis
    if show_sensitivity and result.valuation != Valuation.NOT_APPLICABLE:
        print(f"\n{'='*17} ANALISI DI SENSIBILITA' {'='*17}")
        print("   Come cambia il Fair Value al variare di r e g:")
        print()

        sensitivity = sensitivity_analysis(stock)

        # Print header
        growth_rates = sorted(set(g for r, g in sensitivity.keys()))
        print("         g->  ", end="")
        for g in growth_rates:
            print(f"{g*100:>6.0f}%", end=" ")
        print()
        print("   r    ", "-" * 42)

        required_returns = sorted(set(r for r, g in sensitivity.keys()))
        for r in required_returns:
            print(f"   {r*100:>4.0f}% |", end="")
            for g in growth_rates:
                if (r, g) in sensitivity and sensitivity[(r, g)]:
                    val = sensitivity[(r, g)]
                    # Highlight current scenario
                    if abs(r - result.required_return) < 0.001 and abs(g - result.growth_rate) < 0.001:
                        print(f" [{val:>5.0f}]", end="")
                    else:
                        print(f"  {val:>5.0f} ", end="")
                else:
                    print("    N/A ", end="")
            print()

    print("\n" + "=" * 60)
    print("DISCLAIMER: Questa analisi e' solo a scopo educativo.")
    print("   I risultati dipendono fortemente dalle ipotesi sui tassi.")
    print("   Non costituisce consulenza finanziaria.")
    print("=" * 60 + "\n")


def analyze_stock(
    ticker_or_name: str,
    required_return: float = 0.08,
    custom_growth_rate: Optional[float] = None,
    show_sensitivity: bool = True
) -> Optional[ValuationResult]:
    """
    Main function to analyze a stock

    Args:
        ticker_or_name: Stock ticker or company name
        required_return: Required rate of return (default 8%)
        custom_growth_rate: Override calculated growth rate
        show_sensitivity: Show sensitivity analysis table

    Returns:
        ValuationResult or None if analysis fails
    """
    print(f"\n[*] Cercando dati per: {ticker_or_name}...")

    # Fetch stock data
    stock_data = fetch_stock_data(ticker_or_name)

    if stock_data is None:
        print(f"[X] Impossibile trovare dati per '{ticker_or_name}'")
        print("   Prova ad usare il simbolo ticker (es. AAPL, MSFT, JNJ)")
        return None

    print(f"[OK] Trovato: {stock_data.company_name} ({stock_data.ticker})")

    # Calculate valuation
    result = calculate_valuation(
        stock_data=stock_data,
        required_return=required_return,
        custom_growth_rate=custom_growth_rate
    )

    # Print report
    print_valuation_report(result, show_sensitivity=show_sensitivity)

    return result


def manual_analysis():
    """
    Perform analysis with manually entered data
    Useful when API is not available or for hypothetical scenarios
    """
    print("\n" + "=" * 60)
    print("  ANALISI MANUALE - Inserisci i dati")
    print("=" * 60)

    try:
        company_name = input("\nNome azienda: ").strip() or "Azienda"
        ticker = input("Ticker: ").strip() or "XXX"

        current_price = float(input("Prezzo attuale: ").strip())
        last_dividend = float(input("Dividendo annuale per azione: ").strip())

        r_input = input("Tasso rendimento richiesto (%) [default: 8]: ").strip()
        required_return = float(r_input) / 100 if r_input else 0.08

        g_input = input("Tasso crescita dividendi (%) [default: 3]: ").strip()
        growth_rate = float(g_input) / 100 if g_input else 0.03

        stock_data = StockData(
            ticker=ticker.upper(),
            company_name=company_name,
            current_price=current_price,
            currency="EUR",
            last_dividend=last_dividend,
            dividend_yield=last_dividend / current_price if current_price > 0 else 0,
            dividend_growth_rate=growth_rate,
            sector="N/A",
            industry="N/A"
        )

        result = calculate_valuation(
            stock_data=stock_data,
            required_return=required_return,
            custom_growth_rate=growth_rate
        )

        print_valuation_report(result, show_sensitivity=True)
        return result

    except ValueError:
        print("[X] Valore non valido. Usa numeri (es. 50.00 per prezzo)")
        return None


def demo_example():
    """
    Run the MegaCorp example from the theory
    """
    print("\n" + "=" * 60)
    print("  ESEMPIO: MegaCorp Inc.")
    print("  (Esempio didattico dal modello teorico)")
    print("=" * 60)

    # Create example stock data
    stock_data = StockData(
        ticker="MEGA",
        company_name="MegaCorp Inc.",
        current_price=40.00,  # We'll test with different prices
        currency="EUR",
        last_dividend=2.00 / 1.03,  # D0 so that D1 = 2.00
        dividend_yield=0.05,
        dividend_growth_rate=0.03,  # 3% growth
        sector="Example",
        industry="Educational"
    )

    print("\nDati dell'esempio:")
    print(f"  - Dividendo atteso prossimo anno (D1): 2.00 EUR")
    print(f"  - Tasso di crescita (g): 3%")
    print(f"  - Tasso rendimento richiesto (r): 7%")

    # Calculate with r=7%, g=3%
    result = calculate_valuation(
        stock_data=stock_data,
        required_return=0.07,
        custom_growth_rate=0.03
    )

    print(f"\nCalcolo: P = D1 / (r - g) = 2.00 / (0.07 - 0.03) = 2.00 / 0.04 = 50.00 EUR")

    print("\n" + "-" * 60)
    print("CONFRONTO CON DIVERSI PREZZI DI MERCATO:")
    print("-" * 60)

    for test_price in [40.00, 50.00, 70.00]:
        stock_data_test = StockData(
            ticker="MEGA",
            company_name="MegaCorp Inc.",
            current_price=test_price,
            currency="EUR",
            last_dividend=2.00 / 1.03,
            dividend_yield=2.00 / test_price,
            dividend_growth_rate=0.03,
            sector="Example",
            industry="Educational"
        )

        result = calculate_valuation(
            stock_data=stock_data_test,
            required_return=0.07,
            custom_growth_rate=0.03
        )

        print(f"\nSe il prezzo di mercato e' {test_price:.2f} EUR:")
        print(f"  Fair Value: {result.fair_value:.2f} EUR")
        print(f"  Margine: {result.margin_of_safety:+.1f}%")
        print(f"  Verdetto: {result.valuation.value}")

    print("\n" + "-" * 60)
    print("IMPATTO DEI TASSI DI INTERESSE:")
    print("-" * 60)
    print("\nCosa succede se i tassi salgono (r passa da 7% a 9%)?")

    for r in [0.07, 0.09]:
        d1 = 2.00
        fair_value = gordon_growth_model(d1, r, 0.03)
        print(f"\n  Con r = {r*100:.0f}%: Fair Value = {fair_value:.2f} EUR")

    print("\n  L'azienda e' la stessa, ma il valore crolla del 33%!")
    print("  Questo spiega perche' i mercati scendono quando i tassi salgono.")
    print("=" * 60 + "\n")


def interactive_mode():
    """Run the app in interactive mode"""
    print("\n" + "=" * 60)
    print("  STOCK VALUATION APP - Dividend Discount Model")
    print("  Gordon Growth Model (GGM) Calculator")
    print("=" * 60)

    while True:
        print("\nOpzioni:")
        print("  1. Analizza un'azione (inserisci ticker)")
        print("  2. Analizza con parametri personalizzati")
        print("  3. Confronta impatto dei tassi")
        print("  4. Inserimento manuale dei dati")
        print("  5. Esempio didattico (MegaCorp)")
        print("  q. Esci")

        choice = input("\nScelta: ").strip().lower()

        if choice == 'q':
            print("\nArrivederci!\n")
            break

        elif choice == '1':
            ticker = input("\nInserisci ticker (es. AAPL, JNJ, KO): ").strip()
            if ticker:
                analyze_stock(ticker)

        elif choice == '2':
            ticker = input("\nInserisci ticker: ").strip()
            if not ticker:
                continue

            try:
                r_input = input("Tasso rendimento richiesto (%) [default: 8]: ").strip()
                required_return = float(r_input) / 100 if r_input else 0.08

                g_input = input("Tasso crescita dividendi (%) [vuoto=automatico]: ").strip()
                custom_growth = float(g_input) / 100 if g_input else None

                analyze_stock(ticker, required_return, custom_growth)
            except ValueError:
                print("[X] Valore non valido. Usa numeri (es. 8 per 8%)")

        elif choice == '3':
            ticker = input("\nInserisci ticker: ").strip()
            if not ticker:
                continue

            stock_data = fetch_stock_data(ticker)
            if stock_data is None:
                print(f"[X] Impossibile trovare dati per '{ticker}'")
                continue

            if stock_data.last_dividend <= 0:
                print(f"[X] {stock_data.company_name} non paga dividendi")
                continue

            print(f"\nImpatto dei tassi su {stock_data.company_name}")
            print(f"   Prezzo attuale: {stock_data.current_price:.2f} {stock_data.currency}")
            print(f"   Dividendo: {stock_data.last_dividend:.2f} {stock_data.currency}")

            growth = stock_data.dividend_growth_rate or 0.02
            print(f"   Crescita dividendi: {growth * 100:.1f}%\n")

            print("   Tasso (r)  |  Fair Value  |  vs Mercato")
            print("   " + "-" * 42)

            for r in [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12]:
                if r > growth:
                    d1 = stock_data.last_dividend * (1 + growth)
                    fv = gordon_growth_model(d1, r, growth)
                    diff = (fv - stock_data.current_price) / stock_data.current_price * 100
                    status = "[UP]" if diff > 10 else ("[DOWN]" if diff < -10 else "[=]")
                    print(f"     {r*100:>4.0f}%   |   {fv:>8.2f}   |  {diff:>+6.1f}% {status}")

        elif choice == '4':
            manual_analysis()

        elif choice == '5':
            demo_example()


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--demo':
            demo_example()
        elif sys.argv[1] == '--help':
            print("\nStock Valuation App - Dividend Discount Model")
            print("\nUsage:")
            print("  python stock_valuation.py                  # Interactive mode")
            print("  python stock_valuation.py TICKER           # Analyze a stock")
            print("  python stock_valuation.py TICKER r         # With custom required return")
            print("  python stock_valuation.py TICKER r g       # With custom r and growth rate")
            print("  python stock_valuation.py --demo           # Run MegaCorp example")
            print("\nExamples:")
            print("  python stock_valuation.py JNJ              # Analyze Johnson & Johnson")
            print("  python stock_valuation.py KO 8             # Coca-Cola with 8% required return")
            print("  python stock_valuation.py PG 7 3           # P&G with 7% return, 3% growth")
        else:
            # Command line mode
            ticker = sys.argv[1]
            required_return = float(sys.argv[2]) / 100 if len(sys.argv) > 2 else 0.08
            custom_growth = float(sys.argv[3]) / 100 if len(sys.argv) > 3 else None

            analyze_stock(ticker, required_return, custom_growth)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
