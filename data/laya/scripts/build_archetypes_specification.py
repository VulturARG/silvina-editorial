import json

lines = [
    {
        "id": "1",
        "name": "Ámbitos de conflicto y su interacción",
        "subthemes": [
            "Operaciones conjuntas y combinadas en el teatro de operaciones del Atlántico Sur",
            "Logística militar y líneas de abastecimiento en combate de alta intensidad",
            "Juegos de guerra y simulación operacional en el planeamiento de estado mayor",
            "Doctrina de maniobra blindada y fuegos coordinados en terreno semiárido",
            "Control y vigilancia de la Zona Económica Exclusiva (ZEE) y espacios jurisdiccionales",
            "Lecciones aprendidas en operaciones militares de paz bajo mandato de la ONU",
            "Evolución del combate multidominio: integración de capacidades aeroespaciales y terrestres",
            "Toma de decisiones tácticas en escalón brigada bajo denegación electromagnética",
        ],
    },
    {
        "id": "2",
        "name": "Estrategia, conflicto y política internacional",
        "subthemes": [
            "Estrategia de disuasión no provocativa en el Cono Sur",
            "Geopolítica del Atlántico Sur, paso bioceánico y proyección antártica",
            "Impacto de la multipolaridad y la competencia entre superpotencias en América Latina",
            "Articulación entre diplomacia y poder militar en crisis interestatales",
            "El Tratado Antártico y los desafíos a la soberanía nacional hacia 2048",
            "Alianzas estratégicas regionales y Consejo de Defensa Suramericano",
            "Guerra irrestricta y zonas grises en la periferia global",
            "Fundamentos teóricos del pensamiento estratégico clásico y contemporáneo",
        ],
    },
    {
        "id": "3",
        "name": "Recursos humanos para la defensa",
        "subthemes": [
            "Gestión del talento y retención de especialistas en áreas técnicas y cibernéticas",
            "Liderazgo y toma de decisiones tácticas bajo estrés extremo en combate",
            "Impacto psicológico y abordaje del TEPT en personal de fuerzas especiales",
            "Integración de factores humanos en la operación de sistemas de armas autónomos",
            "Modelos de carrera militar profesional y voluntaria en el siglo XXI",
            "Capacitación y doctrina militar frente a la irrupción de la IA en estados mayores",
            "Aspectos psicosociales en misiones de aislamiento prolongado (Bases Antárticas)",
            "Ética militar y conducción en escenarios de guerra híbrida y asimétrica",
        ],
    },
    {
        "id": "4",
        "name": "Dinámica de los conflictos en el ciberespacio",
        "subthemes": [
            "Ciber-resiliencia de redes tácticas de mando y control (C2) bajo guerra electrónica",
            "Ataques cibernéticos contra infraestructuras críticas y centrales de energía",
            "Marcos jurídicos y Derecho Internacional Humanitario aplicable a ciberoperaciones ofensivas",
            "Guerra de información, desinformación algorítmica y operaciones psicológicas",
            "Convergencia ciber-física y vulnerabilidad de sistemas de armas digitalizados",
            "Criptografía poscuántica para comunicaciones tácticas seguras",
            "Doctrina de ciberdefensa activa y respuesta ante amenazas persistentes avanzadas (APT)",
            "Protección de redes satelitales y telemetría espacial frente a ciberataques",
        ],
    },
    {
        "id": "5",
        "name": "Conocimiento, gestión y protección de recursos estratégicos",
        "subthemes": [
            "Protección y resiliencia de Objetivos de Valor Estratégico (OVE) energéticos (SIN 500 kV)",
            "Seguridad y control de la navegación en la Hidrovía Paraná-Paraguay",
            "Minerales críticos para la defensa: geopolítica y aseguramiento del litio y cobre",
            "Protección de cuencas hídricas transfronterizas y acuíferos estratégicos",
            "Infraestructura portuaria y corredores logísticos bioceánicos en la Patagonia",
            "Sustentabilidad y autosuficiencia de combustibles en bases militares desplegadas",
            "Vulnerabilidad de las telecomunicaciones submarinas y cables de datos de fibra óptica",
            "Defensa de la plataforma continental y de los recursos vivos del mar austral",
        ],
    },
    {
        "id": "6",
        "name": "Inteligencia en los diversos ámbitos de conflicto",
        "subthemes": [
            "Inteligencia geoespacial (GEOINT) satelital para el control de fronteras terrestres",
            "Epistemología y límites del razonamiento automatizado en la apreciación estratégica",
            "Ciclo de inteligencia conjunto frente a la sobreabundancia de fuentes abiertas (OSINT)",
            "Detección de decepción estratégica (maskirovka) en operaciones militares contemporáneas",
            "Sistemas C4ISR integrados para alerta temprana en la defensa aeroespacial",
            "Producción de inteligencia prospectiva en escenarios de crisis geopolítica",
            "Contrainteligencia digital y protección de secretos tecnológicos militares",
            "Interoperabilidad de sensores multidominio en tiempo real para estados mayores",
        ],
    },
    {
        "id": "7",
        "name": "Ciencia, tecnología y producción en la defensa",
        "subthemes": [
            "Desarrollo de la base industrial para la defensa a través del FONDEF",
            "Modernización de blindados y vehículos de combate: el programa TAM 2C",
            "Producción de radares primarios militares 3D (RPA) y soberanía de vigilancia",
            "Desarrollo y fabricación de aeronaves de entrenamiento avanzado (IA-63 Pampa III)",
            "Sistemas autónomos no tripulados (UAV / UGV) de producción nacional",
            "Capacidades astilleras navales y patrulleros oceánicos para la milla 200",
            "Transferencia tecnológica y soberanía en munición guiada de precisión",
            "Desarrollo de propelentes y tecnología de vectores aeroespaciales soberanos",
        ],
    },
]

boolean_profiles = [
    {
        "profile_id": "000",
        "s4_intent": "NO",
        "s5_evidence": "NO",
        "s6_theory": "NO",
        "editorial_verdict": "NO SUSTENTADA",
        "expected_scores": {
            "clarity": 7.0,
            "coherence": 6.5,
            "argumentation": 5.0,
            "conclusions": 4.5,
        },
        "style": "Ensayo de opinión / reflexión libre sin método científico, sin datos ni marco conceptual formal",
    },
    {
        "profile_id": "001",
        "s4_intent": "NO",
        "s5_evidence": "NO",
        "s6_theory": "SI",
        "editorial_verdict": "NO SUSTENTADA",
        "expected_scores": {
            "clarity": 7.5,
            "coherence": 7.0,
            "argumentation": 6.0,
            "conclusions": 5.5,
        },
        "style": "Ensayo teórico con referencias bibliográficas pero sin preguntas de investigación ni datos empíricos",
    },
    {
        "profile_id": "010",
        "s4_intent": "NO",
        "s5_evidence": "SI",
        "s6_theory": "NO",
        "editorial_verdict": "PARCIAL",
        "expected_scores": {
            "clarity": 8.5,
            "coherence": 8.0,
            "argumentation": 6.0,
            "conclusions": 6.5,
        },
        "style": "Informe técnico descriptivo con abundantes datos empíricos y métricas, pero sin hipótesis ni marco teórico",
    },
    {
        "profile_id": "011",
        "s4_intent": "NO",
        "s5_evidence": "SI",
        "s6_theory": "SI",
        "editorial_verdict": "PARCIAL",
        "expected_scores": {
            "clarity": 8.5,
            "coherence": 8.0,
            "argumentation": 7.0,
            "conclusions": 7.0,
        },
        "style": "Monografía analítica con datos y literatura previa, pero estructurada descriptivamente sin pregunta/diseño formal",
    },
    {
        "profile_id": "100",
        "s4_intent": "SI",
        "s5_evidence": "NO",
        "s6_theory": "NO",
        "editorial_verdict": "NO SUSTENTADA",
        "expected_scores": {
            "clarity": 7.5,
            "coherence": 7.0,
            "argumentation": 5.5,
            "conclusions": 5.0,
        },
        "style": "Propuesta preliminar o proyecto exploratorio que plantea preguntas pero no presenta datos ni marco teórico",
    },
    {
        "profile_id": "101",
        "s4_intent": "SI",
        "s5_evidence": "NO",
        "s6_theory": "SI",
        "editorial_verdict": "PARCIAL",
        "expected_scores": {
            "clarity": 8.5,
            "coherence": 8.5,
            "argumentation": 8.0,
            "conclusions": 6.5,
        },
        "style": "Artículo teórico-conceptual riguroso con pregunta de investigación y marco doctrinal, pero sin contrastación empírica",
    },
    {
        "profile_id": "110",
        "s4_intent": "SI",
        "s5_evidence": "SI",
        "s6_theory": "NO",
        "editorial_verdict": "PARCIAL",
        "expected_scores": {
            "clarity": 8.5,
            "coherence": 8.0,
            "argumentation": 7.5,
            "conclusions": 7.0,
        },
        "style": "Estudio empírico/experimental con metodología y resultados cuantitativos, pero con escaso marco conceptual o estado del arte",
    },
    {
        "profile_id": "111",
        "s4_intent": "SI",
        "s5_evidence": "SI",
        "s6_theory": "SI",
        "editorial_verdict": "SUSTENTADA",
        "expected_scores": {
            "clarity": 9.0,
            "coherence": 9.0,
            "argumentation": 9.0,
            "conclusions": 8.5,
        },
        "style": "Artículo científico pleno con estructura IMRyD, marco teórico sólido, datos empíricos demostrativos y conclusiones fundadas",
    },
]

archetypes = []
index = 1
for line in lines:
    for profile_idx, p in enumerate(boolean_profiles):
        subtheme = line["subthemes"][profile_idx % len(line["subthemes"])]
        archetype = {
            "archetype_id": f"ARC-{index:02d}",
            "research_line_id": line["id"],
            "research_line_name": line["name"],
            "profile_id": p["profile_id"],
            "subtheme": subtheme,
            "signals": {
                "s4_intent": p["s4_intent"],
                "s5_evidence": p["s5_evidence"],
                "s6_theory": p["s6_theory"],
            },
            "editorial_verdict": p["editorial_verdict"],
            "expected_scores": p["expected_scores"],
            "style_archetype": p["style"],
            "samples_target_count": 8,
        }
        archetypes.append(archetype)
        index += 1

matrix = {
    "version": "1.0",
    "total_archetypes": len(archetypes),
    "target_samples_per_archetype": 8,
    "total_expected_samples": len(archetypes) * 8,
    "research_lines_count": len(lines),
    "boolean_profiles_count": len(boolean_profiles),
    "archetypes": archetypes,
}

out_path = "E:/IA/laya/data/silvina_editorial/archetypes_specification.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(matrix, f, ensure_ascii=False, indent=2)

print(f"Successfully defined {len(archetypes)} archetypes in {out_path}")
print(f"Total planned samples: {len(archetypes) * 8}")
