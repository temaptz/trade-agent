#!/usr/bin/env python3
"""
Quick start script for Bitcoin trading agent
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ .env file not found. Please run setup.py first")
        return False
    
    # Check if requirements are installed
    try:
        import pandas, numpy, ccxt, langchain, langgraph
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    return True

async def run_demo():
    """Run the demo"""
    print("🚀 Running Bitcoin Trading Agent Demo")
    print("=" * 50)
    
    try:
        from demo import main as demo_main
        await demo_main()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

async def run_single_analysis():
    """Run single analysis"""
    print("🔍 Running Single Analysis")
    print("=" * 50)
    
    try:
        from main import main as main_func
        await main_func()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
    
    return True

async def run_continuous():
    """Run continuous trading"""
    print("🔄 Running Continuous Trading")
    print("=" * 50)
    
    try:
        from main import main as main_func
        # Override sys.argv to run continuous mode
        sys.argv = ["main.py", "continuous"]
        await main_func()
    except KeyboardInterrupt:
        print("\n⏹️  Continuous trading stopped by user")
    except Exception as e:
        print(f"❌ Continuous trading failed: {e}")
        return False
    
    return True

def show_menu():
    """Show menu options"""
    print("\n🤖 Bitcoin Trading Agent")
    print("=" * 30)
    print("1. Run Demo")
    print("2. Single Analysis")
    print("3. Continuous Trading")
    print("4. Check Requirements")
    print("5. Exit")
    print("=" * 30)

async def main():
    """Main function"""
    print("🚀 Bitcoin Trading Agent - Quick Start")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == "1":
                print("\n🎯 Running Demo...")
                await run_demo()
                
            elif choice == "2":
                print("\n🔍 Running Single Analysis...")
                await run_single_analysis()
                
            elif choice == "3":
                print("\n🔄 Starting Continuous Trading...")
                print("Press Ctrl+C to stop")
                await run_continuous()
                
            elif choice == "4":
                print("\n🔍 Checking Requirements...")
                if check_requirements():
                    print("✅ All requirements are met")
                else:
                    print("❌ Some requirements are missing")
                
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid option. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)