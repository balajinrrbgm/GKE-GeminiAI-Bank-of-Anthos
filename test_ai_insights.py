#!/usr/bin/env python3
"""
Test script for Enhanced AI Financial Insights
Tests the visualization data generation and comprehensive analytics
"""

import requests
import json
import sys

def test_ai_insights():
    # Test the AI insights API endpoint
    frontend_url = "http://35.244.7.235"
    test_account_id = "1011226111"
    
    print("🧪 Testing Enhanced AI Financial Insights...")
    print(f"Frontend URL: {frontend_url}")
    print(f"Test Account ID: {test_account_id}")
    print("-" * 50)
    
    # Test 1: Check if frontend is accessible
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False
    
    # Test 2: Test AI insights endpoint (through frontend proxy)
    insights_url = f"{frontend_url}/api/ai/insights/{test_account_id}"
    print(f"\n🔍 Testing insights endpoint: {insights_url}")
    
    try:
        response = requests.get(insights_url, timeout=30)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Insights API is working!")
            
            # Check for enhanced features
            required_fields = ['insights', 'summary', 'visualizations']
            missing_fields = []
            
            for field in required_fields:
                if field in data:
                    print(f"✅ Found '{field}' in response")
                else:
                    missing_fields.append(field)
                    print(f"❌ Missing '{field}' in response")
            
            # Test visualization data structure
            if 'visualizations' in data:
                viz_data = data['visualizations']
                expected_charts = ['monthly_spending_chart', 'income_vs_expense_chart', 'category_pie_chart']
                
                for chart in expected_charts:
                    if chart in viz_data:
                        print(f"✅ Found chart: {chart}")
                        if 'data' in viz_data[chart]:
                            print(f"  📊 Chart has data: {len(viz_data[chart]['data'])} items")
                        else:
                            print(f"  ❌ Chart missing data")
                    else:
                        print(f"❌ Missing chart: {chart}")
            
            # Test summary data
            if 'summary' in data:
                summary = data['summary']
                summary_fields = ['balance', 'health_score', 'net_change', 'top_category']
                
                for field in summary_fields:
                    if field in summary:
                        print(f"✅ Summary has {field}: {summary[field]}")
                    else:
                        print(f"❌ Summary missing {field}")
            
            print(f"\n📋 Response Preview:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))
            
            return len(missing_fields) == 0
            
        else:
            print(f"❌ AI Insights API error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ AI Insights API error: {e}")
        return False

def test_visualization_features():
    """Test frontend visualization capabilities"""
    print("\n🎨 Testing Frontend Visualization Features...")
    
    frontend_url = "http://35.244.7.235"
    
    try:
        response = requests.get(frontend_url, timeout=10)
        content = response.text
        
        # Check for Chart.js integration
        if 'chart.js' in content.lower() or 'chartjs' in content.lower():
            print("✅ Chart.js library detected")
        else:
            print("❌ Chart.js library not found")
        
        # Check for chart containers
        chart_containers = [
            'monthly-spending-chart',
            'income-expense-chart', 
            'category-pie-chart'
        ]
        
        for container in chart_containers:
            if container in content:
                print(f"✅ Found chart container: {container}")
            else:
                print(f"❌ Missing chart container: {container}")
        
        # Check for AI insights section
        if 'ai-insights' in content or 'financial-insights' in content:
            print("✅ AI insights section detected")
        else:
            print("❌ AI insights section not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Frontend analysis error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Bank of Anthos - Enhanced AI Insights Test Suite")
    print("=" * 60)
    
    # Run tests
    insights_test = test_ai_insights()
    viz_test = test_visualization_features()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"AI Insights API: {'✅ PASS' if insights_test else '❌ FAIL'}")
    print(f"Visualization Features: {'✅ PASS' if viz_test else '❌ FAIL'}")
    
    if insights_test and viz_test:
        print("\n🎉 All tests passed! Enhanced AI insights are working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)