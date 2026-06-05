"""
Structure Validator - Validates IMRyD structure in scientific articles
"""

from typing import List, Dict
from domain.models import Section
from config import REQUIRED_SECTIONS
from domain.models import StructureValidationResult
from domain.enums import ArticleType

class StructureValidator:
    """Validates IMRyD structure in scientific articles."""
    
    def validate(self, sections: List[Section]) -> Dict:
        """Validate structure and return issues."""
        issues = {
            "missing_sections": [],
            "out_of_order": [],
            "too_short": []
        }
        
        # Check for missing sections
        found_names = {s.name for s in sections}
        for required in REQUIRED_SECTIONS.keys():
            if required not in found_names:
                issues["missing_sections"].append(required)
        
        # Check order
        for i in range(len(sections) - 1):
            if sections[i].expected_order > sections[i + 1].expected_order:
                issues["out_of_order"].append((sections[i].name, sections[i + 1].name))
        
        # Check minimum length
        for section in sections:
            min_words = REQUIRED_SECTIONS[section.name]["min_words"]
            if section.word_count < min_words:
                issues["too_short"].append({
                    "section": section.name,
                    "current": section.word_count,
                    "minimum": min_words
                })
        
        return issues
    
    def validate_structure(self, document_content, article_type):
        if article_type == ArticleType.CIENTIFICO:
            required = ["Resumen", "Introducción", "Metodología", "Resultados", "Discusión", "Conclusiones", "Referencias"]
        elif article_type == ArticleType.DIVULGACION:
            required = ["Resumen", "Introducción", "Desarrollo", "Conclusiones", "Referencias"]
        elif article_type == ArticleType.OPINION:
            required = ["Introducción", "Argumentación", "Conclusiones"]
        else:
            required = ["Introducción", "Conclusiones"]

        present = self._extract_present_sections(document_content)

        missing = [
            s for s in required
            if s.lower() not in [p.lower() for p in present]
        ]

        is_valid = len(missing) == 0

        return StructureValidationResult(
            is_valid=is_valid,
            missing_sections=missing
        )

          
    def _get_required_sections(self, category):
        """Get required sections based on article category."""
        from domain.enums import ClassificationCategory
            
        if category == ClassificationCategory.RESEARCH_ARTICLE:
              return ["Resumen", "Introducción", "Metodología", "Resultados", "Discusión", "Conclusiones", "Referencias"]
        elif category == ClassificationCategory.REVIEW_ARTICLE:
              return ["Resumen", "Introducción", "Desarrollo", "Conclusiones", "Referencias"]
        else:
              return ["Introducción", "Desarrollo", "Conclusiones", "Referencias"]

    
    def _extract_present_sections(self, document_content):
        """Extract section headers with flexible matching."""
        sections = []
        
        # Flexible keyword mapping
        section_map = {
            'resumen': ['resumen', 'abstract'],
            'introducción': ['introducción', 'introduccion', 'introduction'],
            'metodología': ['metodología', 'metodologia', 'methodology', 'método', 'metodo', 'materiales y métodos'],
            'resultados': ['resultados', 'resultados y análisis', 'results'],
            'discusión': ['discusión', 'discusion', 'discussion'],
            'desarrollo': ['desarrollo', 'development'],
            'conclusiones': ['conclusiones', 'conclusión', 'conclusion'],
            'referencias': ['referencias', 'bibliografía', 'fuentes bibliográficas']
        }
        
        for para in document_content.paragraphs:
            text_lower = para.lower().strip()
            
            # Check short headers OR inline format (e.g. "Resumen: ...")
            is_short_header = len(text_lower) < 100
            is_inline_header = any(
                text_lower.startswith(kw + ':') or text_lower.startswith(kw + ' :')
                for keywords in section_map.values()
                for kw in keywords
            )
            if is_short_header or is_inline_header:
                for section_name, keywords in section_map.items():
                    if any(kw in text_lower for kw in keywords):
                        sections.append(section_name.capitalize())
                        break
            
            
        return sections
