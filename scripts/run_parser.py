# scripts/run_parser.py

"""
Скрипт для запуска полного парсера ИТМО
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.parsers.itmo_program_parser import CompleteITMOParser

async def main():
    """Главная функция"""
    print("🎓 Полный парсер ИТМО - веб + PDF")
    print("=" * 50)
    
    parser = CompleteITMOParser()
    results = await parser.parse_all_programs()
    
    print("\n✅ Парсинг завершен!")
    print(f"Обработано программ: {len(results)}")
    
    for program_id, data in results.items():
        web_status = "✅" if data['web_data'] else "❌"
        pdf_status = "✅" if data['curriculum_data'] else "❌"
        
        title = "Неизвестно"
        if data['web_data']:
            title = data['web_data']['program_title']
        
        print(f"  📚 {program_id}: {title}")
        print(f"     Веб: {web_status} | PDF: {pdf_status}")

if __name__ == '__main__':
    asyncio.run(main())