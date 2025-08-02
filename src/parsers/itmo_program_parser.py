# src/parsers/complete_itmo_parser.py

import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# PDF библиотеки
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PDF библиотеки не установлены. Установите: pip install PyPDF2 pdfplumber")

# === ПАРСИНГ ВЕБ-СТРАНИЦ ===

def parse_directions_data(text):
    """Парсинг данных направлений подготовки"""
    directions = []
    pattern = r'(\d{2}\.\d{2}\.\d{2})([А-Яа-яё\s]+?)(\d+)бюджетных(\d+)целевая(\d+)контрактных'
    
    matches = re.finditer(pattern, text)
    for match in matches:
        direction = {
            'code': match.group(1).strip(),
            'name': match.group(2).strip(),
            'budget_places': int(match.group(3)),
            'target_places': int(match.group(4)),
            'contract_places': int(match.group(5))
        }
        directions.append(direction)
    
    return directions

def parse_table_col_data(text):
    """Парсинг данных из Information_table__col__8wJDy"""
    patterns = [
        (r'форма обучения(.+)', 'форма обучения'),
        (r'длительность(.+)', 'длительность'),
        (r'язык обучения(.+)', 'язык обучения'),
        (r'стоимость контрактного обучения \(год\)(.+)', 'стоимость контрактного обучения (год)'),
        (r'общежитие(.+)', 'общежитие'),
        (r'военный учебный центр(.+)', 'военный учебный центр'),
        (r'гос\. аккредитация(.+)', 'гос. аккредитация'),
        (r'дополнительные возможности(.+)', 'дополнительные возможности')
    ]
    
    result = {}
    for pattern, key in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            result[key] = value
    
    return result

def extract_web_data(soup):
    """Извлечение данных с веб-страницы"""
    result = {
        'program_title': '',
        'directions': [],
        'basic_info': {},
        'manager_name': '',
        'manager_contacts': [],
        'social_links': [],
        'pdf_links': []
    }
    
    # Заголовок программы
    header_element = soup.find(class_='Information_information__header__fab3I')
    if header_element:
        result['program_title'] = header_element.get_text().strip()
    
    # Направления
    directions_text = ""
    for direction_element in soup.find_all(class_='Directions_directions__edkEZ'):
        directions_text += direction_element.get_text().strip()
    
    if directions_text:
        result['directions'] = parse_directions_data(directions_text)
    
    # Базовая информация
    for element in soup.find_all(class_='Information_table__col__8wJDy'):
        text = element.get_text().strip()
        parsed_data = parse_table_col_data(text)
        result['basic_info'].update(parsed_data)
    
    # Имя менеджера
    manager_name_element = soup.find(class_='Information_manager__name__ecPmn')
    if manager_name_element:
        result['manager_name'] = manager_name_element.get_text().strip()
    
    # Контакты менеджера
    for contact_element in soup.find_all(class_='Information_manager__contact__1fPAH'):
        contact_text = contact_element.get_text().strip()
        if contact_text:
            result['manager_contacts'].append(contact_text)
    
    # Социальные ссылки
    for social_element in soup.find_all(class_='Information_socials__link___eN3E'):
        social_data = {
            'text': social_element.get_text().strip(),
            'href': social_element.get('href', '') if social_element.name == 'a' else ''
        }
        
        if not social_data['href'] and social_element.find('a'):
            link = social_element.find('a')
            social_data['href'] = link.get('href', '')
        
        result['social_links'].append(social_data)
    
    # PDF ссылки
    for pdf_link in soup.find_all('a', href=lambda x: x and x.endswith('.pdf')):
        result['pdf_links'].append({
            'text': pdf_link.get_text().strip(),
            'href': pdf_link.get('href', '')
        })
    
    return result

# === ПАРСИНГ PDF ===

def extract_text_from_pdf(pdf_path):
    """Извлечение текста из PDF"""
    if not PDF_AVAILABLE:
        return ""
    
    text = ""
    
    # Пробуем pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except Exception as e:
        print(f"pdfplumber ошибка: {e}")
    
    # Пробуем PyPDF2
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"PyPDF2 ошибка: {e}")
    
    return text

def parse_curriculum_text(text):
    """Парсинг текста учебного плана"""
    # Название программы
    program_name = ""
    lines = text.split('\n')[:10]
    for line in lines:
        line = line.strip()
        if ('искусственный интеллект' in line.lower() or 
            'ии' in line.lower() and 'программа' in line.lower()):
            program_name = line
            break
    
    if not program_name:
        program_name = "Учебная программа"
    
    # Извлечение блоков учебного плана
    blocks = []
    
    # Паттерны для блоков
    block_patterns = [
        r'Блок\s+(\d+)\.?\s*([^\n]+)\s+(\d+)\s+(\d+)',
        r'(Обязательные дисциплины)[.\s]*(\d+)\s+(\d+)',
        r'(Пул выборных дисциплин)[.\s]*(\d+)\s+(\d+)',
        r'(Универсальная.*подготовка)\s+(\d+)\s+(\d+)',
        r'(Практика)\s+(\d+)\s+(\d+)',
        r'(ГИА)\s+(\d+)\s+(\d+)'
    ]
    
    for pattern in block_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            groups = match.groups()
            
            if len(groups) >= 3:
                if len(groups) == 4:
                    block_name = f"Блок {groups[0]}. {groups[1]}"
                    credits = int(groups[2])
                    hours = int(groups[3])
                else:
                    block_name = groups[0]
                    credits = int(groups[1])
                    hours = int(groups[2])
                
                # Извлекаем курсы для блока
                courses = extract_courses_for_block(text, match.end(), block_name)
                
                block = {
                    'name': block_name,
                    'total_credits': credits,
                    'total_hours': hours,
                    'courses': courses
                }
                blocks.append(block)
    
    # Если не нашли блоки, парсим все курсы
    if not blocks:
        all_courses = extract_courses_from_text(text)
        if all_courses:
            total_credits = sum(course.get('credits', 0) for course in all_courses)
            blocks.append({
                'name': 'Учебный план',
                'total_credits': total_credits,
                'total_hours': total_credits * 36,
                'courses': all_courses
            })
    
    return {
        'program_name': program_name,
        'blocks': blocks,
        'total_credits': sum(block['total_credits'] for block in blocks),
        'total_courses': sum(len(block['courses']) for block in blocks)
    }

def extract_courses_for_block(text, start_pos, block_name):
    """Извлечение курсов для блока"""
    block_text = text[start_pos:]
    
    # Ограничиваем область поиска следующим блоком
    next_block_patterns = [
        r'Блок\s+\d+',
        r'Универсальная.*подготовка',
        r'Обязательные дисциплины',
        r'Пул выборных дисциплин'
    ]
    
    end_pos = len(block_text)
    for pattern in next_block_patterns:
        match = re.search(pattern, block_text, re.IGNORECASE)
        if match and match.start() > 100:
            end_pos = match.start()
            break
    
    relevant_text = block_text[:end_pos]
    return extract_courses_from_text(relevant_text)

def extract_courses_from_text(text):
    """Извлечение курсов из текста"""
    courses = []
    
    # Паттерны для курсов
    course_patterns = [
        r'^(\d+)\s+([А-Яа-яёЁ\w\s\-\(\)/\.,]+?)\s+(\d+)\s+(\d+)$',
        r'^([А-Яа-яёЁ\w\s\-\(\)/\.,]{15,}?)\s+(\d+)\s+(\d+)$',
        r'^\d+\s+([А-Яа-яёЁ\w\s\-\(\)/\.,]+?)\s+(\d+)\s+\d+$'
    ]
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if len(line) < 10 or is_header_line(line):
            continue
        
        for pattern in course_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                course = parse_course_match(match, line)
                if course:
                    courses.append(course)
                    break
    
    return courses

def parse_course_match(match, original_line):
    """Парсинг совпадения курса"""
    groups = match.groups()
    
    try:
        if len(groups) == 4:
            semester = int(groups[0])
            name = groups[1].strip()
            credits = int(groups[2])
            hours = int(groups[3])
        elif len(groups) == 3:
            name = groups[0].strip()
            credits = int(groups[1])
            hours = int(groups[2])
            semester = None
        else:
            return None
        
        # Очищаем название
        name = clean_course_name(name)
        
        if len(name) < 5 or credits <= 0:
            return None
        
        return {
            'name': name,
            'credits': credits,
            'hours': hours,
            'semester': semester
        }
        
    except (ValueError, IndexError):
        return None

def clean_course_name(name):
    """Очистка названия курса"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r'^\d+\.?\s*', '', name)
    name = name.rstrip('/.').strip()
    return name

def is_header_line(line):
    """Проверка заголовочной строки"""
    header_patterns = [
        r'^Блок\s+\d+',
        r'^Семестр',
        r'^Наименование',
        r'^Трудоемкость',
        r'^\d+\s+\d+$',
        r'^Учебный план',
        r'^ОП\s+',
        r'^Пул выборных',
        r'^Обязательные'
    ]
    
    for pattern in header_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    
    return False

# === ОСНОВНОЙ ПАРСЕР ===

class CompleteITMOParser:
    """Полный парсер ИТМО с веб и PDF"""
    
    def __init__(self):
        # Определяем корневую директорию проекта
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent  # src/parsers -> src -> project_root
        
        self.pdf_dir = project_root / "data" / "pdf"
        self.output_dir = project_root / "data" / "parsed"
        
        # Создаем директории
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.programs = {
            'ai': 'https://abit.itmo.ru/program/master/ai',
            'ai_product': 'https://abit.itmo.ru/program/master/ai_product'
        }
    
    async def parse_program(self, program_id, url):
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
        web_data = await self.parse_web_page(url)
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
                    
                    curriculum_data = await self.parse_curriculum_pdf(pdf_url, program_id)
                    if curriculum_data:
                        result['curriculum_data'] = curriculum_data
                        print(f"✅ PDF данные: {curriculum_data['total_courses']} курсов")
                    break
        
        # 3. Проверка локальных PDF файлов
        if not result['curriculum_data']:
            local_pdf = self.find_local_pdf(program_id)
            if local_pdf:
                curriculum_data = self.parse_local_pdf(local_pdf)
                if curriculum_data:
                    result['curriculum_data'] = curriculum_data
                    print(f"✅ Локальный PDF: {curriculum_data['total_courses']} курсов")
        
        return result
    
    async def parse_web_page(self, url):
        """Парсинг веб-страницы"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        return extract_web_data(soup)
        except Exception as e:
            print(f"❌ Ошибка веб-парсинга: {e}")
        
        return None
    
    async def parse_curriculum_pdf(self, pdf_url, program_id):
        """Скачивание и парсинг PDF"""
        if not PDF_AVAILABLE:
            print("❌ PDF библиотеки недоступны")
            return None
        
        try:
            # Скачиваем PDF
            pdf_path = await self.download_pdf(pdf_url, program_id)
            if pdf_path:
                return self.parse_local_pdf(pdf_path)
        except Exception as e:
            print(f"❌ Ошибка PDF парсинга: {e}")
        
        return None
    
    async def download_pdf(self, pdf_url, program_id):
        """Скачивание PDF файла"""
        filename = f"{program_id}_curriculum.pdf"
        pdf_path = self.pdf_dir / filename
        
        if pdf_path.exists():
            print(f"📄 Используем существующий PDF: {pdf_path}")
            return pdf_path
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        with open(pdf_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        print(f"📥 PDF скачан: {pdf_path}")
                        return pdf_path
        except Exception as e:
            print(f"❌ Ошибка скачивания PDF: {e}")
        
        return None
    
    def find_local_pdf(self, program_id):
        """Поиск локального PDF файла"""
        patterns = [
            f"{program_id}_curriculum.pdf",
            f"{program_id}.pdf",
            f"curriculum_{program_id}.pdf"
        ]
        
        for pattern in patterns:
            pdf_path = self.pdf_dir / pattern
            if pdf_path.exists():
                return pdf_path
        
        # Поиск любых PDF в директории
        for pdf_file in self.pdf_dir.glob("*.pdf"):
            if program_id in pdf_file.name.lower():
                return pdf_file
        
        return None
    
    def parse_local_pdf(self, pdf_path):
        """Парсинг локального PDF файла"""
        if not PDF_AVAILABLE:
            return None
        
        try:
            text = extract_text_from_pdf(pdf_path)
            if text:
                return parse_curriculum_text(text)
        except Exception as e:
            print(f"❌ Ошибка парсинга PDF {pdf_path}: {e}")
        
        return None
    
    async def parse_all_programs(self):
        """Парсинг всех программ"""
        print("🚀 Запуск полного парсинга ИТМО")
        
        all_results = {}
        
        for program_id, url in self.programs.items():
            result = await self.parse_program(program_id, url)
            all_results[program_id] = result
            
            # Пауза между запросами
            await asyncio.sleep(2)
        
        # Сохраняем результаты
        await self.save_results(all_results)
        return all_results
    
    async def save_results(self, results):
        """Сохранение результатов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Полные данные
        full_filename = self.output_dir / f"itmo_complete_{timestamp}.json"
        with open(full_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Краткая сводка
        summary = self.create_summary(results)
        summary_filename = self.output_dir / f"itmo_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Создаем копии как "latest" версии (вместо symlink для Windows)
        latest_full = self.output_dir / "latest_complete.json"
        latest_summary = self.output_dir / "latest_summary.json"
        
        # Копируем файлы
        import shutil
        shutil.copy2(full_filename, latest_full)
        shutil.copy2(summary_filename, latest_summary)
        
        print(f"💾 Результаты сохранены:")
        print(f"   Полные данные: {full_filename}")
        print(f"   Сводка: {summary_filename}")
        print(f"   Последние версии: latest_complete.json, latest_summary.json")
    
    def create_summary(self, results):
        """Создание сводки результатов"""
        summary = {
            'parsed_at': datetime.now().isoformat(),
            'programs_count': len(results),
            'programs': {}
        }
        
        for program_id, data in results.items():
            program_summary = {
                'program_id': program_id,
                'url': data['url'],
                'has_web_data': data['web_data'] is not None,
                'has_curriculum': data['curriculum_data'] is not None
            }
            
            if data['web_data']:
                program_summary.update({
                    'title': data['web_data']['program_title'],
                    'directions_count': len(data['web_data']['directions']),
                    'pdf_links_count': len(data['web_data']['pdf_links'])
                })
            
            if data['curriculum_data']:
                program_summary.update({
                    'total_credits': data['curriculum_data']['total_credits'],
                    'total_courses': data['curriculum_data']['total_courses'],
                    'blocks_count': len(data['curriculum_data']['blocks'])
                })
            
            summary['programs'][program_id] = program_summary
        
        return summary

# === ЗАПУСК ===

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