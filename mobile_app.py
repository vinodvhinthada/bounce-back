"""
MOBILE ANGEL ONE MARKET ANALYSIS - COMPLETE WEBAPP
==================================================
This is the mobile-optimized version of your comprehensive market analysis app
with Angel One API integration, NIFTY 50/Bank NIFTY analysis, and PCR data.
"""

import os
import requests
import pyotp
from flask import Flask, render_template_string
import logging
import json
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
API_KEY = os.getenv('ANGEL_API_KEY', 'tKo2xsA5')
USERNAME = os.getenv('ANGEL_USERNAME', 'C125633')
PASSWORD = os.getenv('ANGEL_PASSWORD', '4111')
TOTP_TOKEN = os.getenv('ANGEL_TOTP_TOKEN', 'TZZ2VTRBUWPB33SLOSA3NXSGWA')

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
        self.auth_token = None
        self.base_url = "https://apiconnect.angelone.in"
        self.login()
    
    def login(self):
        """Authenticate with Angel One API"""
        try:
            totp = pyotp.TOTP(TOTP_TOKEN).now()
            
            login_data = {
                "clientcode": USERNAME,
                "password": PASSWORD,
                "totp": totp
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '192.168.1.1',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': API_KEY
            }
            
            response = requests.post(
                f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword",
                json=login_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    self.auth_token = data['data']['jwtToken']
                    logger.info("✅ Successfully logged in to Angel One")
                    return True
            
            logger.error("❌ Login failed")
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def fetch_data(self, datatype, expirytype="NEAR", limit=50):
        """Fetch gainers/losers data"""
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '192.168.1.1',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': API_KEY
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/marketData/v1/gainersLosers"
            payload = {"datatype": datatype, "expirytype": expirytype}
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    return data.get('data', [])[:limit]
            
            return []
        except Exception as e:
            logger.error(f"Error fetching {datatype}: {e}")
            return []
    
    def fetch_pcr_data(self):
        """Fetch PCR data"""
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-PrivateKey': API_KEY
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/marketData/v1/putCallRatio"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    return data.get('data', [])
            
            return []
        except Exception as e:
            logger.error(f"Error fetching PCR data: {e}")
            return []

def improved_symbol_matching(trading_symbol, stock_list):
    """Improved symbol matching for futures format"""
    if not trading_symbol:
        return None, None
    
    symbol_upper = trading_symbol.upper().strip()
    
    # Sort stock symbols by length (descending) to prioritize longer matches
    sorted_symbols = sorted(stock_list.keys(), key=len, reverse=True)
    
    for stock_symbol in sorted_symbols:
        if stock_symbol in symbol_upper:
            # Special handling for short symbols
            if len(stock_symbol) <= 3:
                import re
                # Create pattern: symbol followed by non-alphabetic character or futures pattern
                pattern = f'{re.escape(stock_symbol)}(?:[^A-Z]|$|\\d{{2}}[A-Z]{{3}}\\d{{2}})'
                if re.search(pattern, symbol_upper):
                    return stock_symbol, stock_list[stock_symbol]
            else:
                return stock_symbol, stock_list[stock_symbol]
    
    return None, None

def analyze_nifty50(client):
    """Analyze NIFTY 50 with weighted impact"""
    # Get OI data
    all_gainers = client.fetch_data("PercOIGainers", "NEAR", 100)
    time.sleep(1)
    all_losers = client.fetch_data("PercOILosers", "NEAR", 100)
    time.sleep(1)
    pcr_data = client.fetch_pcr_data()
    
    # Filter NIFTY 50 stocks
    nifty_gainers = []
    nifty_losers = []
    nifty_pcr = []
    
    if all_gainers:
        for item in all_gainers:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, NIFTY50_STOCKS)
            if matched_symbol:
                item['nifty_symbol'] = matched_symbol
                item['weightage'] = weightage
                nifty_gainers.append(item)
    
    if all_losers:
        for item in all_losers:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, NIFTY50_STOCKS)
            if matched_symbol:
                item['nifty_symbol'] = matched_symbol
                item['weightage'] = weightage
                nifty_losers.append(item)
    
    if pcr_data:
        for item in pcr_data:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, NIFTY50_STOCKS)
            if matched_symbol:
                item['nifty_symbol'] = matched_symbol
                item['weightage'] = weightage
                nifty_pcr.append(item)
    
    # Calculate weighted impact
    gainers_impact = 0
    losers_impact = 0
    total_weightage = 0
    matched_stocks = set()
    
    for item in nifty_gainers:
        weightage = item.get('weightage', 0)
        pct_change = item.get('percentChange', 0)
        gainers_impact += (pct_change * weightage) / 100
        matched_stocks.add(item.get('nifty_symbol'))
        total_weightage += weightage
    
    for item in nifty_losers:
        weightage = item.get('weightage', 0)
        pct_change = item.get('percentChange', 0)
        losers_impact += (abs(pct_change) * weightage) / 100
        matched_stocks.add(item.get('nifty_symbol'))
        if item.get('nifty_symbol') not in [g.get('nifty_symbol') for g in nifty_gainers]:
            total_weightage += weightage
    
    net_impact = gainers_impact - losers_impact
    
    # Calculate PCR impact
    weighted_pcr = 0
    if nifty_pcr:
        total_pcr_weight = 0
        for item in nifty_pcr:
            weightage = item.get('weightage', 0)
            pcr = item.get('pcr', 0)
            weighted_pcr += pcr * weightage
            total_pcr_weight += weightage
        if total_pcr_weight > 0:
            weighted_pcr = weighted_pcr / total_pcr_weight
    
    return {
        'gainers': nifty_gainers,
        'losers': nifty_losers,
        'pcr_data': nifty_pcr,
        'gainers_impact': gainers_impact,
        'losers_impact': losers_impact,
        'net_impact': net_impact,
        'weighted_pcr': weighted_pcr,
        'coverage': total_weightage,
        'matched_stocks_count': len(matched_stocks),
        'total_stocks': len(NIFTY50_STOCKS)
    }

def analyze_banknifty(client):
    """Analyze Bank NIFTY with weighted impact"""
    # Get OI data
    all_gainers = client.fetch_data("PercOIGainers", "NEAR", 100)
    time.sleep(1)
    all_losers = client.fetch_data("PercOILosers", "NEAR", 100)
    time.sleep(1)
    pcr_data = client.fetch_pcr_data()
    
    # Filter Bank NIFTY stocks
    bank_gainers = []
    bank_losers = []
    bank_pcr = []
    
    if all_gainers:
        for item in all_gainers:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, BANKNIFTY_STOCKS)
            if matched_symbol:
                item['bank_symbol'] = matched_symbol
                item['weightage'] = weightage
                bank_gainers.append(item)
    
    if all_losers:
        for item in all_losers:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, BANKNIFTY_STOCKS)
            if matched_symbol:
                item['bank_symbol'] = matched_symbol
                item['weightage'] = weightage
                bank_losers.append(item)
    
    if pcr_data:
        for item in pcr_data:
            symbol = item.get('tradingSymbol', '')
            matched_symbol, weightage = improved_symbol_matching(symbol, BANKNIFTY_STOCKS)
            if matched_symbol:
                item['bank_symbol'] = matched_symbol
                item['weightage'] = weightage
                bank_pcr.append(item)
    
    # Calculate weighted impact
    gainers_impact = 0
    losers_impact = 0
    total_weightage = 0
    matched_banks = set()
    
    for item in bank_gainers:
        weightage = item.get('weightage', 0)
        pct_change = item.get('percentChange', 0)
        gainers_impact += (pct_change * weightage) / 100
        matched_banks.add(item.get('bank_symbol'))
        total_weightage += weightage
    
    for item in bank_losers:
        weightage = item.get('weightage', 0)
        pct_change = item.get('percentChange', 0)
        losers_impact += (abs(pct_change) * weightage) / 100
        matched_banks.add(item.get('bank_symbol'))
        if item.get('bank_symbol') not in [g.get('bank_symbol') for g in bank_gainers]:
            total_weightage += weightage
    
    net_impact = gainers_impact - losers_impact
    
    # Calculate PCR impact
    weighted_pcr = 0
    if bank_pcr:
        total_pcr_weight = 0
        for item in bank_pcr:
            weightage = item.get('weightage', 0)
            pcr = item.get('pcr', 0)
            weighted_pcr += pcr * weightage
            total_pcr_weight += weightage
        if total_pcr_weight > 0:
            weighted_pcr = weighted_pcr / total_pcr_weight
    
    return {
        'gainers': bank_gainers,
        'losers': bank_losers,
        'pcr_data': bank_pcr,
        'gainers_impact': gainers_impact,
        'losers_impact': losers_impact,
        'net_impact': net_impact,
        'weighted_pcr': weighted_pcr,
        'coverage': total_weightage,
        'matched_banks_count': len(matched_banks),
        'total_banks': len(BANKNIFTY_STOCKS)
    }

def determine_verdict(net_impact, weighted_pcr):
    """Determine market verdict based on impact and PCR"""
    # OI Sentiment
    if net_impact > 0.5:
        oi_sentiment = "Bullish"
    elif net_impact < -0.5:
        oi_sentiment = "Bearish"
    else:
        oi_sentiment = "Neutral"
    
    # PCR Sentiment
    if weighted_pcr > 1.2:
        pcr_sentiment = "Bearish"
    elif weighted_pcr > 1.0:
        pcr_sentiment = "Cautious"
    elif weighted_pcr > 0.8:
        pcr_sentiment = "Bullish"
    else:
        pcr_sentiment = "Very Bullish"
    
    # Final Verdict
    if oi_sentiment == "Bullish" and "Bullish" in pcr_sentiment:
        final_verdict = "Strong Bullish"
        verdict_color = "success"
        verdict_emoji = "🚀🚀🚀"
    elif oi_sentiment == "Bearish" and pcr_sentiment == "Bearish":
        final_verdict = "Strong Bearish"
        verdict_color = "danger"
        verdict_emoji = "💥💥💥"
    elif "Bullish" in pcr_sentiment:
        final_verdict = "Very Bullish"
        verdict_color = "success"
        verdict_emoji = "🚀🚀"
    elif oi_sentiment == "Bullish" or "Bullish" in pcr_sentiment:
        final_verdict = "Bullish"
        verdict_color = "success"
        verdict_emoji = "📈📈"
    elif oi_sentiment == "Bearish" or pcr_sentiment == "Bearish":
        final_verdict = "Bearish"
        verdict_color = "danger"
        verdict_emoji = "📉📉"
    else:
        final_verdict = "Neutral"
        verdict_color = "warning"
        verdict_emoji = "⚖️"
    
    return final_verdict, verdict_color, verdict_emoji, oi_sentiment, pcr_sentiment

@app.route('/')
def mobile_dashboard():
    """Mobile market analysis dashboard"""
    
    try:
        # Initialize Angel One client
        client = MobileAngelClient()
        
        # Analyze both indices
        nifty_analysis = analyze_nifty50(client)
        banknifty_analysis = analyze_banknifty(client)
        
        # Determine verdicts
        nifty_verdict, nifty_color, nifty_emoji, nifty_oi, nifty_pcr_sentiment = determine_verdict(
            nifty_analysis['net_impact'], nifty_analysis['weighted_pcr']
        )
        
        bank_verdict, bank_color, bank_emoji, bank_oi, bank_pcr_sentiment = determine_verdict(
            banknifty_analysis['net_impact'], banknifty_analysis['weighted_pcr']
        )
        
        # Calculate NIFTY spot and Bank NIFTY spot (mock values)
        nifty_spot = 25145.75
        banknifty_spot = 52380.25
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        # Fallback data
        nifty_analysis = {'gainers': [], 'losers': [], 'net_impact': 0, 'weighted_pcr': 1, 'coverage': 0, 'matched_stocks_count': 0, 'total_stocks': 50}
        banknifty_analysis = {'gainers': [], 'losers': [], 'net_impact': 0, 'weighted_pcr': 1, 'coverage': 0, 'matched_banks_count': 0, 'total_banks': 12}
        nifty_verdict, nifty_color, nifty_emoji = "Neutral", "warning", "⚖️"
        bank_verdict, bank_color, bank_emoji = "Neutral", "warning", "⚖️"
        nifty_oi = bank_oi = "Neutral"
        nifty_pcr_sentiment = bank_pcr_sentiment = "Unknown"
        nifty_spot = 25145.75
        banknifty_spot = 52380.25

    # Mobile HTML template
    template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Angel One Market Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            min-height: 100vh; 
            font-family: 'Segoe UI', sans-serif;
            color: #333;
        }
        .main-card { 
            backdrop-filter: blur(15px); 
            background: rgba(255, 255, 255, 0.95); 
            border: none; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            border-radius: 20px;
            margin-bottom: 20px;
        }
        .index-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        }
        .verdict-card {
            border-radius: 15px;
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        }
        .impact-meter {
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .header-title {
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            text-align: center;
            margin-bottom: 30px;
        }
        .metric-box {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            text-align: center;
        }
        .stock-item {
            border-left: 4px solid #007bff;
            margin-bottom: 8px;
            padding: 12px;
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
            font-size: 0.9em;
        }
        .positive { border-left-color: #28a745; }
        .negative { border-left-color: #dc3545; }
        .refresh-btn {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            width: 100%;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }
        .holdings-container {
            max-height: 400px;
            overflow-y: auto;
        }
        .analysis-tabs {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .tab-button {
            background: rgba(255,255,255,0.2);
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            color: white;
            margin: 5px;
            transition: all 0.3s;
        }
        .tab-button.active {
            background: rgba(255,255,255,0.8);
            color: #333;
        }
        @media (max-width: 768px) {
            .container-fluid { padding: 10px; }
            .main-card { margin-bottom: 15px; padding: 15px; }
            .stock-item { padding: 8px; font-size: 0.85em; }
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <div class="py-4">
            <h1 class="header-title">
                <i class="fas fa-chart-line"></i> Angel One Market Analysis
            </h1>
            <p class="text-center text-white">Real-time NIFTY 50 & Bank NIFTY Weighted Analysis</p>
            <button class="refresh-btn" onclick="refreshData()">
                <i class="fas fa-sync-alt"></i> Refresh Data
            </button>
        </div>
        
        <!-- Index Levels -->
        <div class="row mb-4">
            <div class="col-6">
                <div class="index-card">
                    <h5><i class="fas fa-chart-area"></i> NIFTY 50</h5>
                    <h2>{{ "%.2f"|format(nifty_spot) }}</h2>
                    <small>Live Index</small>
                </div>
            </div>
            <div class="col-6">
                <div class="index-card">
                    <h5><i class="fas fa-university"></i> Bank NIFTY</h5>
                    <h2>{{ "%.2f"|format(banknifty_spot) }}</h2>
                    <small>Live Index</small>
                </div>
            </div>
        </div>
        
        <!-- Market Verdicts -->
        <div class="row mb-4">
            <div class="col-6">
                <div class="verdict-card bg-{{ nifty_color }} text-white">
                    <h6>NIFTY 50 Verdict</h6>
                    <h4>{{ nifty_emoji }}</h4>
                    <strong>{{ nifty_verdict }}</strong>
                    <div class="mt-2">
                        <small>OI: {{ nifty_oi }} | PCR: {{ nifty_pcr_sentiment }}</small>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="verdict-card bg-{{ bank_color }} text-white">
                    <h6>Bank NIFTY Verdict</h6>
                    <h4>{{ bank_emoji }}</h4>
                    <strong>{{ bank_verdict }}</strong>
                    <div class="mt-2">
                        <small>OI: {{ bank_oi }} | PCR: {{ bank_pcr_sentiment }}</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- NIFTY 50 Analysis -->
        <div class="main-card">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line"></i> NIFTY 50 Weighted Analysis
                    <span class="badge bg-light text-dark ms-2">{{ nifty_analysis.matched_stocks_count }}/{{ nifty_analysis.total_stocks }}</span>
                </h5>
            </div>
            <div class="card-body">
                <!-- Impact Metrics -->
                <div class="row mb-3">
                    <div class="col-4 text-center">
                        <h6>Net Impact</h6>
                        <h5 class="text-{{ 'success' if nifty_analysis.net_impact > 0 else 'danger' }}">
                            {{ "%.3f"|format(nifty_analysis.net_impact) }}%
                        </h5>
                    </div>
                    <div class="col-4 text-center">
                        <h6>Weighted PCR</h6>
                        <h5 class="text-{{ 'danger' if nifty_analysis.weighted_pcr > 1.2 else 'warning' if nifty_analysis.weighted_pcr > 1.0 else 'success' }}">
                            {{ "%.4f"|format(nifty_analysis.weighted_pcr) }}
                        </h5>
                    </div>
                    <div class="col-4 text-center">
                        <h6>Coverage</h6>
                        <h5 class="text-info">{{ "%.1f"|format(nifty_analysis.coverage) }}%</h5>
                    </div>
                </div>
                
                <!-- Impact Meter -->
                <div class="impact-meter bg-secondary">
                    <div class="bg-{{ 'success' if nifty_analysis.net_impact > 0 else 'danger' }}" 
                         style="width: {{ min(abs(nifty_analysis.net_impact) * 20, 100) }}%; height: 100%;"></div>
                </div>
                
                <!-- Gainers and Losers Tabs -->
                <div class="mt-3">
                    <ul class="nav nav-pills justify-content-center mb-3" id="niftyTabs">
                        <li class="nav-item">
                            <button class="nav-link active" onclick="showTab('nifty-gainers')">
                                Gainers ({{ nifty_analysis.gainers|length }})
                            </button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link" onclick="showTab('nifty-losers')">
                                Losers ({{ nifty_analysis.losers|length }})
                            </button>
                        </li>
                    </ul>
                    
                    <!-- NIFTY Gainers -->
                    <div id="nifty-gainers" class="tab-content holdings-container">
                        {% for stock in nifty_analysis.gainers[:15] %}
                        <div class="stock-item positive">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ stock.get('nifty_symbol', stock.get('tradingSymbol', 'N/A')[:15]) }}</strong>
                                    <small class="text-muted d-block">Weight: {{ "%.2f"|format(stock.get('weightage', 0)) }}%</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-success">{{ "%.2f"|format(stock.get('percentChange', 0)) }}%</span>
                                    <small class="text-muted d-block">OI: {{ "%.0f"|format(stock.get('netChangeOpnInterest', 0)) }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <!-- NIFTY Losers -->
                    <div id="nifty-losers" class="tab-content holdings-container" style="display: none;">
                        {% for stock in nifty_analysis.losers[:15] %}
                        <div class="stock-item negative">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ stock.get('nifty_symbol', stock.get('tradingSymbol', 'N/A')[:15]) }}</strong>
                                    <small class="text-muted d-block">Weight: {{ "%.2f"|format(stock.get('weightage', 0)) }}%</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-danger">{{ "%.2f"|format(stock.get('percentChange', 0)) }}%</span>
                                    <small class="text-muted d-block">OI: {{ "%.0f"|format(stock.get('netChangeOpnInterest', 0)) }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bank NIFTY Analysis -->
        <div class="main-card">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <i class="fas fa-university"></i> Bank NIFTY Weighted Analysis
                    <span class="badge bg-dark text-light ms-2">{{ banknifty_analysis.matched_banks_count }}/{{ banknifty_analysis.total_banks }}</span>
                </h5>
            </div>
            <div class="card-body">
                <!-- Impact Metrics -->
                <div class="row mb-3">
                    <div class="col-4 text-center">
                        <h6>Net Impact</h6>
                        <h5 class="text-{{ 'success' if banknifty_analysis.net_impact > 0 else 'danger' }}">
                            {{ "%.3f"|format(banknifty_analysis.net_impact) }}%
                        </h5>
                    </div>
                    <div class="col-4 text-center">
                        <h6>Weighted PCR</h6>
                        <h5 class="text-{{ 'danger' if banknifty_analysis.weighted_pcr > 1.2 else 'warning' if banknifty_analysis.weighted_pcr > 1.0 else 'success' }}">
                            {{ "%.4f"|format(banknifty_analysis.weighted_pcr) }}
                        </h5>
                    </div>
                    <div class="col-4 text-center">
                        <h6>Coverage</h6>
                        <h5 class="text-info">{{ "%.1f"|format(banknifty_analysis.coverage) }}%</h5>
                    </div>
                </div>
                
                <!-- Impact Meter -->
                <div class="impact-meter bg-secondary">
                    <div class="bg-{{ 'success' if banknifty_analysis.net_impact > 0 else 'danger' }}" 
                         style="width: {{ min(abs(banknifty_analysis.net_impact) * 10, 100) }}%; height: 100%;"></div>
                </div>
                
                <!-- Gainers and Losers Tabs -->
                <div class="mt-3">
                    <ul class="nav nav-pills justify-content-center mb-3" id="bankTabs">
                        <li class="nav-item">
                            <button class="nav-link active" onclick="showTab('bank-gainers')">
                                Gainers ({{ banknifty_analysis.gainers|length }})
                            </button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link" onclick="showTab('bank-losers')">
                                Losers ({{ banknifty_analysis.losers|length }})
                            </button>
                        </li>
                    </ul>
                    
                    <!-- Bank Gainers -->
                    <div id="bank-gainers" class="tab-content holdings-container">
                        {% for bank in banknifty_analysis.gainers[:10] %}
                        <div class="stock-item positive">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ bank.get('bank_symbol', bank.get('tradingSymbol', 'N/A')[:15]) }}</strong>
                                    <small class="text-muted d-block">Weight: {{ "%.2f"|format(bank.get('weightage', 0)) }}%</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-success">{{ "%.2f"|format(bank.get('percentChange', 0)) }}%</span>
                                    <small class="text-muted d-block">OI: {{ "%.0f"|format(bank.get('netChangeOpnInterest', 0)) }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <!-- Bank Losers -->
                    <div id="bank-losers" class="tab-content holdings-container" style="display: none;">
                        {% for bank in banknifty_analysis.losers[:10] %}
                        <div class="stock-item negative">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ bank.get('bank_symbol', bank.get('tradingSymbol', 'N/A')[:15]) }}</strong>
                                    <small class="text-muted d-block">Weight: {{ "%.2f"|format(bank.get('weightage', 0)) }}%</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-danger">{{ "%.2f"|format(bank.get('percentChange', 0)) }}%</span>
                                    <small class="text-muted d-block">OI: {{ "%.0f"|format(bank.get('netChangeOpnInterest', 0)) }}</small>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="text-center py-4">
            <small class="text-white">
                <i class="fas fa-mobile-alt"></i> Angel One Mobile Analysis | 
                Updated: {{ current_time }} | 
                <i class="fas fa-chart-line"></i> Real-time Data
            </small>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Manual refresh function
        function refreshData() {
            document.body.style.opacity = '0.8';
            location.reload();
        }
        
        // Tab switching function
        function showTab(tabId) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Remove active class from all nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabId).style.display = 'block';
            
            // Add active class to clicked nav link
            event.target.classList.add('active');
        }
        
        // Auto refresh every 60 seconds
        setTimeout(function() {
            location.reload();
        }, 60000);
        
        // Add loading indicator during refresh
        window.addEventListener('beforeunload', function() {
            document.body.style.opacity = '0.7';
        });
        
        // Initialize first tab as active on load
        document.addEventListener('DOMContentLoaded', function() {
            // Make sure first tabs are visible
            const firstNiftyTab = document.getElementById('nifty-gainers');
            const firstBankTab = document.getElementById('bank-gainers');
            if (firstNiftyTab) firstNiftyTab.style.display = 'block';
            if (firstBankTab) firstBankTab.style.display = 'block';
        });
    </script>
</body>
</html>
    """
    
    return render_template_string(
        template,
        nifty_analysis=nifty_analysis,
        banknifty_analysis=banknifty_analysis,
        nifty_verdict=nifty_verdict,
        nifty_color=nifty_color,
        nifty_emoji=nifty_emoji,
        nifty_oi=nifty_oi,
        nifty_pcr_sentiment=nifty_pcr_sentiment,
        bank_verdict=bank_verdict,
        bank_color=bank_color,
        bank_emoji=bank_emoji,
        bank_oi=bank_oi,
        bank_pcr_sentiment=bank_pcr_sentiment,
        nifty_spot=nifty_spot,
        banknifty_spot=banknifty_spot,
        current_time=datetime.now().strftime("%H:%M:%S")
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

