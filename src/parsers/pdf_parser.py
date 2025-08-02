import re
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def extract_text_from_pdf(pdf_path: Path) -> str:
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
    except Exception:
        pass
    
    # Пробуем PyPDF2
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    
    return text

def parse_curriculum_text(text: str) -> Dict:
    """Основная функция парсинга учебного плана"""
    # Название программы
    program_name = extract_program_name(text)
    
    # Парсим главные блоки
    blocks = parse_main_blocks(text)
    
    # Считаем статистику
    total_credits = sum(block.get('total_credits', 0) for block in blocks)
    total_courses = sum(count_courses_in_block(block) for block in blocks)
    
    return {
        'program_name': program_name,
        'blocks': blocks,
        'total_credits': total_credits,
        'total_courses': total_courses
    }

def extract_program_name(text: str) -> str:
    """Извлечение названия программы"""
    lines = text.split('\n')[:10]
    
    for line in lines:
        line = line.strip()
        if 'искусственный интеллект' in line.lower():
            return line
    
    return "Учебная программа"

def parse_main_blocks(text: str) -> List[Dict]:
    """Парсинг основных блоков"""
    blocks = []
    
    # Ищем блоки типа "Блок 1. Название"
    block_pattern = r'Блок\s+(\d+)\.\s*([^\n]+?)\s+(\d+)\s+(\d+)'
    matches = list(re.finditer(block_pattern, text, re.IGNORECASE))
    
    for i, match in enumerate(matches):
        block_num = int(match.group(1))
        block_title = match.group(2).strip()
        block_credits = int(match.group(3))
        block_hours = int(match.group(4))
        
        # Определяем границы блока
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[start_pos:end_pos]
        
        # Парсим содержимое блока
        if block_num == 1:  # Дисциплины
            sub_blocks = parse_disciplines_block(block_text)
        elif block_num == 2:  # Практика
            sub_blocks = parse_practice_block(block_text)
        else:  # Другие блоки
            sub_blocks = parse_other_block(block_text)
        
        blocks.append({
            'name': f"Блок {block_num}. {block_title}",
            'block_number': block_num,
            'total_credits': block_credits,
            'total_hours': block_hours,
            'sub_blocks': sub_blocks
        })
    
    # Универсальная подготовка
    universal_block = parse_universal_block(text)
    if universal_block:
        blocks.append(universal_block)
    
    return blocks

def parse_disciplines_block(text: str) -> List[Dict]:
    """Парсинг блока дисциплин"""
    sub_blocks = []
    
    # Ищем подблоки дисциплин
    patterns = [
        r'(Обязательные дисциплины)\.\s*(\d+)\s*семестр\s+(\d+)\s+(\d+)',
        r'(Пул выборных дисциплин)\.\s*(\d+)\s*семестр\s+(\d+)\s+(\d+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            sub_block_name = match.group(1)
            semester = int(match.group(2))
            credits = int(match.group(3))
            hours = int(match.group(4))
            
            # Находим курсы для этого подблока
            courses = find_courses_after_position(text, match.end())
            
            sub_blocks.append({
                'name': f"{sub_block_name}. {semester} семестр",
                'semester': semester,
                'total_credits': credits,
                'total_hours': hours,
                'courses': courses
            })
    
    return sub_blocks

def parse_practice_block(text: str) -> List[Dict]:
    """Парсинг блока практик"""
    sub_blocks = []
    
    # Ищем практики с семестрами (исключаем "Практика по выбору")
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Пропускаем "Практика по выбору"
        if 'практика по выбору' in line.lower():
            continue
        
        # Ищем строки с практиками
        match = re.match(r'^(\d+)\s+([А-Яё][^0-9]+?)\s+(\d+)\s+(\d+)$', line)
        if match:
            semester = int(match.group(1))
            practice_name = match.group(2).strip()
            credits = int(match.group(3))
            hours = int(match.group(4))
            
            # Проверяем что это практика
            if any(word in practice_name.lower() for word in ['практика', 'работа', 'вкр']):
                course = {
                    'name': practice_name,
                    'credits': credits,
                    'hours': hours,
                    'semester': semester
                }
                
                sub_blocks.append({
                    'name': practice_name,
                    'semester': semester,
                    'total_credits': credits,
                    'total_hours': hours,
                    'courses': [course]
                })
    
    return sub_blocks

def parse_other_block(text: str) -> List[Dict]:
    """Парсинг других блоков"""
    courses = find_courses_in_text(text)
    
    if courses:
        total_credits = sum(course.get('credits', 0) for course in courses)
        total_hours = sum(course.get('hours', 0) for course in courses)
        
        return [{
            'name': 'Дисциплины',
            'semester': None,
            'total_credits': total_credits,
            'total_hours': total_hours,
            'courses': courses
        }]
    
    return []

def parse_universal_block(text: str) -> Optional[Dict]:
    """Парсинг универсальной подготовки"""
    pattern = r'(Универсальная.*подготовка)\s+(\d+)\s+(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        block_name = match.group(1)
        credits = int(match.group(2))
        hours = int(match.group(3))
        
        # Находим курсы после этого блока
        start_pos = match.end()
        block_text = text[start_pos:start_pos + 2000]  # Ограничиваем поиск
        courses = find_courses_in_text(block_text)
        
        return {
            'name': block_name,
            'block_number': None,
            'total_credits': credits,
            'total_hours': hours,
            'sub_blocks': [{
                'name': 'Универсальные дисциплины',
                'semester': None,
                'total_credits': credits,
                'total_hours': hours,
                'courses': courses
            }]
        }
    
    return None

def find_courses_after_position(text: str, start_pos: int) -> List[Dict]:
    """Поиск курсов после определенной позиции"""
    # Берем текст после позиции до следующего подблока
    remaining_text = text[start_pos:]
    
    # Ищем следующий подблок
    next_block = re.search(r'(Обязательные дисциплины|Пул выборных дисциплин|Универсальная)', 
                          remaining_text, re.IGNORECASE)
    
    if next_block:
        relevant_text = remaining_text[:next_block.start()]
    else:
        relevant_text = remaining_text[:1000]  # Ограничиваем поиск
    
    return find_courses_in_text(relevant_text)

def find_courses_in_text(text: str) -> List[Dict]:
    """Поиск курсов в тексте"""
    courses = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Пропускаем короткие строки и заголовки
        if len(line) < 15:
            continue
        
        # Пропускаем "Практика по выбору"
        if 'практика по выбору' in line.lower():
            continue
        
        # Пропускаем заголовки
        if any(word in line for word in ['Блок', 'семестр', 'Трудоемкость', 'Наименование']):
            continue
        
        # Ищем курсы
        course_result = parse_course_line(line)
        if course_result:
            # ИСПРАВЛЕНИЕ: Проверяем, является ли результат списком или словарем
            if isinstance(course_result, list):
                courses.extend(course_result)  # Добавляем все курсы из списка
            else:
                courses.append(course_result)  # Добавляем один курс
    
    return courses

def parse_course_line(line: str) -> Optional[Union[Dict, List[Dict]]]:
    """Парсинг строки с курсом"""
    # Паттерны для курсов
    patterns = [
        r'^(\d+)\s+([А-Яё].+?)\s+(\d+)\s+(\d+)$',           # Семестр + Название + Кредиты + Часы
        r'^([А-Яё].{15,}?)\s+(\d+)\s+(\d+)$',               # Название + Кредиты + Часы
        r'^(\d+,\s*\d+(?:,\s*\d+)*)\s+([А-Яё].+?)\s+(\d+)\s+(\d+)$'  # Список семестров
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            groups = match.groups()
            
            if len(groups) == 4:
                # Проверяем первую группу - семестр или список семестров
                first_group = groups[0]
                
                if ',' in first_group:  # Список семестров
                    semesters = [int(s.strip()) for s in first_group.split(',') if s.strip().isdigit()]
                    name = clean_course_name(groups[1])
                    credits = int(groups[2])
                    hours = int(groups[3])
                    
                    # ИСПРАВЛЕНИЕ: Возвращаем список курсов для каждого семестра
                    return create_multiple_courses(name, credits, hours, semesters)
                
                elif first_group.isdigit():  # Один семестр
                    semester = int(first_group)
                    name = clean_course_name(groups[1])
                    credits = int(groups[2])
                    hours = int(groups[3])
                
                else:  # Название курса в первой группе
                    name = clean_course_name(first_group)
                    credits = int(groups[1])
                    hours = int(groups[2])
                    semester = None
            
            elif len(groups) == 3:  # Название + Кредиты + Часы
                name = clean_course_name(groups[0])
                credits = int(groups[1])
                hours = int(groups[2])
                semester = None
            
            else:
                continue
            
            # Валидация
            if len(name) < 5 or credits <= 0:
                continue
            
            return {
                'name': name,
                'credits': credits,
                'hours': hours,
                'semester': semester
            }
    
    return None

def create_multiple_courses(name: str, credits: int, hours: int, semesters: List[int]) -> List[Dict]:
    """Создание нескольких курсов для разных семестров"""
    courses = []
    for semester in semesters:
        if 1 <= semester <= 8:  # Валидный семестр
            courses.append({
                'name': name,
                'credits': credits,
                'hours': hours,
                'semester': semester
            })
    return courses

def clean_course_name(name: str) -> str:
    """Очистка названия курса"""
    # Удаляем лишние пробелы
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Удаляем номера семестров в начале
    name = re.sub(r'^\d+(?:,\s*\d+)*\s+', '', name)
    
    # Удаляем trailing символы
    name = name.rstrip('/.').strip()
    
    return name

def count_courses_in_block(block: Dict) -> int:
    """Подсчет курсов в блоке"""
    total = 0
    for sub_block in block.get('sub_blocks', []):
        courses = sub_block.get('courses', [])
        if isinstance(courses, list):
            total += len(courses)
        else:
            total += 1
    return total