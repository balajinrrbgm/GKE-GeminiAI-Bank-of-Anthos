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
    
    def get_user_data(self, username: str, auth_token: str) -> Dict[str, Any]:
        """Fetch user data from various microservices"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        user_data = {'username': username}
        
        try:
            # Get balance
            balance_response = requests.get(
                f'{BALANCEREADER_URL}/balances/{username}',
                headers=headers,
                timeout=5
            )
            if balance_response.status_code == 200:
                user_data['balance'] = balance_response.json()
            else:
                # Fallback demo data
                user_data['balance'] = {"balance": 1250.75, "currency": "USD"}
            
            # Get transaction history
            transactions_response = requests.get(
                f'{TRANSACTIONHISTORY_URL}/transactions/{username}',
                headers=headers,
                timeout=5
            )
            if transactions_response.status_code == 200:
                user_data['transactions'] = transactions_response.json()
            else:
                # Fallback demo data
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
            else:
                # Fallback demo data
                user_data['contacts'] = [
                    {"label": "Alice Johnson", "account_num": "1234567890"},
                    {"label": "Bob Smith", "account_num": "0987654321"}
                ]
                
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
    
    def analyze_spending_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze user spending patterns"""
        if not transactions:
            return {"message": "No transactions found for analysis"}
        
        # Calculate spending by category, time periods, etc.
        total_spent = sum(float(t.get('amount', 0)) for t in transactions if float(t.get('amount', 0)) < 0)
        total_received = sum(float(t.get('amount', 0)) for t in transactions if float(t.get('amount', 0)) > 0)
        
        # Group by month
        monthly_spending = {}
        for transaction in transactions:
            if 'timestamp' in transaction:
                month = transaction['timestamp'][:7]  # YYYY-MM format
                amount = float(transaction.get('amount', 0))
                if amount < 0:  # Spending
                    monthly_spending[month] = monthly_spending.get(month, 0) + abs(amount)
        
        return {
            "total_spent": abs(total_spent),
            "total_received": total_received,
            "monthly_spending": monthly_spending,
            "transaction_count": len(transactions),
            "average_transaction": abs(total_spent) / len([t for t in transactions if float(t.get('amount', 0)) < 0]) if any(float(t.get('amount', 0)) < 0 for t in transactions) else 0
        }
    
    def generate_financial_insights(self, user_data: Dict[str, Any]) -> str:
        """Generate AI-powered financial insights"""
        if not self.model:
            return "AI insights are currently unavailable. Please check configuration."
        
        try:
            spending_analysis = self.analyze_spending_patterns(user_data.get('transactions', []))
            
            prompt = f"""
            You are a helpful financial advisor AI for Bank of Anthos. 
            Analyze this user's financial data and provide personalized insights and recommendations.
            Keep responses concise, helpful, and encouraging.
            
            User Financial Summary:
            - Current Balance: ${user_data.get('balance', {}).get('balance', 0)}
            - Total Spent: ${spending_analysis.get('total_spent', 0):.2f}
            - Total Received: ${spending_analysis.get('total_received', 0):.2f}
            - Number of Transactions: {spending_analysis.get('transaction_count', 0)}
            - Average Transaction: ${spending_analysis.get('average_transaction', 0):.2f}
            - Monthly Spending: {spending_analysis.get('monthly_spending', {})}
            
            Please provide:
            1. A brief financial health assessment
            2. 2-3 actionable recommendations
            3. Any patterns you notice in their spending
            
            Format as a friendly, professional response in 3-4 sentences.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return "I'm having trouble analyzing your financial data right now. Please try again later."
    
    def chat_with_user(self, message: str, user_data: Dict[str, Any]) -> str:
        """Handle chat conversations with context"""
        if not self.model:
            return "AI chat is currently unavailable. Please check configuration."
        
        try:
            context = f"""
            You are a helpful banking AI assistant for Bank of Anthos. 
            The user has:
            - Balance: ${user_data.get('balance', {}).get('balance', 0)}
            - {len(user_data.get('transactions', []))} recent transactions
            - {len(user_data.get('contacts', []))} contacts
            
            User question: {message}
            
            Provide a helpful, accurate response about their banking needs. 
            If they ask about specific transactions or balances, use the provided data.
            Keep responses concise and friendly.
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
    """Get AI-powered financial insights for a user"""
    # For development/demo: disable auth check
    # auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    # if not auth_token:
    #     abort(401, 'Authorization token required')
    
    try:
        # For demo: use dummy auth token
        auth_token = 'demo-token'
        user_data = ai_assistant.get_user_data(username, auth_token)
        insights = ai_assistant.generate_financial_insights(user_data)
        
        return jsonify({
            "username": username,
            "insights": insights,
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