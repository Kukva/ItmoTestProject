
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.parsers.web_parser import parse_web_page
from src.parsers.pdf_manager import PDFManager
from src.parsers.data_manager import DataManager

class ITMOParser:
    """Основной класс парсера ИТМО"""
    
    def __init__(self):
        # Определяем корневую директорию проекта
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent
        
        self.data_manager = DataManager(project_root)
        self.pdf_manager = PDFManager(self.data_manager.pdf_dir)
        
        self.programs = {
            'ai': 'https://abit.itmo.ru/program/master/ai',
            'ai_product': 'https://abit.itmo.ru/program/master/ai_product'
        }
    
    async def parse_program(self, program_id: str, url: str) -> dict:
        """Парсинг одной программы"""
        print(f"🔍 Парсинг программы: {program_id}")
        
        result = {
            'program_id': program_id,
            'url': url,
            'parsed_at': datetime.now().isoformat(),
            'web_data': None,
            'curriculum_data': None
        }
        
        # 1. Парсинг веб-страницы
        web_data = await parse_web_page(url)
        if web_data:
            result['web_data'] = web_data
            print(f"✅ Веб-данные: {web_data['program_title']}")
        
        # 2. Скачивание и парсинг PDF
        if web_data and web_data['pdf_links']:
            for pdf_link in web_data['pdf_links']:
                if 'учебный план' in pdf_link['text'].lower():
                    pdf_url = pdf_link['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = 'https://abit.itmo.ru' + pdf_url
                    
                    curriculum_data = await self._parse_curriculum_pdf(pdf_url, program_id)
                    if curriculum_data:
                        result['curriculum_data'] = curriculum_data
                        print(f"✅ PDF данные: {curriculum_data['total_courses']} курсов")
                    break
        
        # 3. Проверка локальных PDF файлов
        if not result['curriculum_data']:
            local_pdf = self.pdf_manager.find_local_pdf(program_id)
            if local_pdf:
                curriculum_data = self.pdf_manager.parse_local_pdf(local_pdf)
                if curriculum_data:
                    result['curriculum_data'] = curriculum_data
                    print(f"✅ Локальный PDF: {curriculum_data['total_courses']} курсов")
        
        return result
    
    async def _parse_curriculum_pdf(self, pdf_url: str, program_id: str) -> dict:
        """Скачивание и парсинг PDF"""
        try:
            # Скачиваем PDF
            pdf_path = await self.pdf_manager.download_pdf(pdf_url, program_id)
            if pdf_path:
                return self.pdf_manager.parse_local_pdf(pdf_path)
        except Exception as e:
            print(f"❌ Ошибка PDF парсинга: {e}")
        
        return None
    
    async def parse_all_programs(self) -> dict:
        """Парсинг всех программ"""
        print("🚀 Запуск парсинга всех программ ИТМО")
        print("=" * 50)
        
        all_results = {}
        
        for program_id, url in self.programs.items():
            result = await self.parse_program(program_id, url)
            all_results[program_id] = result
            
            # Пауза между запросами
            await asyncio.sleep(2)
        
        # Сохраняем результаты
        self.data_manager.save_results(all_results)
        return all_results
    
    def print_summary(self, results: dict):
        """Вывод сводки результатов"""
        print("\n✅ Парсинг завершен!")
        print(f"Обработано программ: {len(results)}")
        
        for program_id, data in results.items():
            web_status = "✅" if data['web_data'] else "❌"
            pdf_status = "✅" if data['curriculum_data'] else "❌"
            
            title = "Неизвестно"
            courses_count = 0
            
            if data['web_data']:
                title = data['web_data']['program_title']
            
            if data['curriculum_data']:
                courses_count = data['curriculum_data']['total_courses']
            
            print(f"\n📚 {program_id}: {title}")
            print(f"   Веб-данные: {web_status}")
            print(f"   PDF-данные: {pdf_status}")
            if courses_count > 0:
                print(f"   Курсов: {courses_count}")

async def main():
    """Главная функция"""
    print("🎓Парсер ИТМО")
    print("=" * 50)
    
    parser = ITMOParser()
    
    try:
        results = await parser.parse_all_programs()
        parser.print_summary(results)
        
    except KeyboardInterrupt:
        print("\n🛑 Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())