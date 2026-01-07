#!/usr/bin/env python3
"""
Web application for Stock Valuation using Dividend Discount Model
Flask-based API and web interface
"""

from flask import Flask, render_template, jsonify, request
from stock_valuation import (
    fetch_stock_data,
    calculate_valuation,
    gordon_growth_model,
    sensitivity_analysis,
    StockData,
    Valuation
)

app = Flask(__name__)


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze a stock using the Gordon Growth Model

    Request JSON:
    {
        "ticker": "JNJ",
        "required_return": 8,  // percentage
        "growth_rate": null   // null for auto, or percentage
    }
    """
    data = request.get_json()

    ticker = data.get('ticker', '').strip().upper()
    required_return = float(data.get('required_return', 8)) / 100
    custom_growth = data.get('growth_rate')

    if custom_growth is not None and custom_growth != '':
        custom_growth = float(custom_growth) / 100
    else:
        custom_growth = None

    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    # Fetch stock data
    stock_data = fetch_stock_data(ticker)

    if stock_data is None:
        return jsonify({
            'error': f'Could not find data for {ticker}. Please check the ticker symbol.'
        }), 404

    # Calculate valuation
    result = calculate_valuation(
        stock_data=stock_data,
        required_return=required_return,
        custom_growth_rate=custom_growth
    )

    # Prepare response
    response = {
        'stock': {
            'ticker': stock_data.ticker,
            'company_name': stock_data.company_name,
            'current_price': round(stock_data.current_price, 2),
            'currency': stock_data.currency,
            'dividend': round(stock_data.last_dividend, 2),
            'dividend_yield': round(stock_data.dividend_yield * 100, 2),
            'dividend_growth_rate': round(stock_data.dividend_growth_rate * 100, 2) if stock_data.dividend_growth_rate else None,
            'sector': stock_data.sector,
            'industry': stock_data.industry
        },
        'valuation': {
            'fair_value': round(result.fair_value, 2) if result.fair_value else None,
            'required_return': round(result.required_return * 100, 1),
            'growth_rate': round(result.growth_rate * 100, 2),
            'margin_of_safety': round(result.margin_of_safety, 1) if result.margin_of_safety else None,
            'verdict': result.valuation.name,
            'verdict_text': result.valuation.value,
            'd1': round(stock_data.last_dividend * (1 + result.growth_rate), 2) if stock_data.last_dividend > 0 else None
        }
    }

    # Add sensitivity analysis if applicable
    if result.valuation != Valuation.NOT_APPLICABLE:
        sens = sensitivity_analysis(stock_data)
        sensitivity_data = []
        for (r, g), fv in sens.items():
            if fv:
                sensitivity_data.append({
                    'r': round(r * 100, 0),
                    'g': round(g * 100, 0),
                    'fair_value': round(fv, 2),
                    'is_current': abs(r - result.required_return) < 0.001 and abs(g - result.growth_rate) < 0.001
                })
        response['sensitivity'] = sensitivity_data

    return jsonify(response)


@app.route('/api/manual', methods=['POST'])
def manual_analysis():
    """
    Analyze with manually entered data

    Request JSON:
    {
        "company_name": "MegaCorp",
        "ticker": "MEGA",
        "current_price": 40,
        "dividend": 2,
        "required_return": 7,
        "growth_rate": 3
    }
    """
    data = request.get_json()

    try:
        company_name = data.get('company_name', 'Company')
        ticker = data.get('ticker', 'XXX').upper()
        current_price = float(data.get('current_price', 0))
        dividend = float(data.get('dividend', 0))
        required_return = float(data.get('required_return', 8)) / 100
        growth_rate = float(data.get('growth_rate', 3)) / 100

        if current_price <= 0:
            return jsonify({'error': 'Current price must be positive'}), 400

        if dividend <= 0:
            return jsonify({'error': 'Dividend must be positive for DDM analysis'}), 400

        # Create stock data
        stock_data = StockData(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            currency='EUR',
            last_dividend=dividend,
            dividend_yield=dividend / current_price,
            dividend_growth_rate=growth_rate,
            sector='Manual Entry',
            industry='Manual Entry'
        )

        # Calculate valuation
        result = calculate_valuation(
            stock_data=stock_data,
            required_return=required_return,
            custom_growth_rate=growth_rate
        )

        # Prepare response
        response = {
            'stock': {
                'ticker': stock_data.ticker,
                'company_name': stock_data.company_name,
                'current_price': round(stock_data.current_price, 2),
                'currency': stock_data.currency,
                'dividend': round(stock_data.last_dividend, 2),
                'dividend_yield': round(stock_data.dividend_yield * 100, 2),
                'dividend_growth_rate': round(growth_rate * 100, 2),
                'sector': stock_data.sector,
                'industry': stock_data.industry
            },
            'valuation': {
                'fair_value': round(result.fair_value, 2) if result.fair_value else None,
                'required_return': round(result.required_return * 100, 1),
                'growth_rate': round(result.growth_rate * 100, 2),
                'margin_of_safety': round(result.margin_of_safety, 1) if result.margin_of_safety else None,
                'verdict': result.valuation.name,
                'verdict_text': result.valuation.value,
                'd1': round(dividend * (1 + growth_rate), 2)
            }
        }

        # Add sensitivity analysis
        sens = sensitivity_analysis(stock_data)
        sensitivity_data = []
        for (r, g), fv in sens.items():
            if fv:
                sensitivity_data.append({
                    'r': round(r * 100, 0),
                    'g': round(g * 100, 0),
                    'fair_value': round(fv, 2),
                    'is_current': abs(r - result.required_return) < 0.001 and abs(g - result.growth_rate) < 0.001
                })
        response['sensitivity'] = sensitivity_data

        return jsonify(response)

    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400


@app.route('/api/demo')
def demo():
    """Return the MegaCorp demo example data"""
    examples = []

    for price in [40.00, 50.00, 70.00]:
        d1 = 2.00
        r = 0.07
        g = 0.03
        fair_value = gordon_growth_model(d1, r, g)
        margin = (fair_value - price) / price * 100

        if margin > 10:
            verdict = 'UNDERVALUED'
            verdict_text = 'SOTTOVALUTATA (Undervalued)'
        elif margin < -10:
            verdict = 'OVERVALUED'
            verdict_text = 'SOPRAVVALUTATA (Overvalued)'
        else:
            verdict = 'FAIRLY_VALUED'
            verdict_text = 'FAIRLY VALUED (Prezzo Corretto)'

        examples.append({
            'price': price,
            'fair_value': round(fair_value, 2),
            'margin': round(margin, 1),
            'verdict': verdict,
            'verdict_text': verdict_text
        })

    # Interest rate impact
    rate_impact = []
    for r in [0.07, 0.09]:
        fv = gordon_growth_model(2.00, r, 0.03)
        rate_impact.append({
            'rate': int(r * 100),
            'fair_value': round(fv, 2)
        })

    return jsonify({
        'company': 'MegaCorp Inc.',
        'd1': 2.00,
        'g': 3,
        'r': 7,
        'examples': examples,
        'rate_impact': rate_impact
    })


@app.route('/api/rate-impact', methods=['POST'])
def rate_impact():
    """
    Calculate fair value at different required return rates
    """
    data = request.get_json()

    dividend = float(data.get('dividend', 2))
    growth_rate = float(data.get('growth_rate', 3)) / 100
    current_price = float(data.get('current_price', 50))

    results = []
    for r in [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12]:
        if r > growth_rate:
            d1 = dividend * (1 + growth_rate)
            fv = gordon_growth_model(d1, r, growth_rate)
            diff = (fv - current_price) / current_price * 100
            results.append({
                'rate': int(r * 100),
                'fair_value': round(fv, 2),
                'vs_market': round(diff, 1)
            })

    return jsonify({'results': results})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
