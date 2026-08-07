"""
main.py
Main entry point for Silvina Editorial Assistant v0.9
Orchestrates the complete document analysis workflow.
"""

# ruff: noqa: E402 — sys.path must be extended with the project root before
# the src.* imports below can resolve.

from argparse import ArgumentParser
from os.path import exists, join
from pathlib import Path
from re import sub
from sys import exit, path, stderr, stdout
from traceback import print_exc
from typing import Any, Dict

if hasattr(stdout, "reconfigure"):
    stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(stderr, "reconfigure"):
    stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
project_root = Path(__file__).parent
path.insert(0, str(project_root))

from src.domain.dtos.report_input_dto import ReportInputDTO
from src.domain.exceptions.base_src_error import BaseSrcError
from src.domain.exceptions.language_model_errors import LanguageModelUnavailable
from src.infrastructure.wirings.analyze_document_use_case_wiring import (
    AnalyzeDocumentUseCaseWiring,
)
from src.infrastructure.wirings.export_report_wiring import ExportReportWiring
from src.infrastructure.wirings.json_report_wiring import JsonReportWiring


class SilvinaEditorialAssistant:
    """Main orchestrator for the Silvina Editorial Assistant."""

    def __init__(self) -> None:
        """Initialize Silvina wiring the hexagonal use cases."""
        print("🔧 Inicializando Silvina Editorial Assistant v0.9...")

        try:
            self._analyze_document_use_case = AnalyzeDocumentUseCaseWiring().create_use_case()
            self._export_report_use_case = ExportReportWiring().create_use_case()
            self._export_json_report_use_case = JsonReportWiring().create_use_case()
            self._last_report_input: ReportInputDTO | None = None

            print("✅ Silvina inicializada correctamente\n")

        except Exception as e:
            print(f"❌ Error al inicializar Silvina: {e}")
            raise

    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """
        Perform complete analysis of a document using the hexagonal use case pipeline.
        """
        print(f"📄 Analizando documento: {Path(document_path).name}")
        print("=" * 80)

        try:
            report = self._analyze_document_use_case.execute(document_path)
        except LanguageModelUnavailable:
            print(f"\n❌ Error fatal: {LanguageModelUnavailable.MESSAGE}")
            raise
        except Exception as e:
            print(f"\n❌ Error durante el análisis: {e}")
            raise

        print("\n" + "=" * 80)
        print("✅ Análisis completado exitosamente\n")

        self._last_report_input = report
        return self._map_report_to_legacy_dict(report)

    def _map_report_to_legacy_dict(self, report: ReportInputDTO) -> Dict[str, Any]:
        """Convert a ReportInputDTO into the legacy analysis_results dictionary shape."""
        document_content = report.document_content
        classification = report.classification
        quality = report.quality
        grammar = report.grammar
        structure = report.structure
        citations_analysis = report.citations
        apa_validation = report.apa_validation

        return {
            "filename": Path(report.filename).name,
            "document_info": {
                "title": document_content.title,
                "authors": document_content.authors,
                "word_count": document_content.word_count,
                "char_count": document_content.char_count,
                "estimated_pages": document_content.word_count // 250,
            },
            "classification": {
                "category": classification.article_type,
                "article_size": classification.article_size,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
            },
            "quality_analysis": {
                "overall_score": quality.overall_score,
                "quality_level": quality.quality_level,
                "gramatica": {
                    "score": grammar.score,
                    "feedback": grammar.feedback,
                    "errors": grammar.errors,
                },
                "dimensions": quality.dimension_scores,
            },
            "structure_validation": {
                "is_valid": structure.is_valid,
                "missing_sections": structure.missing_sections,
                "details": structure.section_details,
            },
            "citations_analysis": {
                "total_citations": citations_analysis.total_citations,
                "total_references": citations_analysis.total_references,
                "matched_count": citations_analysis.matched_count,
                "unmatched_count": citations_analysis.unmatched_count,
                "by_type": citations_analysis.citations_by_type,
                "unmatched_citations": citations_analysis.unmatched_citations[:20],
                "apa_violations": apa_validation.violation_count,
                "apa_compliant": apa_validation.is_valid,
            },
            "apa_validation": {
                "violations": [
                    {
                        "citation": v.citation_text,
                        "error_type": v.error_type.value,
                        "location": v.location,
                        "explanation": v.explanation,
                        "correction": v.correction,
                    }
                    for v in apa_validation.violations
                ],
                "report": "",
            },
            "recommendations": [
                {"priority": r.priority.value, "message": r.message} for r in report.recommendations
            ],
        }

    def save_word_report(self, analysis_results: Dict[str, Any], output_path: str) -> bool:
        """Save the last analyzed report as a Word document via ExportReportUseCase."""
        try:
            print(f"💾 Guardando reporte Word: {output_path}")
            success = self._export_report_use_case.execute(
                report_input=self._last_report_input, output_path=output_path
            )

            if success:
                print("   ✅ Reporte Word guardado exitosamente")
            else:
                print("   ❌ Error al guardar reporte Word")

            return success

        except Exception as e:
            print(f"   ❌ Error al guardar reporte Word: {e}")
            return False

    def save_json_report(self, analysis_results: Dict[str, Any], output_path: str) -> None:
        """Save the last analyzed report as a JSON file via ExportReportUseCase."""
        print(f"💾 Guardando datos JSON: {output_path}")

        self._export_json_report_use_case.execute(
            report_input=self._last_report_input, output_path=output_path
        )

        print("   ✅ Datos JSON guardados exitosamente")


def _build_argument_parser() -> ArgumentParser:
    """Build the CLI argument parser for the Silvina Editorial Assistant."""
    parser = ArgumentParser(description="Silvina Editorial Assistant - Academic document analysis")
    parser.add_argument(
        "document_path",
        nargs="?",
        default=None,
        help="Path to the .docx document to analyze (prompts interactively if omitted)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for both generated reports (default: same folder as the input document)",
    )
    parser.add_argument(
        "--word-report-path",
        default=None,
        help="Full path for the Word report (default: <output-dir>/<document-name>_analisis.docx)",
    )
    parser.add_argument(
        "--json-report-path",
        default=None,
        help="Full path for the JSON report (default: <output-dir>/<document-name>_analisis.json)",
    )
    return parser


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("   SILVINA EDITORIAL ASSISTANT v0.9")
    print("   Asistente de Análisis Editorial para Documentos Académicos")
    print("=" * 80 + "\n")

    arguments = _build_argument_parser().parse_args()

    document_path = arguments.document_path
    if document_path is None:
        print("📄 SILVINA – Modo interactivo")
        document_path = input("Ingrese la ruta del documento (.docx): ").strip().strip('"')

    # Verify file exists
    if not exists(document_path):
        print(f"❌ Error: El archivo no existe: {document_path}")
        exit(2)

    # Verify it's a .docx file
    if not document_path.lower().endswith(".docx"):
        print("❌ Error: El archivo debe ser un documento Word (.docx)")
        exit(2)

    base_name = Path(document_path).stem
    safe_base_name = sub(r'[<>:"/\\|?*]', "_", base_name)
    output_dir = arguments.output_dir or str(Path(document_path).parent)
    word_report_path = arguments.word_report_path or join(
        output_dir, f"{safe_base_name}_analisis.docx"
    )
    json_report_path = arguments.json_report_path or join(
        output_dir, f"{safe_base_name}_analisis.json"
    )

    try:
        # Initialize Silvina
        silvina = SilvinaEditorialAssistant()

        # Analyze document
        results = silvina.analyze_document(document_path)

        # Save reports
        print("\n" + "=" * 80)
        print("📊 GENERANDO REPORTES")
        print("=" * 80 + "\n")

        # silvina.save_text_report(results, str(text_report_path))
        word_report_saved = silvina.save_word_report(results, str(word_report_path))
        silvina.save_json_report(results, str(json_report_path))

        if not word_report_saved:
            print("Error: No se pudo guardar el reporte de Word (DOCX).")
            exit(1)

        # Print summary
        print("\n" + "=" * 80)
        print("🎉 ANÁLISIS COMPLETADO")
        print("=" * 80)
        print("\nRESUMEN:")
        print(f"  📄 Documento analizado: {Path(document_path).name}")
        print(f"  📝 Total de palabras: {results['document_info']['word_count']:,}")
        print(f"  📝 Total de caracteres: {results['document_info']['char_count']:,}")
        print(f"\n  🏷️  Tipo: {results['classification']['category'].value.upper()}")

        print(f"  📏 Tamaño: {results['classification']['article_size'].value.upper()}")
        print(f"  💭 Razonamiento: {results['classification']['reasoning']}")

        print("\n  ⭐ ANÁLISIS DE CALIDAD:")
        print(
            f"     📝 Gramática (Tier 1): {results['quality_analysis']['gramatica']['score']:.1f}/10"
        )
        print(f"        {results['quality_analysis']['gramatica']['feedback']}")
        # Show detailed errors if any
        gramatica_errors = results["quality_analysis"]["gramatica"].get("errors", [])
        if gramatica_errors:
            print("        Detalles:")
            for err in gramatica_errors[:5]:  # Show first 5
                context = err.context[:50] + "..." if len(err.context) > 50 else err.context
                print(f"          • {err.message}")
                print(f'            Contexto: "{context}"')
                if err.replacements:
                    print(f"            Sugerencia: {', '.join(err.replacements)}")

        print(f"     🧠 Semántica (Tier 2): {results['quality_analysis']['overall_score']:.1f}/10")
        for dim, data in results["quality_analysis"]["dimensions"].items():
            print(f"        • {dim.capitalize()}: {data['score']:.1f}/10 - {data['feedback']}")

        print(
            f"\n  📋 ESTRUCTURA: {'✓ Válida' if results['structure_validation']['is_valid'] else '✗ Incompleta'}"
        )
        if results["structure_validation"]["missing_sections"]:
            print("     Missing sections:")
            for sec in results["structure_validation"]["missing_sections"]:
                print(f"       - {sec}")

        # Total citations excluding footnotes (CitationMatcher already filters footnotes out)
        total_citations = results["citations_analysis"]["total_citations"]
        print(f"\n  📚 CITAS: {total_citations} detectadas")

        print("\n  💡 ANÁLISIS FINAL:")
        for rec in results["recommendations"]:
            color = {"alta": "🔴", "media": "🟡", "baja": "🟢"}.get(rec["priority"], "⚪")
            print(f"     {color} {rec['priority'].upper()}: {rec['message']}")

        print(f"\n  💾 Reportes: {output_dir}")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠ Análisis interrumpido por el usuario")
        exit(0)
    except BaseSrcError as exc:
        message = exc.dict().get("error", "Unknown domain error")
        print(f"\n\n❌ Error fatal: {message}")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        print_exc()
        exit(1)


if __name__ == "__main__":
    main()
