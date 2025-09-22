// AI Assistant JavaScript with Enhanced Visualizations
// Copyright 2025 Google LLC

// AI Assistant functionality
let chatExpanded = true;
let isTyping = false;
let charts = {}; // Store chart instances

// Initialize AI features when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeAIFeatures();
    loadAIInsights();
});

function initializeAIFeatures() {
    // Set up chat input event listeners
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    if (chatInput) {
        // Send message on Enter key press
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Enable/disable send button based on input
        chatInput.addEventListener('input', function() {
            const hasText = this.value.trim().length > 0;
            sendButton.disabled = !hasText || isTyping;
        });
    }

    console.log('AI Assistant features initialized with enhanced visualizations');
}

// Load AI insights with enhanced visualization
async function loadAIInsights() {
    try {
        console.log('Loading enhanced AI insights...');
        showLoadingState();
        
        const response = await fetch('/api/ai/insights/{{ account_id }}');
        if (response.ok) {
            const data = await response.json();
            console.log('Enhanced insights loaded:', data);
            displayEnhancedInsights(data);
        } else {
            console.error('Failed to load insights:', response.status);
            showInsightsError('Failed to load AI insights. Please try again.');
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        showInsightsError('Error connecting to AI service. Please check your connection.');
    }
}

function displayEnhancedInsights(data) {
    // Hide loading state
    document.getElementById('ai-loading').style.display = 'none';
    
    // Show summary cards
    if (data.summary) {
        updateSummaryCards(data.summary);
        document.getElementById('financial-summary').style.display = 'block';
    }
    
    // Show charts if visualization data is available
    if (data.visualizations) {
        createFinancialCharts(data.visualizations);
        document.getElementById('financial-charts').style.display = 'block';
        document.getElementById('category-charts').style.display = 'block';
    }
    
    // Show AI insights text
    if (data.insights) {
        displayInsightsText(data.insights);
        document.getElementById('ai-insights-text').style.display = 'block';
    }
}

function updateSummaryCards(summary) {
    // Update balance
    const balanceElement = document.getElementById('summary-balance');
    if (balanceElement && summary.balance) {
        balanceElement.textContent = `$${summary.balance.toFixed(2)}`;
    }
    
    // Update health score
    const healthElement = document.getElementById('summary-health-score');
    if (healthElement && summary.health_score !== undefined) {
        healthElement.textContent = `${summary.health_score}/100`;
        
        // Update progress bar
        const progressElement = document.getElementById('health-progress');
        if (progressElement) {
            progressElement.style.width = `${summary.health_score}%`;
            progressElement.textContent = `${summary.health_score}%`;
            
            // Color code based on score
            if (summary.health_score >= 80) {
                progressElement.className = 'progress-bar bg-success';
            } else if (summary.health_score >= 60) {
                progressElement.className = 'progress-bar bg-warning';
            } else {
                progressElement.className = 'progress-bar bg-danger';
            }
        }
    }
    
    // Update net change
    const netElement = document.getElementById('summary-net-change');
    if (netElement && summary.net_change !== undefined) {
        const netChange = summary.net_change;
        netElement.textContent = `$${netChange.toFixed(2)}`;
        netElement.style.color = netChange >= 0 ? '#28a745' : '#dc3545';
    }
    
    // Update top category
    const categoryElement = document.getElementById('summary-top-category');
    if (categoryElement && summary.top_category) {
        categoryElement.textContent = summary.top_category;
    }
}

function createFinancialCharts(visualizations) {
    // Destroy existing charts
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};
    
    // Monthly Spending Chart
    if (visualizations.monthly_spending_chart) {
        createLineChart('monthly-spending-chart', visualizations.monthly_spending_chart);
    }
    
    // Income vs Expense Chart
    if (visualizations.income_vs_expense_chart) {
        createBarChart('income-expense-chart', visualizations.income_vs_expense_chart);
    }
    
    // Category Pie Chart
    if (visualizations.category_pie_chart) {
        createPieChart('category-pie-chart', visualizations.category_pie_chart);
    }
}

function createLineChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    const data = chartData.data || {};
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Amount ($)',
                data: values,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function createBarChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    const data = chartData.data || {};
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Amount ($)',
                data: values,
                backgroundColor: [
                    '#28a745', // Income - green
                    '#dc3545', // Expenses - red
                    '#007bff'  // Net - blue
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function createPieChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    const data = chartData.data || {};
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    charts[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#007bff',
                    '#28a745',
                    '#ffc107',
                    '#dc3545',
                    '#6c757d',
                    '#17a2b8',
                    '#fd7e14'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function displayInsightsText(insights) {
    const container = document.getElementById('ai-insights-content-text');
    if (container && insights) {
        // Format the insights text with better styling
        const formattedInsights = formatInsightsText(insights);
        container.innerHTML = formattedInsights;
    }
}

function formatInsightsText(text) {
    // Basic formatting for better readability
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
        .replace(/\n\n/g, '</p><p>') // Paragraphs
        .replace(/\n•/g, '<br>•') // Bullet points
        .replace(/\n-/g, '<br>-') // Dash points
        .replace(/\n(\d+\.)/g, '<br>$1') // Numbered lists
        .replace(/^/, '<p>') // Start paragraph
        .replace(/$/, '</p>'); // End paragraph
}

function showLoadingState() {
    document.getElementById('ai-loading').style.display = 'block';
    document.getElementById('financial-summary').style.display = 'none';
    document.getElementById('financial-charts').style.display = 'none';
    document.getElementById('category-charts').style.display = 'none';
    document.getElementById('ai-insights-text').style.display = 'none';
}

function showInsightsError(message) {
    document.getElementById('ai-loading').style.display = 'none';
    const container = document.getElementById('ai-insights-content-text');
    if (container) {
        container.innerHTML = `<div class="alert alert-warning">${message}</div>`;
        document.getElementById('ai-insights-text').style.display = 'block';
    }
}

// Refresh insights function
function refreshAIInsights() {
    console.log('Refreshing AI insights...');
    loadAIInsights();
}

// Toggle chat widget expanded/collapsed state
function toggleChat() {
    const chatBody = document.getElementById('chat-body');
    const chatToggle = document.getElementById('chat-toggle');
    
    if (chatExpanded) {
        chatBody.classList.add('collapsed');
        chatToggle.classList.add('rotated');
        chatToggle.textContent = 'expand_more';
    } else {
        chatBody.classList.remove('collapsed');
        chatToggle.classList.remove('rotated');
        chatToggle.textContent = 'expand_less';
    }
    
    chatExpanded = !chatExpanded;
}

// Send message to AI assistant
async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Clear input and disable send button
    chatInput.value = '';
    document.getElementById('send-button').disabled = true;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Get current user from the page context
        const username = getCurrentUsername();
        
        // Send message to AI assistant API
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include', // Include cookies for authentication
            body: JSON.stringify({
                message: message,
                username: username
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Remove typing indicator and add AI response
        hideTypingIndicator();
        addMessageToChat(data.ai_response || 'Sorry, I had trouble processing your request.', 'ai');
        
    } catch (error) {
        console.error('Error sending message to AI:', error);
        hideTypingIndicator();
        addMessageToChat('I\'m sorry, I\'m having trouble connecting right now. Please try again later.', 'ai', true);
    }
}

// Add message to chat interface
function addMessageToChat(message, sender, isError = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    if (sender === 'user') {
        messageDiv.className = 'user-message';
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(message)}</div>
        `;
    } else {
        messageDiv.className = 'ai-message';
        const iconColor = isError ? '#d93025' : '#4285f4';
        messageDiv.innerHTML = `
            <span class="material-icons" style="background: ${iconColor};">smart_toy</span>
            <div class="message-content ${isError ? 'ai-error' : ''}">${escapeHtml(message)}</div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    isTyping = true;
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <span class="material-icons">smart_toy</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide typing indicator
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    
    // Re-enable send button if there's text in input
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    if (chatInput && sendButton) {
        sendButton.disabled = chatInput.value.trim().length === 0;
    }
}

// Load AI insights
async function loadAIInsights() {
    const insightsContent = document.getElementById('ai-insights-content');
    
    try {
        const username = getCurrentUsername();
        
        const response = await fetch(`/api/ai/insights/${username}`, {
            method: 'GET',
            credentials: 'include' // Include cookies for authentication
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        insightsContent.innerHTML = `
            <div class="ai-insight-text">
                ${escapeHtml(data.insights || 'No insights available at this time.')}
            </div>
            <small class="text-muted">Last updated: ${formatTimestamp(data.timestamp)}</small>
        `;
        
    } catch (error) {
        console.error('Error loading AI insights:', error);
        insightsContent.innerHTML = `
            <div class="ai-error">
                <strong>Unable to load AI insights</strong><br>
                Our AI assistant is currently unavailable. Please try again later.
            </div>
        `;
    }
}

// Refresh AI insights
function refreshAIInsights() {
    const insightsContent = document.getElementById('ai-insights-content');
    insightsContent.innerHTML = `
        <div class="insights-loading">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Loading insights...</span>
            </div>
            <p class="mt-2">Analyzing your financial data...</p>
        </div>
    `;
    
    loadAIInsights();
}

// Helper functions
function getCurrentUsername() {
    // Try to get username from various possible sources
    const usernameElement = document.querySelector('[data-username]');
    if (usernameElement) {
        return usernameElement.getAttribute('data-username');
    }
    
    // Fallback: try to extract from account info or other page elements
    const accountInfo = document.querySelector('.account-number');
    if (accountInfo) {
        // This is a fallback - in real implementation, you'd get the actual username
        return 'testuser'; // Default for demo
    }
    
    return 'guest';
}

function getAuthToken() {
    // Try to get auth token from various sources
    const token = localStorage.getItem('auth_token') || 
                  sessionStorage.getItem('auth_token') ||
                  getCookie('auth_token');
    
    // For demo purposes, return a placeholder token
    return token || 'demo-token';
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (error) {
        return 'Unknown';
    }
}

// Global functions for testing
window.aiAssistant = {
    sendMessage,
    toggleChat,
    refreshAIInsights,
    loadAIInsights
};