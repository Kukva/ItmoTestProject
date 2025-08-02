import re
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

def parse_directions_data(text: str) -> List[Dict]:
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

def parse_table_col_data(text: str) -> Dict[str, str]:
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

def extract_web_data(soup: BeautifulSoup) -> Dict:
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

async def parse_web_page(url: str) -> Optional[Dict]:
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