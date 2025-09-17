"""Setup verification script for the AI Trading Bot."""

import os
import sys
import subprocess
import importlib
from datetime import datetime

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_dependencies():
    """Check if all dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'langchain',
        'langgraph', 
        'langchain_ollama',
        'pybit',
        'yfinance',
        'duckduckgo_search',
        'ccxt',
        'ta',
        'pandas',
        'numpy',
        'loguru',
        'pydantic',
        'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_ollama():
    """Check if Ollama is running and model is available."""
    print("\n🦙 Checking Ollama...")
    
    try:
        # Check if ollama command exists
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ollama installed - OK")
        else:
            print("❌ Ollama not found - Install from https://ollama.ai/")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama not found - Install from https://ollama.ai/")
        return False
    
    try:
        # Check if model is available
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=10)
        if 'gemma2:9b' in result.stdout:
            print("✅ Gemma2 model - OK")
        else:
            print("⚠️  Gemma2 model not found - Run: ollama pull gemma2:9b")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Could not check models - Ollama might not be running")
        return False
    
    return True

def check_configuration():
    """Check configuration files."""
    print("\n⚙️  Checking configuration...")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file exists - OK")
        
        # Check if it's not the example file
        with open('.env', 'r') as f:
            content = f.read()
            if 'your_bybit_api_key_here' in content:
                print("⚠️  .env file contains example values - Please configure your API keys")
                return False
    else:
        print("❌ .env file not found - Copy .env.example to .env")
        return False
    
    # Check if logs directory exists
    if os.path.exists('logs'):
        print("✅ logs directory exists - OK")
    else:
        print("⚠️  logs directory not found - Will be created on first run")
    
    return True

def check_api_connectivity():
    """Check API connectivity (without actual trading)."""
    print("\n🌐 Checking API connectivity...")
    
    try:
        from market_tools import MarketDataProvider
        provider = MarketDataProvider()
        
        # Try to get current price (this should work even with dummy credentials)
        price = provider.get_current_price("BTCUSDT")
        if price:
            print(f"✅ Market data API - OK (BTC: ${price:,.2f})")
        else:
            print("⚠️  Market data API - Could not fetch price")
    except Exception as e:
        print(f"⚠️  Market data API - Error: {e}")
    
    return True

def check_file_structure():
    """Check if all required files exist."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'main.py',
        'trading_agent.py',
        'market_tools.py',
        'trading_manager.py',
        'config.py',
        'logger_config.py',
        'monitor.py',
        'utils.py',
        'test_bot.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - OK")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def run_quick_test():
    """Run a quick test of the bot components."""
    print("\n🧪 Running quick test...")
    
    try:
        # Test market analysis
        from market_tools import MarketAnalyzer
        analyzer = MarketAnalyzer()
        analysis = analyzer.get_comprehensive_analysis("BTCUSDT")
        
        if analysis and 'current_price' in analysis:
            print("✅ Market analysis - OK")
        else:
            print("⚠️  Market analysis - No data")
        
        # Test news analysis
        from market_tools import NewsAnalyzer
        news_analyzer = NewsAnalyzer()
        news = news_analyzer.search_crypto_news("bitcoin", 3)
        
        if news:
            print("✅ News analysis - OK")
        else:
            print("⚠️  News analysis - No data")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed - Error: {e}")
        return False

def main():
    """Main setup verification."""
    print("🤖 AI Trading Bot Setup Verification")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama", check_ollama),
        ("Configuration", check_configuration),
        ("File Structure", check_file_structure),
        ("API Connectivity", check_api_connectivity),
        ("Quick Test", run_quick_test)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} - Error: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Your trading bot is ready to use.")
        print("\nNext steps:")
        print("1. Configure your Bybit API keys in .env")
        print("2. Run tests: python test_bot.py")
        print("3. Start trading: python main.py single")
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Install Ollama: https://ollama.ai/")
        print("- Pull model: ollama pull gemma2:9b")
        print("- Configure .env file with your API keys")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)