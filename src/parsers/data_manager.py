import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class DataManager:
    """Менеджер для сохранения и загрузки данных"""
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
        
        self.project_root = project_root
        self.pdf_dir = project_root / "data" / "pdf"
        self.output_dir = project_root / "data" / "parsed"
        
        # Создаем директории
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results: Dict[str, Any]) -> None:
        """Сохранение результатов парсинга"""
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
        shutil.copy2(full_filename, latest_full)
        shutil.copy2(summary_filename, latest_summary)
        
        print(f"💾 Результаты сохранены:")
        print(f"   Полные данные: {full_filename}")
        print(f"   Сводка: {summary_filename}")
        print(f"   Последние версии: latest_complete.json, latest_summary.json")
    
    def create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def load_latest_data(self) -> Dict[str, Any]:
        """Загрузка последних данных"""
        latest_file = self.output_dir / "latest_complete.json"
        
        if not latest_file.exists():
            return {}
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return {}