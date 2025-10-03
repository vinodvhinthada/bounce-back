"""
Mobile-Ready Market Analysis App
Portable version with environment variables - no PC dependencies
"""

import os
from SmartApi import SmartConnect
from logzero import logger
import pyotp
import pandas as pd
from datetime import datetime
import time
from flask import Flask, render_template, jsonify, request
import json
import threading
import re
from collections import defaultdict

# Environment Variables Configuration
API_KEY = os.getenv('ANGEL_API_KEY', 'tKo2xsA5')
USERNAME = os.getenv('ANGEL_USERNAME', 'C125633')
PASSWORD = os.getenv('ANGEL_PASSWORD', '4111')
TOTP_TOKEN = os.getenv('ANGEL_TOTP_TOKEN', "TZZ2VTRBUWPB33SLOSA3NXSGWA")
PORT = int(os.getenv('PORT', 5002))

# NIFTY 50 STOCKS WITH WEIGHTAGE
NIFTY50_STOCKS = {
    'RELIANCE': 9.37, 'HDFCBANK': 7.50, 'BHARTIARTL': 5.76, 'TCS': 5.33, 'ICICIBANK': 4.96,
    'SBIN': 4.03, 'BAJFINANCE': 3.11, 'INFY': 3.04, 'HINDUNILVR': 3.01, 'ITC': 2.57,
    'LT': 2.55, 'MARUTI': 2.54, 'M&M': 2.18, 'KOTAKBANK': 2.07, 'SUNPHARMA': 1.99,
    'HCLTECH': 1.91, 'AXISBANK': 1.82, 'ULTRACEMCO': 1.81, 'NTPC': 1.67, 'BAJAJFINSV': 1.62,
    'ZOMATO': 1.61, 'ADANIPORTS': 1.55, 'ONGC': 1.55, 'TITAN': 1.53, 'ADANIENT': 1.51,
    'BEL': 1.50, 'JSWSTEEL': 1.42, 'TATAMOTORS': 1.34, 'POWERGRID': 1.32, 'WIPRO': 1.28,
    'BAJAJ-AUTO': 1.22, 'COALINDIA': 1.21, 'NESTLEIND': 1.14, 'ASIANPAINT': 1.13, 'TATASTEEL': 1.06,
    'EICHERMOT': 0.97, 'JIOFINANCIAL': 0.96, 'GRASIM': 0.96, 'SBILIFE': 0.91, 'HINDALCO': 0.87,
    'TRENT': 0.87, 'HDFCLIFE': 0.83, 'TECHM': 0.70, 'CIPLA': 0.62, 'SHRIRAMFIN': 0.62,
    'TATACONSUM': 0.57, 'HEROMOTOCO': 0.55, 'APOLLOHOSP': 0.54, 'DRREDDY': 0.53, 'INDUSINDBK': 0.29
}

# BANK NIFTY STOCKS WITH WEIGHTAGE
BANKNIFTY_STOCKS = {
    'HDFCBANK': 32.06, 'ICICIBANK': 21.20, 'SBIN': 17.24, 'KOTAKBANK': 8.87, 'AXISBANK': 7.78,
    'BANKBARODA': 2.90, 'PNB': 2.80, 'CANARABANK': 2.42, 'IDFCFIRSTB': 1.28, 'INDUSINDBK': 1.25,
    'AUBANK': 1.17, 'FEDERALBNK': 1.03
}

class MobileAngelClient:
    def __init__(self):
        self.smart_api = None
        self.auth_token = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Angel One client"""
        try:
            self.smart_api = SmartConnect(API_KEY)
            totp = pyotp.TOTP(TOTP_TOKEN).now()
            
            data = self.smart_api.generateSession(USERNAME, PASSWORD, totp)
            if data['status']:
                self.auth_token = data['data']['jwtToken']
                logger.info("✅ Successfully logged in to Angel One")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def symbol_matching(self, trading_symbol, stock_list):
        """Improved symbol matching with boundary detection"""
        if not trading_symbol:
            return None, None
        
        symbol_upper = trading_symbol.upper().strip()
        sorted_symbols = sorted(stock_list.keys(), key=len, reverse=True)
        
        for stock_symbol in sorted_symbols:
            if stock_symbol in symbol_upper:
                if len(stock_symbol) <= 3:
                    pattern = f'{re.escape(stock_symbol)}(?:[^A-Z]|$|\\d{{2}}[A-Z]{{3}}\\d{{2}})'
                    if re.search(pattern, symbol_upper):
                        return stock_symbol, stock_list[stock_symbol]
                else:
                    return stock_symbol, stock_list[stock_symbol]
        
        return None, None
    
    def get_market_price(self, stock_symbol):
        """Get current market price for a stock"""
        try:
            # Search for the equity symbol
            response = self.smart_api.searchScrip('NSE', stock_symbol)
            if response and response.get('status') and response.get('data'):
                equity_symbols = [s for s in response['data'] if s['tradingsymbol'].endswith('-EQ')]
                if equity_symbols:
                    token = equity_symbols[0]['symboltoken']
                    ltp_response = self.smart_api.ltpData('NSE', [token])
                    if ltp_response and ltp_response.get('status') and ltp_response.get('data'):
                        return ltp_response['data'][0].get('ltp', 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting price for {stock_symbol}: {e}")
            return 0
    
    def get_enhanced_pcr_data(self):
        """Get enhanced PCR data with additional calculations"""
        try:
            response = self.smart_api.putCallRatio()
            if response and response.get('status'):
                data = response.get('data', [])
                
                # Enhance each record with additional data
                enhanced_data = []
                for item in data:
                    symbol = item.get('tradingSymbol', '')
                    pcr = item.get('pcr', 0)
                    
                    # Calculate implied sentiment from PCR
                    if pcr > 1.2:
                        sentiment = 'Bearish'
                        sentiment_score = min(100, (pcr - 1) * 100)
                    elif pcr < 0.8:
                        sentiment = 'Bullish'
                        sentiment_score = min(100, (1 - pcr) * 100)
                    else:
                        sentiment = 'Neutral'
                        sentiment_score = 50
                    
                    enhanced_item = {
                        **item,
                        'sentiment': sentiment,
                        'sentiment_score': round(sentiment_score, 1),
                        'call_bias': 'Strong' if pcr < 0.7 else 'Moderate' if pcr < 0.9 else 'Weak',
                        'put_bias': 'Strong' if pcr > 1.3 else 'Moderate' if pcr > 1.1 else 'Weak'
                    }
                    enhanced_data.append(enhanced_item)
                
                return enhanced_data
            return []
        except Exception as e:
            logger.error(f"Error fetching enhanced PCR data: {e}")
            return []
    
    def analyze_nifty50_enhanced(self):
        """Enhanced NIFTY 50 analysis with sentiment"""
        pcr_data = self.get_enhanced_pcr_data()
        matches = []
        
        for item in pcr_data:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = self.symbol_matching(symbol, NIFTY50_STOCKS)
            if matched_symbol:
                # Get current price
                current_price = self.get_market_price(matched_symbol)
                
                matches.append({
                    'symbol': matched_symbol,
                    'original_symbol': symbol,
                    'weightage': weightage,
                    'pcr': item.get('pcr', 0),
                    'sentiment': item.get('sentiment', 'Neutral'),
                    'sentiment_score': item.get('sentiment_score', 50),
                    'call_bias': item.get('call_bias', 'Neutral'),
                    'put_bias': item.get('put_bias', 'Neutral'),
                    'current_price': current_price,
                    'callOI': 0,  # Will be populated from option chain if needed
                    'putOI': 0    # Will be populated from option chain if needed
                })
        
        return sorted(matches, key=lambda x: x['weightage'], reverse=True)
    
    def analyze_banknifty_enhanced(self):
        """Enhanced Bank NIFTY analysis with sentiment"""
        pcr_data = self.get_enhanced_pcr_data()
        matches = []
        
        for item in pcr_data:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = self.symbol_matching(symbol, BANKNIFTY_STOCKS)
            if matched_symbol:
                # Get current price
                current_price = self.get_market_price(matched_symbol)
                
                matches.append({
                    'symbol': matched_symbol,
                    'original_symbol': symbol,
                    'weightage': weightage,
                    'pcr': item.get('pcr', 0),
                    'sentiment': item.get('sentiment', 'Neutral'),
                    'sentiment_score': item.get('sentiment_score', 50),
                    'call_bias': item.get('call_bias', 'Neutral'),
                    'put_bias': item.get('put_bias', 'Neutral'),
                    'current_price': current_price,
                    'callOI': 0,  # Will be populated from option chain if needed
                    'putOI': 0    # Will be populated from option chain if needed
                })
        
        return sorted(matches, key=lambda x: x['weightage'], reverse=True)

# Initialize client
angel_client = MobileAngelClient()
app = Flask(__name__)

# Mobile-optimized HTML template (inline to avoid file dependencies)
MOBILE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>📱 Mobile Market Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { font-size: 14px; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
        .table-container { max-height: 400px; overflow-y: auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .table th { background: #3498db; color: white; position: sticky; top: 0; z-index: 10; font-size: 12px; padding: 8px 4px; }
        .table td { font-size: 11px; padding: 6px 4px; }
        .badge-bullish { background: #27ae60; color: white; }
        .badge-bearish { background: #e74c3c; color: white; }
        .badge-neutral { background: #95a5a6; color: white; }
        .sentiment-bullish { color: #27ae60; font-weight: bold; }
        .sentiment-bearish { color: #e74c3c; font-weight: bold; }
        .sentiment-neutral { color: #95a5a6; font-weight: bold; }
        .loading { text-align: center; padding: 30px; color: #6c757d; }
        .mobile-header { position: sticky; top: 0; background: white; z-index: 100; padding: 10px 0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .refresh-btn { position: fixed; bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 60px; height: 60px; }
        .compact-metrics { font-size: 12px; }
        .compact-metrics h6 { font-size: 11px; margin-bottom: 2px; }
        .compact-metrics h5 { font-size: 16px; margin-bottom: 0; }
    </style>
</head>
<body class="bg-light">
    <!-- Mobile Header -->
    <div class="mobile-header">
        <div class="container-fluid">
            <h5 class="text-center text-primary mb-0">📱 Market Analysis</h5>
            <p class="text-center text-muted mb-0" style="font-size: 12px;">Real-time NIFTY 50 & Bank NIFTY</p>
        </div>
    </div>

    <div class="container-fluid">
        <!-- NIFTY 50 Section -->
        <div class="metric-card">
            <h6 class="mb-2">📊 NIFTY 50</h6>
            <div class="row compact-metrics">
                <div class="col-4">
                    <h6>Stocks</h6>
                    <h5 id="nifty50-total">-</h5>
                </div>
                <div class="col-4">
                    <h6>Coverage</h6>
                    <h5 id="nifty50-coverage">-</h5>
                </div>
                <div class="col-4">
                    <h6>Sentiment</h6>
                    <span id="nifty50-overall" class="badge">Loading...</span>
                </div>
            </div>
            <div class="row compact-metrics mt-2">
                <div class="col-4 text-success">🟢 <span id="nifty50-bullish">-</span></div>
                <div class="col-4 text-danger">🔴 <span id="nifty50-bearish">-</span></div>
                <div class="col-4 text-warning">🟡 <span id="nifty50-neutral">-</span></div>
            </div>
        </div>
        
        <div class="table-container mb-4">
            <div id="nifty50-loading" class="loading">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2">Loading NIFTY 50...</p>
            </div>
            <table class="table table-striped" id="nifty50-table" style="display:none;">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Stock</th>
                        <th>Wt%</th>
                        <th>₹</th>
                        <th>PCR</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody id="nifty50-tbody"></tbody>
            </table>
        </div>

        <!-- Bank NIFTY Section -->
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h6 class="mb-2">🏦 Bank NIFTY</h6>
            <div class="row compact-metrics">
                <div class="col-4">
                    <h6>Banks</h6>
                    <h5 id="banknifty-total">-</h5>
                </div>
                <div class="col-4">
                    <h6>Coverage</h6>
                    <h5 id="banknifty-coverage">-</h5>
                </div>
                <div class="col-4">
                    <h6>Sentiment</h6>
                    <span id="banknifty-overall" class="badge">Loading...</span>
                </div>
            </div>
            <div class="row compact-metrics mt-2">
                <div class="col-4 text-success">🟢 <span id="banknifty-bullish">-</span></div>
                <div class="col-4 text-danger">🔴 <span id="banknifty-bearish">-</span></div>
                <div class="col-4 text-warning">🟡 <span id="banknifty-neutral">-</span></div>
            </div>
        </div>
        
        <div class="table-container mb-5">
            <div id="banknifty-loading" class="loading">
                <div class="spinner-border text-danger" role="status"></div>
                <p class="mt-2">Loading Bank NIFTY...</p>
            </div>
            <table class="table table-striped" id="banknifty-table" style="display:none;">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Bank</th>
                        <th>Wt%</th>
                        <th>₹</th>
                        <th>PCR</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody id="banknifty-tbody"></tbody>
            </table>
        </div>

        <!-- Footer -->
        <div class="text-center mb-4">
            <p class="text-muted" style="font-size: 12px;">Last Updated: <span id="last-updated">-</span></p>
        </div>
    </div>

    <!-- Floating Refresh Button -->
    <button class="btn btn-primary refresh-btn" onclick="refreshData()">🔄</button>

    <script>
        function formatPCR(pcr) { return parseFloat(pcr).toFixed(3); }
        function formatPrice(price) { return price > 0 ? '₹' + parseFloat(price).toFixed(0) : '-'; }
        function getSentimentClass(sentiment) {
            switch(sentiment.toLowerCase()) {
                case 'bullish': return 'sentiment-bullish';
                case 'bearish': return 'sentiment-bearish';
                default: return 'sentiment-neutral';
            }
        }
        function getSentimentBadge(sentiment) {
            switch(sentiment.toLowerCase()) {
                case 'bullish': return 'badge-bullish';
                case 'bearish': return 'badge-bearish';
                default: return 'badge-neutral';
            }
        }
        function updateTimestamp() { document.getElementById('last-updated').textContent = new Date().toLocaleString(); }

        function loadNifty50() {
            document.getElementById('nifty50-loading').style.display = 'block';
            fetch('/api/nifty50')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('nifty50-loading').style.display = 'none';
                    if (data.success) {
                        document.getElementById('nifty50-total').textContent = data.summary.unique_stocks;
                        document.getElementById('nifty50-coverage').textContent = data.summary.coverage_percent + '%';
                        document.getElementById('nifty50-bullish').textContent = data.summary.bullish_stocks;
                        document.getElementById('nifty50-bearish').textContent = data.summary.bearish_stocks;
                        document.getElementById('nifty50-neutral').textContent = data.summary.neutral_stocks;
                        
                        const overallSentiment = data.summary.overall_sentiment;
                        document.getElementById('nifty50-overall').textContent = overallSentiment;
                        document.getElementById('nifty50-overall').className = `badge ${getSentimentBadge(overallSentiment)}`;
                        
                        const tbody = document.getElementById('nifty50-tbody');
                        tbody.innerHTML = '';
                        data.data.forEach((item, index) => {
                            const row = tbody.insertRow();
                            row.innerHTML = `
                                <td>${index + 1}</td>
                                <td><strong>${item.symbol}</strong></td>
                                <td>${item.weightage}%</td>
                                <td>${formatPrice(item.current_price)}</td>
                                <td>${formatPCR(item.pcr)}</td>
                                <td><span class="${getSentimentClass(item.sentiment)}">${item.sentiment}</span></td>
                            `;
                        });
                        document.getElementById('nifty50-table').style.display = 'block';
                    }
                })
                .catch(error => console.error('NIFTY 50 load error:', error));
        }

        function loadBankNifty() {
            document.getElementById('banknifty-loading').style.display = 'block';
            fetch('/api/banknifty')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('banknifty-loading').style.display = 'none';
                    if (data.success) {
                        document.getElementById('banknifty-total').textContent = data.summary.unique_banks;
                        document.getElementById('banknifty-coverage').textContent = data.summary.coverage_percent + '%';
                        document.getElementById('banknifty-bullish').textContent = data.summary.bullish_banks;
                        document.getElementById('banknifty-bearish').textContent = data.summary.bearish_banks;
                        document.getElementById('banknifty-neutral').textContent = data.summary.neutral_banks;
                        
                        const overallSentiment = data.summary.overall_sentiment;
                        document.getElementById('banknifty-overall').textContent = overallSentiment;
                        document.getElementById('banknifty-overall').className = `badge ${getSentimentBadge(overallSentiment)}`;
                        
                        const tbody = document.getElementById('banknifty-tbody');
                        tbody.innerHTML = '';
                        data.data.forEach((item, index) => {
                            const row = tbody.insertRow();
                            row.innerHTML = `
                                <td>${index + 1}</td>
                                <td><strong>${item.symbol}</strong></td>
                                <td>${item.weightage}%</td>
                                <td>${formatPrice(item.current_price)}</td>
                                <td>${formatPCR(item.pcr)}</td>
                                <td><span class="${getSentimentClass(item.sentiment)}">${item.sentiment}</span></td>
                            `;
                        });
                        document.getElementById('banknifty-table').style.display = 'block';
                    }
                })
                .catch(error => console.error('Bank NIFTY load error:', error));
        }

        function refreshData() {
            loadNifty50();
            loadBankNifty();
            updateTimestamp();
        }

        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            setInterval(refreshData, 180000); // Auto-refresh every 3 minutes
        });
    </script>
</body>
</html>
"""

@app.route('/')
def mobile_dashboard():
    """Mobile-optimized dashboard"""
    return MOBILE_TEMPLATE

@app.route('/api/nifty50')
def api_nifty50():
    """Enhanced NIFTY 50 analysis API"""
    try:
        data = angel_client.analyze_nifty50_enhanced()
        unique_stocks = set(item['symbol'] for item in data)
        
        # Calculate overall sentiment
        sentiments = [item['sentiment'] for item in data]
        bullish_count = sentiments.count('Bullish')
        bearish_count = sentiments.count('Bearish')
        neutral_count = sentiments.count('Neutral')
        
        return jsonify({
            'success': True,
            'data': data,
            'summary': {
                'total_matches': len(data),
                'unique_stocks': len(unique_stocks),
                'coverage_percent': round(len(unique_stocks) / 50 * 100, 1),
                'bullish_stocks': bullish_count,
                'bearish_stocks': bearish_count,
                'neutral_stocks': neutral_count,
                'overall_sentiment': 'Bullish' if bullish_count > bearish_count else 'Bearish' if bearish_count > bullish_count else 'Neutral'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/banknifty')
def api_banknifty():
    """Enhanced Bank NIFTY analysis API"""
    try:
        data = angel_client.analyze_banknifty_enhanced()
        unique_banks = set(item['symbol'] for item in data)
        
        # Calculate overall sentiment
        sentiments = [item['sentiment'] for item in data]
        bullish_count = sentiments.count('Bullish')
        bearish_count = sentiments.count('Bearish')
        neutral_count = sentiments.count('Neutral')
        
        return jsonify({
            'success': True,
            'data': data,
            'summary': {
                'total_matches': len(data),
                'unique_banks': len(unique_banks),
                'coverage_percent': round(len(unique_banks) / 12 * 100, 1),
                'bullish_banks': bullish_count,
                'bearish_banks': bearish_count,
                'neutral_banks': neutral_count,
                'overall_sentiment': 'Bullish' if bullish_count > bearish_count else 'Bearish' if bearish_count > bullish_count else 'Neutral'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check for deployment platforms"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("📱 MOBILE MARKET ANALYSIS - CLOUD READY")
    print("=" * 50)
    print(f"🌐 Dashboard: http://localhost:{PORT}")
    print(f"📊 NIFTY 50 API: http://localhost:{PORT}/api/nifty50")
    print(f"🏦 Bank NIFTY API: http://localhost:{PORT}/api/banknifty")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)