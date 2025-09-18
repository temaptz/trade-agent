#!/usr/bin/env python3
"""
CLI для отрисовки графа LangGraph агента в Mermaid и PNG (опционально).
"""
import argparse
import subprocess
import sys
from pathlib import Path
from loguru import logger

# Локальные импорты
from trading_agent import TradingAgent

def write_file(path: Path, content: str):
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "w", encoding="utf-8") as f:
		f.write(content)


def try_render_png(mmd_path: Path, png_path: Path) -> bool:
	"""Пытается отрисовать PNG через mermaid-cli (mmdc)."""
	try:
		result = subprocess.run(["mmdc", "-i", str(mmd_path), "-o", str(png_path)], capture_output=True, text=True)
		if result.returncode == 0:
			logger.info(f"PNG сохранен: {png_path}")
			return True
		else:
			logger.warning("Не удалось сгенерировать PNG. Установите mermaid-cli (mmdc)")
			if result.stderr:
				logger.debug(result.stderr)
			return False
	except FileNotFoundError:
		logger.warning("Команда 'mmdc' не найдена. Установите mermaid-cli: npm i -g @mermaid-js/mermaid-cli")
		return False
	except Exception as e:
		logger.error(f"Ошибка генерации PNG: {e}")
		return False


def main():
	parser = argparse.ArgumentParser(description="Рендер графа агента в Mermaid/PNG")
	parser.add_argument("--out", default="agent_graph", help="Базовое имя выходных файлов (без расширения)")
	args = parser.parse_args()

	out_base = Path(args.out)
	mmd_path = out_base.with_suffix(".mmd")
	md_path = out_base.with_suffix(".md")
	png_path = out_base.with_suffix(".png")

	# Генерация Mermaid
	agent = TradingAgent()
	mermaid = agent.get_graph_mermaid()

	write_file(mmd_path, mermaid)
	logger.info(f"Mermaid сохранен: {mmd_path}")

	# Обертка в Markdown для предпросмотра
	md_content = f"""# Граф агента (Mermaid)

```mermaid
{mermaid}
```
"""
	write_file(md_path, md_content)
	logger.info(f"Markdown сохранен: {md_path}")

	# Попытка сгенерировать PNG
	try_render_png(mmd_path, png_path)

if __name__ == "__main__":
	# Настройка логирования
	logger.remove()
	logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
	main()