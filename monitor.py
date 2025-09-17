#!/usr/bin/env python3
"""
Мониторинг торгового робота
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

from config import Config
from trading_agent import TradingAgent
from bybit_client import BybitClient

logger = logging.getLogger(__name__)

class TradingMonitor:
    """Мониторинг торгового робота"""
    
    def __init__(self, config: Config):
        self.config = config
        self.agent = None
        self.bybit_client = None
        self.log_file = Path("trading_bot.log")
        self.stats_file = Path("trading_stats.json")
        self.stats = self._load_stats()
        
    def _load_stats(self) -> Dict[str, Any]:
        """Загружает статистику из файла"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки статистики: {e}")
        
        return {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0,
            "last_analysis": None,
            "last_trade": None,
            "errors": []
        }
    
    def _save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")
    
    def initialize(self):
        """Инициализирует мониторинг"""
        try:
            if not self.agent:
                self.agent = TradingAgent(self.config)
            if not self.bybit_client:
                self.bybit_client = BybitClient(self.config)
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации мониторинга: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получает статус системы"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "ollama_status": self._check_ollama(),
                "bybit_status": self._check_bybit(),
                "balance": self._get_balance(),
                "recent_errors": self._get_recent_errors(),
                "last_analysis": self.stats.get("last_analysis"),
                "trading_stats": {
                    "total_trades": self.stats.get("total_trades", 0),
                    "successful_trades": self.stats.get("successful_trades", 0),
                    "success_rate": self._calculate_success_rate(),
                    "total_profit": self.stats.get("total_profit", 0.0)
                }
            }
            return status
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {"error": str(e)}
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Проверяет статус Ollama"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    "status": "online",
                    "models": [model['name'] for model in models],
                    "gemma_available": any('gemma' in model['name'].lower() for model in models)
                }
            else:
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def _check_bybit(self) -> Dict[str, Any]:
        """Проверяет статус Bybit"""
        try:
            if not self.bybit_client:
                return {"status": "not_initialized"}
            
            balance = self.bybit_client.get_account_balance()
            return {
                "status": "online",
                "balance_btc": balance.get('btc_balance', 0),
                "balance_usdt": balance.get('usdt_balance', 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_balance(self) -> Dict[str, Any]:
        """Получает текущий баланс"""
        try:
            if not self.bybit_client:
                return {}
            
            balance = self.bybit_client.get_account_balance()
            return {
                "btc": balance.get('btc_balance', 0),
                "usdt": balance.get('usdt_balance', 0),
                "total_usdt": balance.get('total', {}).get('USDT', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {}
    
    def _get_recent_errors(self) -> List[Dict[str, Any]]:
        """Получает последние ошибки из логов"""
        try:
            if not self.log_file.exists():
                return []
            
            errors = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Ищем ошибки за последние 24 часа
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for line in lines[-1000:]:  # Проверяем последние 1000 строк
                if "ERROR" in line:
                    try:
                        # Парсим время из лога
                        time_str = line.split(' - ')[0]
                        log_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if log_time > cutoff_time:
                            errors.append({
                                "time": time_str,
                                "message": line.strip()
                            })
                    except:
                        # Если не удается распарсить время, добавляем как есть
                        errors.append({
                            "time": "unknown",
                            "message": line.strip()
                        })
            
            return errors[-10:]  # Последние 10 ошибок
            
        except Exception as e:
            logger.error(f"Ошибка чтения логов: {e}")
            return []
    
    def _calculate_success_rate(self) -> float:
        """Вычисляет процент успешных сделок"""
        total = self.stats.get("total_trades", 0)
        successful = self.stats.get("successful_trades", 0)
        
        if total == 0:
            return 0.0
        
        return (successful / total) * 100
    
    def run_analysis_and_monitor(self) -> Dict[str, Any]:
        """Запускает анализ и обновляет статистику"""
        try:
            logger.info("Запуск анализа с мониторингом...")
            
            # Запускаем анализ
            result = self.agent.run_analysis()
            
            # Обновляем статистику
            self.stats["last_analysis"] = datetime.now().isoformat()
            
            if result.get("action"):
                self.stats["total_trades"] += 1
                
                action = result["action"]
                if action.get("status") == "executed":
                    self.stats["successful_trades"] += 1
                    logger.info("✅ Торговая операция выполнена успешно")
                else:
                    self.stats["failed_trades"] += 1
                    logger.warning(f"⚠️ Торговая операция не выполнена: {action.get('status')}")
            
            # Сохраняем статистику
            self._save_stats()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа с мониторингом: {e}")
            self.stats["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e)
            })
            self._save_stats()
            return {"error": str(e)}
    
    def generate_report(self) -> str:
        """Генерирует отчет о работе робота"""
        try:
            status = self.get_system_status()
            
            report = f"""
🤖 ОТЧЕТ О РАБОТЕ ТОРГОВОГО РОБОТА
{'='*50}
Время отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 СТАТУС СИСТЕМЫ:
• Ollama: {status.get('ollama_status', {}).get('status', 'unknown')}
• Bybit: {status.get('bybit_status', {}).get('status', 'unknown')}

💰 БАЛАНС:
• BTC: {status.get('balance', {}).get('btc', 0):.8f}
• USDT: {status.get('balance', {}).get('usdt', 0):.2f}

📈 ТОРГОВАЯ СТАТИСТИКА:
• Всего сделок: {status.get('trading_stats', {}).get('total_trades', 0)}
• Успешных: {status.get('trading_stats', {}).get('successful_trades', 0)}
• Процент успеха: {status.get('trading_stats', {}).get('success_rate', 0):.1f}%
• Общая прибыль: {status.get('trading_stats', {}).get('total_profit', 0):.2f} USDT

🕐 ПОСЛЕДНИЙ АНАЛИЗ:
{status.get('last_analysis', 'Никогда')}

❌ ПОСЛЕДНИЕ ОШИБКИ:
"""
            
            recent_errors = status.get('recent_errors', [])
            if recent_errors:
                for error in recent_errors[-3:]:  # Последние 3 ошибки
                    report += f"• {error.get('time', 'unknown')}: {error.get('message', 'unknown')}\n"
            else:
                report += "• Ошибок не обнаружено\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return f"Ошибка генерации отчета: {e}"

def main():
    """Основная функция мониторинга"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Мониторинг торгового робота")
    parser.add_argument("--status", action="store_true", help="Показать статус системы")
    parser.add_argument("--report", action="store_true", help="Сгенерировать отчет")
    parser.add_argument("--analyze", action="store_true", help="Запустить анализ")
    parser.add_argument("--monitor", type=int, help="Запустить мониторинг на N минут")
    
    args = parser.parse_args()
    
    # Инициализация
    config = Config()
    monitor = TradingMonitor(config)
    
    if not monitor.initialize():
        print("❌ Ошибка инициализации мониторинга")
        return 1
    
    if args.status:
        status = monitor.get_system_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.report:
        report = monitor.generate_report()
        print(report)
    
    elif args.analyze:
        result = monitor.run_analysis_and_monitor()
        print(f"Результат анализа: {result}")
    
    elif args.monitor:
        print(f"🔄 Запуск мониторинга на {args.monitor} минут...")
        start_time = time.time()
        
        while time.time() - start_time < args.monitor * 60:
            try:
                result = monitor.run_analysis_and_monitor()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Анализ завершен: {result.get('decision', 'N/A')}")
                
                # Ждем 5 минут до следующего анализа
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\n👋 Мониторинг прерван пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка мониторинга: {e}")
                time.sleep(60)  # Ждем минуту при ошибке
    
    else:
        print("Используйте --help для просмотра доступных опций")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())