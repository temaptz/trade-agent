"""
Клиент для работы с Ollama и моделью Gemma3
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from config import settings

class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_response(self, prompt: str, system_prompt: str = None, 
                              temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Генерация ответа от модели"""
        try:
            if not self.session:
                raise Exception("Session not initialized")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    logger.error(f"Ошибка API Ollama: {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return ""
    
    async def analyze_market_data(self, market_analysis: Dict, news_sentiment: Dict) -> Dict:
        """Анализ рыночных данных с помощью ИИ"""
        try:
            # Подготовка данных для анализа
            market_summary = self._prepare_market_summary(market_analysis)
            news_summary = self._prepare_news_summary(news_sentiment)
            
            system_prompt = """Ты - эксперт по анализу криптовалютных рынков с 20-летним опытом. 
            Анализируй предоставленные данные и давай рекомендации по торговле биткойном.
            Учитывай технические индикаторы, тренды, волатильность, объемы и новостной фон.
            Будь осторожен с рисками и всегда учитывай управление капиталом."""
            
            prompt = f"""
            Проанализируй следующие данные о рынке биткойна:
            
            РЫНОЧНЫЕ ДАННЫЕ:
            {market_summary}
            
            НОВОСТНОЙ ФОН:
            {news_summary}
            
            Дай анализ и рекомендацию:
            1. Общая оценка рынка (1-10)
            2. Торговая рекомендация (BUY/SELL/HOLD)
            3. Уровень уверенности (1-10)
            4. Ключевые факторы
            5. Риски
            6. Целевые уровни (если есть)
            
            Ответь структурированно и кратко.
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.3)
            
            # Парсинг ответа
            analysis = self._parse_ai_response(response)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "ai_analysis": analysis,
                "raw_response": response,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа данных ИИ: {e}")
            return {"error": str(e)}
    
    def _prepare_market_summary(self, market_analysis: Dict) -> str:
        """Подготовка сводки рыночных данных"""
        try:
            summary = []
            
            if "current_price" in market_analysis:
                summary.append(f"Текущая цена: ${market_analysis['current_price']:.2f}")
            
            if "trend" in market_analysis:
                trend = market_analysis["trend"]
                summary.append(f"Тренд: {trend.get('trend', 'unknown')} (сила: {trend.get('strength', 0):.2f})")
            
            if "volatility" in market_analysis:
                vol = market_analysis["volatility"]
                summary.append(f"Волатильность: {vol.get('volatility', 'unknown')} ({vol.get('atr_percent', 0):.2f}%)")
            
            if "volume" in market_analysis:
                vol_data = market_analysis["volume"]
                summary.append(f"Объем: {vol_data.get('volume_trend', 'unknown')} (коэффициент: {vol_data.get('volume_ratio', 1):.2f})")
            
            if "indicators" in market_analysis:
                indicators = market_analysis["indicators"]
                key_indicators = []
                
                if "rsi" in indicators:
                    key_indicators.append(f"RSI: {indicators['rsi']:.2f}")
                if "macd" in indicators:
                    key_indicators.append(f"MACD: {indicators['macd']:.4f}")
                if "sma_20" in indicators:
                    key_indicators.append(f"SMA20: {indicators['sma_20']:.2f}")
                
                if key_indicators:
                    summary.append(f"Индикаторы: {', '.join(key_indicators)}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Ошибка подготовки сводки рынка: {e}")
            return "Данные недоступны"
    
    def _prepare_news_summary(self, news_sentiment: Dict) -> str:
        """Подготовка сводки новостей"""
        try:
            summary = []
            
            if "sentiment" in news_sentiment:
                sentiment = news_sentiment["sentiment"]
                confidence = news_sentiment.get("confidence", 0)
                summary.append(f"Настроение рынка: {sentiment} (уверенность: {confidence:.2f})")
            
            if "news_count" in news_sentiment:
                summary.append(f"Проанализировано новостей: {news_sentiment['news_count']}")
            
            if "distribution" in news_sentiment:
                dist = news_sentiment["distribution"]
                summary.append(f"Распределение тональности: Положительные {dist.get('positive', 0):.2f}, "
                              f"Отрицательные {dist.get('negative', 0):.2f}, "
                              f"Нейтральные {dist.get('neutral', 0):.2f}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Ошибка подготовки сводки новостей: {e}")
            return "Новости недоступны"
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Парсинг ответа ИИ"""
        try:
            analysis = {
                "market_score": 5,
                "recommendation": "HOLD",
                "confidence": 5,
                "key_factors": [],
                "risks": [],
                "target_levels": []
            }
            
            # Простой парсинг ключевых слов
            response_lower = response.lower()
            
            # Поиск оценки рынка
            if "оценка" in response_lower or "score" in response_lower:
                import re
                score_match = re.search(r'(\d+)', response)
                if score_match:
                    analysis["market_score"] = int(score_match.group(1))
            
            # Поиск рекомендации
            if "buy" in response_lower or "покупка" in response_lower:
                analysis["recommendation"] = "BUY"
            elif "sell" in response_lower or "продажа" in response_lower:
                analysis["recommendation"] = "SELL"
            else:
                analysis["recommendation"] = "HOLD"
            
            # Поиск уверенности
            if "уверенность" in response_lower or "confidence" in response_lower:
                conf_match = re.search(r'уверенность[:\s]*(\d+)', response_lower)
                if conf_match:
                    analysis["confidence"] = int(conf_match.group(1))
            
            # Извлечение ключевых факторов
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['фактор', 'factor', 'важно', 'important']):
                    analysis["key_factors"].append(line)
            
            # Извлечение рисков
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['риск', 'risk', 'опасность', 'danger']):
                    analysis["risks"].append(line)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа ИИ: {e}")
            return {"error": "Failed to parse AI response"}
    
    async def generate_trading_plan(self, market_analysis: Dict, news_sentiment: Dict, 
                                  current_positions: List[Dict]) -> Dict:
        """Генерация торгового плана"""
        try:
            system_prompt = """Ты - профессиональный трейдер с 20-летним опытом. 
            Создавай детальные торговые планы с учетом управления рисками, 
            технического анализа и фундаментальных факторов."""
            
            positions_summary = self._prepare_positions_summary(current_positions)
            
            prompt = f"""
            Создай торговый план на основе следующих данных:
            
            РЫНОЧНЫЙ АНАЛИЗ:
            {self._prepare_market_summary(market_analysis)}
            
            НОВОСТНОЙ ФОН:
            {self._prepare_news_summary(news_sentiment)}
            
            ТЕКУЩИЕ ПОЗИЦИИ:
            {positions_summary}
            
            Создай план включающий:
            1. Торговую стратегию
            2. Точки входа и выхода
            3. Управление рисками
            4. Размер позиции
            5. Стоп-лосс и тейк-профит
            6. Временные рамки
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.4)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "trading_plan": response,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации торгового плана: {e}")
            return {"error": str(e)}
    
    def _prepare_positions_summary(self, positions: List[Dict]) -> str:
        """Подготовка сводки позиций"""
        try:
            if not positions:
                return "Нет открытых позиций"
            
            summary = []
            for pos in positions:
                summary.append(f"Позиция: {pos.get('side', 'unknown')} "
                              f"Размер: {pos.get('size', 0)} "
                              f"Цена: {pos.get('avgPrice', 0)} "
                              f"PnL: {pos.get('unrealisedPnl', 0)}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Ошибка подготовки сводки позиций: {e}")
            return "Позиции недоступны"
    
    async def analyze_risk(self, market_analysis: Dict, current_positions: List[Dict]) -> Dict:
        """Анализ рисков"""
        try:
            system_prompt = """Ты - риск-менеджер с экспертизой в криптовалютных рынках. 
            Анализируй риски и давай рекомендации по их минимизации."""
            
            risk_data = self._prepare_risk_data(market_analysis, current_positions)
            
            prompt = f"""
            Проанализируй риски на основе данных:
            
            {risk_data}
            
            Оцени:
            1. Общий уровень риска (1-10)
            2. Основные источники риска
            3. Рекомендации по управлению рисками
            4. Максимальный размер позиции
            5. Уровни стоп-лосса
            """
            
            response = await self.generate_response(prompt, system_prompt, temperature=0.2)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "risk_analysis": response,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа рисков: {e}")
            return {"error": str(e)}
    
    def _prepare_risk_data(self, market_analysis: Dict, positions: List[Dict]) -> str:
        """Подготовка данных для анализа рисков"""
        try:
            risk_data = []
            
            # Данные о волатильности
            if "volatility" in market_analysis:
                vol = market_analysis["volatility"]
                risk_data.append(f"Волатильность: {vol.get('volatility', 'unknown')} "
                               f"({vol.get('atr_percent', 0):.2f}%)")
            
            # Данные о рисках
            if "risk_metrics" in market_analysis:
                risk_metrics = market_analysis["risk_metrics"]
                risk_data.append(f"VaR 95%: {risk_metrics.get('var_95', 0):.4f}")
                risk_data.append(f"Максимальная просадка: {risk_metrics.get('max_drawdown', 0):.4f}")
                risk_data.append(f"Коэффициент Шарпа: {risk_metrics.get('sharpe_ratio', 0):.4f}")
            
            # Данные о позициях
            if positions:
                total_exposure = sum(float(pos.get('size', 0)) for pos in positions)
                risk_data.append(f"Общая экспозиция: {total_exposure}")
            else:
                risk_data.append("Нет открытых позиций")
            
            return "\n".join(risk_data)
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных рисков: {e}")
            return "Данные недоступны"