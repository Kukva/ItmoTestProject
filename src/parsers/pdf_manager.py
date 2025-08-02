import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any
from .pdf_parser import extract_text_from_pdf, parse_curriculum_text, PDF_AVAILABLE

class PDFManager:
    """Менеджер для работы с PDF файлами"""
    
    def __init__(self, pdf_dir: Path):
        self.pdf_dir = pdf_dir
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_pdf(self, pdf_url: str, program_id: str) -> Optional[Path]:
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
    
    def find_local_pdf(self, program_id: str) -> Optional[Path]:
        """Поиск локального PDF файла"""
        # Сначала ищем по стандартным именам
        standard_patterns = [
            f"{program_id}_curriculum.pdf",
            f"{program_id}.pdf",
            f"curriculum_{program_id}.pdf"
        ]
        
        for pattern in standard_patterns:
            pdf_path = self.pdf_dir / pattern
            if pdf_path.exists():
                print(f"📄 Найден PDF по стандартному имени: {pdf_path}")
                return pdf_path
        
        # Ищем все PDF файлы в директории
        all_pdfs = list(self.pdf_dir.glob("*.pdf"))
        
        if not all_pdfs:
            print(f"📄 PDF файлы не найдены в {self.pdf_dir}")
            return None
        
        print(f"📄 Найдено PDF файлов: {len(all_pdfs)}")
        for pdf in all_pdfs:
            print(f"   - {pdf.name}")
        
        # Пытаемся определить принадлежность по содержимому
        for pdf_file in all_pdfs:
            if self._is_pdf_for_program(pdf_file, program_id):
                print(f"📄 PDF {pdf_file.name} подходит для программы {program_id}")
                return pdf_file
        
        # Если не можем определить, берем первый доступный
        if all_pdfs:
            selected_pdf = all_pdfs[0]
            print(f"📄 Используем первый доступный PDF: {selected_pdf.name}")
            return selected_pdf
        
        return None
    
    def _is_pdf_for_program(self, pdf_path: Path, program_id: str) -> bool:
        """Определение принадлежности PDF к программе по содержимому"""
        if not PDF_AVAILABLE:
            return False
        
        try:
            # Извлекаем первые страницы для анализа
            text = self._extract_first_pages_text(pdf_path, max_pages=3)
            
            if not text:
                return False
            
            text_lower = text.lower()
            
            # Ключевые слова для каждой программы
            program_keywords = {
                'ai': [
                    'искусственный интеллект',
                    'artificial intelligence',
                    'машинное обучение',
                    'нейронные сети',
                    'deep learning',
                    'computer vision',
                    'nlp'
                ],
                'ai_product': [
                    'ии в продуктах',
                    'ai product',
                    'продуктовый',
                    'product management',
                    'ai-продукт',
                    'продуктовая аналитика'
                ]
            }
            
            keywords = program_keywords.get(program_id, [])
            
            # Проверяем наличие ключевых слов
            matches = 0
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
                    print(f"   ✅ Найдено ключевое слово: '{keyword}'")
            
            # Если найдено достаточно совпадений, считаем PDF подходящим
            return matches >= 1
            
        except Exception as e:
            print(f"   ❌ Ошибка анализа PDF {pdf_path}: {e}")
            return False
    
    def _extract_first_pages_text(self, pdf_path: Path, max_pages: int = 3) -> str:
        """Извлечение текста с первых страниц PDF"""
        if not PDF_AVAILABLE:
            return ""
        
        text = ""
        
        # Пробуем pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages]):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text
        except Exception as e:
            print(f"   pdfplumber ошибка: {e}")
        
        # Пробуем PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for i in range(min(max_pages, len(pdf_reader.pages))):
                    page = pdf_reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"   PyPDF2 ошибка: {e}")
        
        return text
    
    def parse_local_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
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