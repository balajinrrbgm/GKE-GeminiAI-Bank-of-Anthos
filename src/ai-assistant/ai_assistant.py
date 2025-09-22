# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AI Assistant service for Bank of Anthos using Gemini Pro API"""

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from collections import defaultdict

import google.generativeai as genai
from flask import Flask, request, jsonify, abort

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.warning("GEMINI_API_KEY not set. AI features will be disabled.")
    model = None

# Service endpoints
USERSERVICE_URL = os.environ.get('USERSERVICE_URL', 'http://userservice:8080')
BALANCEREADER_URL = os.environ.get('BALANCEREADER_URL', 'http://balancereader:8080')
TRANSACTIONHISTORY_URL = os.environ.get('TRANSACTIONHISTORY_URL', 'http://transactionhistory:8080')
CONTACTS_URL = os.environ.get('CONTACTS_URL', 'http://contacts:8080')

class BankingAIAssistant:
    """AI Assistant for banking operations using Gemini Pro"""
    
    def __init__(self):
        self.model = model
        self.conversation_context = {}
    
    def get_user_data(self, username: str, auth_token: str = None) -> Dict[str, Any]:
        """Fetch user data from various microservices"""
        user_data = {'username': username}
        
        try:
            # If no auth token provided, get one from userservice
            if not auth_token or auth_token == 'demo-token':
                logger.info(f"Getting auth token for user: {username}")
                login_response = requests.get(
                    f'{USERSERVICE_URL}/login',
                    params={'username': username, 'password': 'bankofanthos'},
                    timeout=5
                )
                if login_response.status_code == 200:
                    auth_token = login_response.json().get('token')
                    logger.info("Successfully obtained auth token")
                else:
                    logger.warning(f"Failed to get auth token: {login_response.status_code}")
                    auth_token = None
            
            if auth_token:
                headers = {'Authorization': f'Bearer {auth_token}'}
                
                # Extract account ID from JWT token
                import base64
                import json as json_lib
                try:
                    token_parts = auth_token.split('.')
                    payload = base64.b64decode(token_parts[1] + '==')
                    token_data = json_lib.loads(payload)
                    account_id = token_data.get('acct', username)
                    logger.info(f"Extracted account ID: {account_id}")
                except Exception as e:
                    logger.error(f"Failed to decode JWT: {e}")
                    account_id = username
                
                # Get balance using account ID
                balance_response = requests.get(
                    f'{BALANCEREADER_URL}/balances/{account_id}',
                    headers=headers,
                    timeout=5
                )
                if balance_response.status_code == 200:
                    balance_cents = balance_response.json()
                    balance_dollars = balance_cents / 100.0  # Convert cents to dollars
                    user_data['balance'] = {"balance": balance_dollars, "currency": "USD"}
                    logger.info(f"Retrieved real balance: ${balance_dollars}")
                else:
                    logger.warning(f"Balance request failed: {balance_response.status_code}")
                    user_data['balance'] = {"balance": 1250.75, "currency": "USD"}
                
                # Get transaction history using account ID
                transactions_response = requests.get(
                    f'{TRANSACTIONHISTORY_URL}/transactions/{account_id}',
                    headers=headers,
                    timeout=5
                )
                if transactions_response.status_code == 200:
                    raw_transactions = transactions_response.json()
                    # Convert transaction format for AI analysis
                    formatted_transactions = []
                    for tx in raw_transactions[:20]:  # Get more transactions for better analysis
                        amount_cents = tx.get('amount', 0)
                        amount_dollars = amount_cents / 100.0
                        
                        # Determine if it's incoming or outgoing based on account
                        is_incoming = tx.get('toAccountNum') == account_id
                        from_account = tx.get('fromAccountNum', 'Unknown')
                        to_account = tx.get('toAccountNum', 'Unknown')
                        
                        # Find contact names for better description
                        contact_name = None
                        other_account = from_account if is_incoming else to_account
                        for contact in user_data.get('contacts', []):
                            if contact.get('account_num') == other_account:
                                contact_name = contact.get('label', 'Unknown Contact')
                                break
                        
                        if contact_name:
                            description = f"{'Payment from' if is_incoming else 'Payment to'} {contact_name}"
                        else:
                            description = f"{'Transfer from' if is_incoming else 'Transfer to'} account {other_account}"
                        
                        formatted_transactions.append({
                            "amount": f"{'+'if is_incoming else '-'}{amount_dollars:.2f}",
                            "description": description,
                            "timestamp": tx.get('timestamp', ''),
                            "raw_amount": amount_cents,
                            "is_incoming": is_incoming,
                            "from_account": from_account,
                            "to_account": to_account,
                            "transaction_id": tx.get('transactionId', '')
                        })
                    
                    user_data['transactions'] = formatted_transactions
                    logger.info(f"Retrieved {len(formatted_transactions)} formatted transactions")
                else:
                    logger.warning(f"Transactions request failed: {transactions_response.status_code}")
                    user_data['transactions'] = [
                        {"amount": "-45.30", "description": "Coffee Shop", "timestamp": "2024-01-15T10:30:00Z"},
                        {"amount": "-120.00", "description": "Grocery Store", "timestamp": "2024-01-14T16:45:00Z"},
                        {"amount": "2500.00", "description": "Salary Deposit", "timestamp": "2024-01-13T09:00:00Z"},
                        {"amount": "-85.50", "description": "Gas Station", "timestamp": "2024-01-12T18:20:00Z"}
                    ]
                
                # Get contacts
                contacts_response = requests.get(
                    f'{CONTACTS_URL}/contacts/{username}',
                    headers=headers,
                    timeout=5
                )
                if contacts_response.status_code == 200:
                    user_data['contacts'] = contacts_response.json()
                    logger.info(f"Retrieved {len(user_data['contacts'])} contacts")
                else:
                    logger.warning(f"Contacts request failed: {contacts_response.status_code}")
                    user_data['contacts'] = [
                        {"label": "Alice Johnson", "account_num": "1234567890"},
                        {"label": "Bob Smith", "account_num": "0987654321"}
                    ]
            else:
                logger.warning("No valid auth token available, using fallback data")
                # Provide fallback demo data when authentication fails
                user_data.update({
                    'balance': {"balance": 1250.75, "currency": "USD"},
                    'transactions': [
                        {"amount": "-45.30", "description": "Coffee Shop", "timestamp": "2024-01-15T10:30:00Z"},
                        {"amount": "-120.00", "description": "Grocery Store", "timestamp": "2024-01-14T16:45:00Z"},
                        {"amount": "2500.00", "description": "Salary Deposit", "timestamp": "2024-01-13T09:00:00Z"},
                        {"amount": "-85.50", "description": "Gas Station", "timestamp": "2024-01-12T18:20:00Z"}
                    ],
                    'contacts': [
                        {"label": "Alice Johnson", "account_num": "1234567890"},
                        {"label": "Bob Smith", "account_num": "0987654321"}
                    ]
                })
                
        except requests.RequestException as e:
            logger.error(f"Error fetching user data: {e}")
            # Provide fallback demo data on request failure
            user_data.update({
                'balance': {"balance": 1250.75, "currency": "USD"},
                'transactions': [
                    {"amount": "-45.30", "description": "Coffee Shop", "timestamp": "2024-01-15T10:30:00Z"},
                    {"amount": "-120.00", "description": "Grocery Store", "timestamp": "2024-01-14T16:45:00Z"},
                    {"amount": "2500.00", "description": "Salary Deposit", "timestamp": "2024-01-13T09:00:00Z"},
                    {"amount": "-85.50", "description": "Gas Station", "timestamp": "2024-01-12T18:20:00Z"}
                ],
                'contacts': [
                    {"label": "Alice Johnson", "account_num": "1234567890"},
                    {"label": "Bob Smith", "account_num": "0987654321"}
                ]
            })
        
        return user_data
    
    def generate_detailed_analytics(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed financial analytics with categorization and trends"""
        transactions = user_data.get('transactions', [])
        balance = user_data.get('balance', {}).get('balance', 0)
        
        if not transactions:
            return {"message": "No transaction data available for analysis"}
        
        # Advanced analytics
        analytics = {
            "current_balance": balance,
            "total_transactions": len(transactions),
            "spending_by_month": {},
            "income_by_month": {},
            "transaction_categories": {},
            "financial_health_score": 0,
            "trends": {},
            "contact_analysis": {}
        }
        
        # Analyze transactions by month and category
        total_income = 0
        total_spending = 0
        contact_frequency = {}
        
        for transaction in transactions:
            timestamp = transaction.get('timestamp', '')
            amount_str = transaction.get('amount', '0')
            description = transaction.get('description', '')
            
            try:
                if 'raw_amount' in transaction:
                    amount = transaction['raw_amount'] / 100.0
                    is_income = amount_str.startswith('+')
                else:
                    amount = float(amount_str)
                    is_income = amount > 0
                
                # Monthly analysis
                if timestamp:
                    month = timestamp[:7]  # YYYY-MM
                    if is_income:
                        analytics["income_by_month"][month] = analytics["income_by_month"].get(month, 0) + abs(amount)
                        total_income += abs(amount)
                    else:
                        analytics["spending_by_month"][month] = analytics["spending_by_month"].get(month, 0) + abs(amount)
                        total_spending += abs(amount)
                
                # Category analysis
                category = self.categorize_transaction(description)
                analytics["transaction_categories"][category] = analytics["transaction_categories"].get(category, 0) + abs(amount)
                
                # Contact analysis
                contact_name = self.extract_contact_from_description(description)
                if contact_name:
                    if contact_name not in contact_frequency:
                        contact_frequency[contact_name] = {"count": 0, "total_amount": 0, "type": "income" if is_income else "expense"}
                    contact_frequency[contact_name]["count"] += 1
                    contact_frequency[contact_name]["total_amount"] += abs(amount)
                    
            except (ValueError, TypeError):
                continue
        
        analytics["contact_analysis"] = contact_frequency
        analytics["total_income"] = total_income
        analytics["total_spending"] = total_spending
        analytics["net_change"] = total_income - total_spending
        
        # Calculate financial health score (0-100)
        savings_rate = (total_income - total_spending) / total_income if total_income > 0 else 0
        balance_ratio = min(balance / 5000, 1)  # Normalize against $5000 target
        transaction_diversity = min(len(analytics["transaction_categories"]) / 5, 1)
        
        analytics["financial_health_score"] = int((savings_rate * 40 + balance_ratio * 40 + transaction_diversity * 20) * 100)
        
        return analytics
    
    def categorize_transaction(self, description: str) -> str:
        """Categorize transactions based on description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['salary', 'deposit', 'income', 'received from']):
            return 'Income'
        elif any(word in description_lower for word in ['grocery', 'food', 'restaurant', 'coffee']):
            return 'Food & Dining'
        elif any(word in description_lower for word in ['gas', 'fuel', 'transport', 'uber', 'taxi']):
            return 'Transportation'
        elif any(word in description_lower for word in ['shopping', 'retail', 'amazon', 'store']):
            return 'Shopping'
        elif any(word in description_lower for word in ['rent', 'mortgage', 'utilities', 'electric', 'water']):
            return 'Housing'
        elif any(word in description_lower for word in ['transfer', 'sent to', 'payment']):
            return 'Transfers'
        else:
            return 'Other'
    
    def extract_contact_from_description(self, description: str) -> str:
        """Extract contact names from transaction descriptions"""
        # Look for common patterns like "Transfer from Alice" or "Sent to Bob"
        import re
        patterns = [
            r'from\s+([A-Z][a-z]+)',
            r'to\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+\(',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
        return None
    
    def generate_financial_insights(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive AI-powered financial insights with visualization data"""
        if not self.model:
            return {
                "insights": "AI insights are currently unavailable. Please check configuration.",
                "analytics": {},
                "visualizations": {}
            }
        
        try:
            # Generate detailed analytics
            analytics = self.generate_detailed_analytics(user_data)
            
            # Create visualization data for charts
            visualizations = {
                "monthly_spending_chart": {
                    "type": "line",
                    "data": analytics.get("spending_by_month", {}),
                    "title": "Monthly Spending Trends"
                },
                "monthly_income_chart": {
                    "type": "line", 
                    "data": analytics.get("income_by_month", {}),
                    "title": "Monthly Income Trends"
                },
                "category_pie_chart": {
                    "type": "pie",
                    "data": analytics.get("transaction_categories", {}),
                    "title": "Spending by Category"
                },
                "income_vs_expense_chart": {
                    "type": "bar",
                    "data": {
                        "Income": analytics.get("total_income", 0),
                        "Expenses": analytics.get("total_spending", 0),
                        "Net": analytics.get("net_change", 0)
                    },
                    "title": "Income vs Expenses Overview"
                },
                "financial_health_gauge": {
                    "type": "gauge",
                    "value": analytics.get("financial_health_score", 0),
                    "title": "Financial Health Score"
                }
            }
            
            # Generate comprehensive AI insights
            prompt = f"""
            You are a professional financial advisor AI for Bank of Anthos. 
            Analyze this comprehensive financial data and provide detailed, actionable insights.
            Be specific, encouraging, and provide concrete recommendations.
            
            FINANCIAL PROFILE:
            - Current Balance: ${analytics.get('current_balance', 0):.2f}
            - Total Income: ${analytics.get('total_income', 0):.2f}
            - Total Spending: ${analytics.get('total_spending', 0):.2f}
            - Net Change: ${analytics.get('net_change', 0):.2f}
            - Financial Health Score: {analytics.get('financial_health_score', 0)}/100
            - Total Transactions: {analytics.get('total_transactions', 0)}
            
            MONTHLY TRENDS:
            - Spending by Month: {analytics.get('spending_by_month', {})}
            - Income by Month: {analytics.get('income_by_month', {})}
            
            SPENDING CATEGORIES:
            {analytics.get('transaction_categories', {})}
            
            CONTACT ANALYSIS:
            {analytics.get('contact_analysis', {})}
            
            Please provide:
            1. **Financial Health Assessment** - Overall financial position analysis
            2. **Spending Analysis** - Detailed breakdown of spending patterns and categories
            3. **Income Trends** - Analysis of income stability and growth
            4. **Budget Recommendations** - Specific budgeting advice based on spending patterns
            5. **Savings Opportunities** - Concrete ways to save money and improve financial health
            6. **Goal Setting** - Suggested financial goals based on current position
            7. **Risk Assessment** - Any financial risks or concerns to address
            
            Format as a comprehensive but readable financial report. Use bullet points and clear sections.
            Be encouraging while being realistic about areas for improvement.
            """
            
            response = self.model.generate_content(prompt)
            insights_text = response.text
            
            return {
                "insights": insights_text,
                "analytics": analytics,
                "visualizations": visualizations,
                "summary": {
                    "balance": analytics.get('current_balance', 0),
                    "health_score": analytics.get('financial_health_score', 0),
                    "net_change": analytics.get('net_change', 0),
                    "top_category": max(analytics.get('transaction_categories', {}).items(), key=lambda x: x[1])[0] if analytics.get('transaction_categories') else "No data"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive insights: {e}")
            return {
                "insights": "I'm having trouble analyzing your financial data right now. Please try again later.",
                "analytics": {},
                "visualizations": {}
            }
    
    def chat_with_user(self, message: str, user_data: Dict[str, Any]) -> str:
        """Handle chat conversations with context"""
        if not self.model:
            return "AI chat is currently unavailable. Please check configuration."
        
        try:
            transactions = user_data.get('transactions', [])
            contacts = user_data.get('contacts', [])
            balance = user_data.get('balance', {}).get('balance', 0)
            
            # Create detailed context for AI
            transaction_details = ""
            if transactions:
                transaction_details = "\n".join([
                    f"- {tx.get('timestamp', 'Unknown')[:10]}: {tx.get('description', 'Unknown')} - ${tx.get('amount', '0')}"
                    for tx in transactions[:10]
                ])
            
            contacts_info = ""
            if contacts:
                contacts_info = "\n".join([
                    f"- {contact.get('label', 'Unknown')}: Account {contact.get('account_num', 'Unknown')}"
                    for contact in contacts
                ])
            
            # Calculate spending/income for current month
            import datetime
            current_month = datetime.datetime.now().strftime("%Y-%m")
            monthly_spent = 0
            monthly_received = 0
            
            for tx in transactions:
                if tx.get('timestamp', '').startswith(current_month):
                    amount_str = tx.get('amount', '0')
                    try:
                        amount = float(amount_str.replace('+', '').replace('-', ''))
                        if amount_str.startswith('-'):
                            monthly_spent += amount
                        else:
                            monthly_received += amount
                    except ValueError:
                        continue
            
            context = f"""
            You are a helpful banking AI assistant for Bank of Anthos. 
            The user has asked: "{message}"
            
            Current Account Information:
            - Balance: ${balance:.2f}
            - Total Transactions: {len(transactions)}
            - This Month's Spending: ${monthly_spent:.2f}
            - This Month's Income: ${monthly_received:.2f}
            
            Recent Transaction History (last 10):
            {transaction_details}
            
            User's Contacts:
            {contacts_info}
            
            Provide a helpful, accurate, and specific response to their question.
            Use the actual data provided above to answer questions about balances, transactions, spending, or contacts.
            If they ask about specific amounts, dates, or patterns, refer to the actual transaction data.
            Keep responses friendly and professional.
            If you need clarification, ask specific questions.
            """
            
            response = self.model.generate_content(context)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "I'm sorry, I'm having trouble understanding your request right now. Please try again."

# Initialize AI assistant
ai_assistant = BankingAIAssistant()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ai-assistant"})

@app.route('/ready')
def ready_check():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready", 
        "service": "ai-assistant",
        "gemini_configured": GEMINI_API_KEY is not None
    })

@app.route('/insights/<username>', methods=['GET'])
def get_financial_insights(username):
    """Get comprehensive AI-powered financial insights for a user"""
    # For development/demo: disable auth check
    # auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    # if not auth_token:
    #     abort(401, 'Authorization token required')
    
    try:
        # For demo: use dummy auth token
        auth_token = 'demo-token'
        user_data = ai_assistant.get_user_data(username, auth_token)
        insights_data = ai_assistant.generate_financial_insights(user_data)
        
        return jsonify({
            "username": username,
            "insights": insights_data.get("insights", ""),
            "analytics": insights_data.get("analytics", {}),
            "visualizations": insights_data.get("visualizations", {}),
            "summary": insights_data.get("summary", {}),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating insights for {username}: {e}")
        return jsonify({"error": "Failed to generate insights"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with AI assistant"""
    data = request.get_json()
    if not data or 'message' not in data or 'username' not in data:
        abort(400, 'Message and username required')
    
    # For development/demo: disable auth check
    # auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    # if not auth_token:
    #     abort(401, 'Authorization token required')
    
    try:
        username = data['username']
        message = data['message']
        
        # For demo: use dummy auth token
        auth_token = 'demo-token'
        user_data = ai_assistant.get_user_data(username, auth_token)
        response = ai_assistant.chat_with_user(message, user_data)
        
        return jsonify({
            "username": username,
            "user_message": message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"error": "Chat service temporarily unavailable"}), 500

@app.route('/spending-analysis/<username>', methods=['GET'])
def get_spending_analysis(username):
    """Get detailed spending analysis"""
    auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not auth_token:
        abort(401, 'Authorization token required')
    
    try:
        user_data = ai_assistant.get_user_data(username, auth_token)
        analysis = ai_assistant.analyze_spending_patterns(user_data.get('transactions', []))
        
        return jsonify({
            "username": username,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error analyzing spending for {username}: {e}")
        return jsonify({"error": "Failed to analyze spending"}), 500

if __name__ == '__main__':
    # Start the Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)