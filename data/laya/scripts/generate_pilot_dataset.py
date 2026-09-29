import json

QUESTIONS_FILE = (
    "E:/Python/silvina-editorial/src/infrastructure/resources/laya/decision_questions.json"
)
OUTPUT_FILE = "E:/IA/laya/data/silvina_editorial/pilot_samples.jsonl"

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

# Doc 1: Científico Pleno - Ciberdefensa (Target: ~1.100 - 1.180 palabras)
doc1 = """TÍTULO: Evaluación de la Ciber-resiliencia en Redes Tácticas Militares Distribuidas: Un Modelo Basado en Transiciones de Fase y Simulación Estocástica

1. Introducción y Planteamiento del Problema
La digitalización acelerada de las operaciones militares en el marco del concepto de Guerra Centrada en Redes (Network-Centric Warfare, NCW) y las Operaciones Multidominio (Multi-Domain Operations, MDO) ha transformado la arquitectura de mando, control, comunicaciones, computación, inteligencia, vigilancia y reconocimiento (C4ISR) en una estructura altamente interdependiente de las comunicaciones móviles ad-hoc (Mobile Ad-Hoc Networks, MANET). En un teatro de operaciones contemporáneo, las unidades de maniobra en escalón brigada y batallón dependen críticamente de enlaces tácticos distribuidos para transmitir en tiempo real telemetría de sensores remotos, imágenes captadas por vehículos aéreos no tripulados (UAV), posicionamiento georreferenciado de tropas y órdenes de tiro sincronizadas. Las lecciones operativas extraídas de los conflictos recientes en Europa del Este y el Cáucaso meridional demuestran de manera inequívoca que la superioridad física en el terreno queda completamente neutralizada si la fuerza de maniobra sufre la disrupción persistente de sus canales de enlace de datos. En este contexto, las redes tácticas operan en entornos electromagnéticos profundamente hostiles, caracterizados por anchos de banda severamente restringidos, alta dinámica topológica por el desplazamiento de vehículos y la presencia activa de capacidades adversarias de denegación cibernética y guerra electrónica coordinada.

El presente estudio examina la degradación operativa de redes MANET militares sometidas a ataques coordinados de denegación de servicio distribuida (DDoS) combinados con jamming selectivo de radiofrecuencia a nivel de enlace de datos. La pregunta central que guía esta investigación es: ¿bajo qué condiciones críticas de densidad de nodos comprometidos, topología dinámica y volumen de tráfico malicioso inyectado una red táctica militar experimenta una transición de fase irreversible que anula la conectividad funcional del sistema de mando y control (C2)? El objetivo central de este trabajo es formular un modelo probabilístico de resiliencia táctica y validar experimentalmente un mecanismo dinámico de reconfiguración y aislamiento autónomo que impida la fragmentación de la red antes de que las operaciones tácticas de combate queden incomunicadas.

La justificación teórica de esta investigación se fundamenta en la teoría de percolación en grafos aleatorios y en los principios de comando y control resiliente formulados por David Alberts y Richard Hayes, integrando los aportes de Barabási sobre la robustez de redes libres de escala frente a ataques dirigidos. A diferencia de las investigaciones desarrolladas para redes comerciales o industriales civiles —donde los nodos colaboran de manera altruista y la infraestructura cuenta con soporte dorsal confiable—, en el ciberespacio táctico el adversario busca deliberadamente comprometer nodos neurálgicos para inducir fallas en cascada y segmentar la fuerza. La literatura previa ha abordado la seguridad táctica principalmente desde enfoques perimetrales o de robustez criptográfica, pero existe un vacío evidente respecto a la dinámica de resiliencia en condiciones DIL (Disconnected, Intermittent, Limited). Se adopta la hipótesis de que la resiliencia en combate no depende únicamente de la redundancia estática de enlaces, sino de la velocidad estocástica con la que la topología puede identificar, aislar y purgar nodos comprometidos antes de alcanzar el umbral de percolación destructiva que fractura el grafo de comunicaciones.

2. Metodología y Resultados Experimentales
Para validar empíricamente el modelo propuesto, se diseñó un protocolo de simulación experimental estructurado utilizando el emulador de redes de código abierto CORE (Common Open Research Emulator) acoplado al motor de propagación de eventos discretos EMANE (Extendable Mobile Ad-hoc Network Emulator). Se configuró un escenario táctico representativo de una brigada mecanizada compuesta por 54 nodos activos: 6 puestos de comando táctico vehicular, 24 vehículos de combate blindados, 18 estaciones de radio de soldados desmontados y 6 plataformas UAV de retransmisión de señales, operando en un área geográfica irregular de 20 km x 20 km durante 7.200 segundos de operación continua con modelos de movilidad Gauss-Markov que simulan maniobras envolventes reales.

Se contrastó el desempeño de dos protocolos: el protocolo de enrutamiento táctico estándar de la OTAN OSPF-MANET (RFC 5828) frente a un protocolo adaptativo propuesto denominado ART-Routing (Adaptive Resilient Tactical Routing), el cual incorpora métricas de entropía local en la tasa de reenvío de paquetes y un algoritmo de votación descentralizada por consenso para detectar nodos maliciosos sin depender de servidores centrales. Se diseñaron diez escenarios de estrés ofensivo incremental, simulando ataques de inundación de paquetes (flooding), ataques de agujero negro selectivo (blackhole) y saturación electromagnética localizada, con tasas de inyección hostil que variaron entre el 10% y el 70% de la capacidad de canal nominal. Se ejecutaron 120 réplicas Monte Carlo para garantizar significancia estadística en los estimadores de dispersión.

Los resultados empíricos demuestran que bajo el protocolo estándar OSPF-MANET, la red sufre una transición de fase catastrófica cuando el porcentaje de nodos atacados o comprometidos supera el 19.3%, registrando una caída drástica de la tasa de entrega de paquetes (Packet Delivery Ratio, PDR) desde un valor inicial del 92.4% hasta un 28.7%, con un incremento exponencial de la latencia media de transmisión que pasa de 75 ms a más de 1.820 ms. Esta latencia interrumpe de forma irreversible la actualización de las pantallas tácticas de conciencia situacional en los puestos de comando y bloquea los mensajes de asignación de blancos. Por el contrario, bajo el protocolo ART-Routing, la red mantuvo una tasa de entrega de paquetes superior al 83.1% y una latencia media contenida por debajo de los 135 ms en todos los ensayos, aislando los nodos comprometidos en un tiempo medio de respuesta de 3.8 segundos mediante la poda automática de tablas de ruteo. Las pruebas estadísticas de hipótesis mediante análisis de varianza (ANOVA) confirmaron diferencias altamente significativas (F = 42.8, p < 0.0001) a favor del modelo resiliente desarrollado.

3. Discusión y Conclusiones
Los hallazgos empíricos confirman de manera concluyente la hipótesis planteada y demuestran que la supervivencia cibernética de una fuerza de combate en red no puede asegurarse mediante barreras estáticas o blindajes de cifrado convencional, sino que exige mecanismos estocásticos de reconfiguración topológica inmediata y consenso local. La principal contribución de este trabajo radica en la determinación matemática del umbral crítico de transición de fase para redes tácticas terrestres, ofreciendo una métrica formal para dimensionar la resiliencia en la doctrina militar conjunta y en los manuales de empleo de transmisiones.

Asimismo, el análisis comparativo evidencia que el costo computacional de ejecutar algoritmos de consenso distribuido en procesadores tácticos embebidos insume menos del 7% de la capacidad de procesamiento de los radios de última generación, lo que torna plenamente factible su implementación en hardware militar de uso común. Es necesario reconocer como delimitación que la simulación no contempló el empleo simultáneo de armas de pulso electromagnético (EMP) de gran altitud, factor que deberá abordarse en etapas investigativas posteriores.

En conclusión, el modelo ART-Routing demuestra que es factible mantener la cohesión operativa del comando y control en el ciberespacio táctico aun cuando una fracción sustancial de los nodos móviles haya sido neutralizada o intervenida por el adversario. Se recomienda a los organismos de investigación y desarrollo de las fuerzas armadas incorporar estos criterios de resiliencia dinámica en el diseño de software para radios tácticas definidas por software (SDR) de producción nacional, garantizando la autonomía tecnológica y la continuidad operacional de la defensa en teatros de guerra multidominio altamente disputados."""

# Doc 2: Ensayo de Opinión - Ciberdefensa (Target: ~1.100 - 1.160 palabras)
doc2 = """TÍTULO: El Campo de Batalla Invisible: Consideraciones Filosóficas y Doctrinales sobre la Vulnerabilidad Digital en la Guerra Moderna

1. Introducción y Consideraciones Iniciales
El siglo XXI ha inaugurado una era de transformaciones vertiginosas donde los contornos tradicionales de la guerra y la paz se han desdibujado de manera alarmante e irreversible. A lo largo de la historia de los conflictos humanos, los soldados y los comandantes tenían la certeza tangible de que el enemigo se manifestaba en el terreno físico: marchaba con uniformes reconocibles, desplegaba baterías de artillería pesada sobre las colinas, izaba estandartes visibles en el horizonte y dejaba a su paso una huella de destrucción material inconfundible. En la actualidad, sin embargo, nos enfrentamos a una dimensión ontológica radicalmente distinta. El ciberespacio ha dejado de ser una simple red de comunicaciones electrónicas para transformarse en un teatro de operaciones invisible, silencioso y omnipresente, donde el poder y la soberanía de las naciones se disputan segundo a segundo en la penumbra de los algoritmos y los servidores remotos.

Al contemplar la situación estratégica mundial contemporánea, surge una profunda inquietud sobre la preparación espiritual, intelectual y doctrinal de nuestras instituciones armadas para enfrentar esta nueva realidad. Muchas veces caemos en el error tecnocrático y reduccionista de concebir la ciberdefensa como un mero conjunto de computadoras modernas, cables de fibra óptica y programas de software administrados por ingenieros y especialistas en gabinetes cerrados. Nada más alejado de la verdad profunda de los acontecimientos. La guerra, tal como lo comprendieron con genialidad Sun Tzu en la antigüedad oriental y Carl von Clausewitz en las estepas europeas del siglo XIX, es ante todo un fenómeno político, moral, psicológico y volitivo. Clausewitz escribió que la guerra es un violento choque de voluntades donde la niebla y la fricción dominan inexorablemente el destino de los combatientes. En el ciberespacio, esa niebla es absoluta, porque el adversario puede permanecer oculto en el anonimato global mientras desmantela las capacidades estratégicas de un Estado soberano.

Nos proponemos en estas páginas compartir un conjunto de reflexiones doctrinarias y filosóficas sobre la vulnerabilidad de la nación frente a este desafío contemporáneo. No pretendemos elaborar fórmulas matemáticas complejas, demostraciones empíricas ni protocolos informáticos rígidos de ingeniería de redes, sino interpelar la conciencia de los líderes civiles y militares para que abandonen definitivamente la complacencia analógica y comprendan que la supervivencia de la patria hoy se juega, fundamentalmente, en la arquitectura invisible de nuestras redes digitales y en la fortaleza moral de nuestro pueblo.

2. Desarrollo Reflexivo y Discusión Doctrinal
Basta con observar los episodios recientes de confrontación geopolítica que sacuden el orden internacional para advertir que las grandes potencias mundiales ya no conciben el movimiento de divisiones blindadas, escuadrones aéreos o buques de guerra sin haber ejecutado con anterioridad una demolición quirúrgica de la resiliencia cibernética de su oponente. Las sociedades modernas, y en particular los países en vías de desarrollo como los nuestros, han construido una dependencia casi total e ingenua respecto de sistemas automatizados para la distribución de agua potable, el control del tráfico aéreo, la red de energía eléctrica y el sistema de transferencias financieras. Nos hemos vuelto rehenes de nuestra propia comodidad tecnológica cotidiana.

¿Qué sucedería si un adversario estatal o paraestatal decidiera repentinamente apagar los interruptores de los servidores bancarios centrales o interferir en los sistemas digitales de control de nuestras grandes represas hidroeléctricas? La respuesta es sobrecogedora y desoladora: la sociedad colapsaría en cuestión de pocas horas, generando desabastecimiento, pánico colectivo en las calles y paralizando al gobierno civil sin necesidad de que un solo soldado invasor cruce nuestras fronteras territoriales. Frente a esta amenaza tangible, la insistencia burocrática en destinar presupuestos millonarios a la adquisición rutinaria de armamento convencional obsoleto parece un síntoma grave de anacronismo institucional. Peor aún es la arraigada e ingenua costumbre de comprar sistemas operativos, equipos de comunicaciones y programas de defensa a corporaciones transnacionales extranjeras, ignorando deliberadamente que cada paquete de software foráneo puede contener puertas traseras diseñadas para responder a los intereses geopolíticos de las potencias dominantes.

Ernst Jünger reflexionaba en su ensayo sobre la técnica que las herramientas modernas no son instrumentos neutrales al servicio del hombre, sino fuerzas que imponen su propia lógica de movilización total. Del mismo modo, Michel Foucault advertía con agudeza que el poder contemporáneo no necesita mostrarse con cadenas visibles porque opera a través de redes capilares de vigilancia y control imperceptible. En la guerra informática contemporánea, la manipulación de las mentes ciudadanas mediante la difusión sistemática de desinformación en redes sociales es un vector de debilitamiento tan peligroso como un virus en una central nuclear. Las operaciones de desestabilización psicológica en la zona gris del conflicto buscan quebrar la cohesión social antes de cualquier acción bélica formal. Si la población pierde la fe en sus instituciones democráticas, en sus símbolos patrios y en sus fuerzas de seguridad, el Estado se derrumba desde adentro sin que suene una sola sirena de alarma. Los contratistas de defensa y los proveedores de servicios esenciales son blancos preferenciales de este asedio silencioso. Por eso sostenemos que la ciberdefensa es, en su raíz más honda, una batalla por la identidad, la disciplina cívica y la cohesión espiritual del pueblo argentino.

3. Conclusiones y Exhortación Soberana
En conclusión, consideramos indispensable y urgente abandonar la mentalidad burocrática, pasiva y compartimentada que ha caracterizado a muchas organizaciones de defensa en las últimas décadas. La verdadera ciberdefensa no reside en los manuales importados ni en las inversiones faraónicas en equipamiento foráneo que hipotecan nuestra soberanía, sino en la forja de un espíritu indomable, creativo, patriótico y autárquico. No necesitamos algoritmos complejos traídos de afuera; necesitamos hombres y mujeres imbuidos de profunda vocación de servicio, conscientes de las lecciones eternas de nuestra historia y dispuestos a dar la batalla en este nuevo campo invisible. La autonomía estratégica exige formar cuadros doctrinarios capaces de interpretar la guerra sin ataduras colonialistas.

La soberanía de la patria no se compra empaquetada en el exterior ni se delega en consultoras privadas sin bandera ni lealtad territorial. La soberanía se defiende con coraje intelectual, con austeridad republicana, con producción nacional y con un compromiso ético inquebrantable de nuestras fuerzas armadas para velar por el destino de la nación en este campo de batalla invisible del siglo XXI. Es hora de despertar y comprender que la trinchera moderna es digital, o no será nada. El tiempo apremia y la historia juzgará nuestra determinación para asumir este deber ineludible con la patria."""

# Doc 3: Informe Técnico OVE - Recursos Estratégicos (Target: ~1.100 - 1.180 palabras)
doc3 = """TÍTULO: Protección y Vulnerabilidad de los Objetivos de Valor Estratégico en el Sistema Eléctrico Interconectado Nacional: Balance Operativo 2024

1. Resumen Ejecutivo y Marco Institucional
El presente informe técnico institucional tiene como propósito elevar a las autoridades del Estado Mayor Conjunto de las Fuerzas Armadas y de la Subsecretaría de Planeamiento Estratégico del Ministerio de Defensa el diagnóstico técnico actualizado sobre las condiciones de seguridad física, redundancia operativa y vulnerabilidad estructural que presentan las 14 subestaciones transformadoras de extra alta tensión (500 kV) que integran la red troncal del Sistema Interconectado Nacional (SIN). Estas instalaciones electromecánicas se encuentran formalmente catalogadas y clasificadas como Objetivos de Valor Estratégico (OVE) bajo las directivas del Sistema de Seguridad y Defensa Nacional, en virtud de que su funcionamiento ininterrumpido constituye el soporte material y energético indispensable para el sostenimiento de las actividades industriales, sanitarias, gubernamentales y operativas de las fuerzas militares a lo largo de todo el territorio continental de la república.

El relevamiento exhaustivo llevado a cabo durante el período comprendido entre marzo de 2023 y febrero de 2024 revela un escenario de riesgo crítico originado por la extrema concentración geográfica y funcional de la infraestructura troncal de transporte energético. De los 18.400 kilómetros de líneas de transmisión de 500 kV que cruzan el país, el 62.4% de la potencia máxima despachada en horas de pico de demanda nacional (equivalente a 16.800 MW) converge y depende de apenas cuatro subestaciones nodales situadas en el corredor pampeano-litoral: General Rodríguez, Atucha, Campana y Ezeiza. El análisis técnico y los modelos de flujo de potencia confirman que una contingencia simultánea o un acto de sabotaje coordinado sobre dos de estas cuatro estaciones de maniobra provocaría el colapso inmediato del anillo de extra alta tensión, dejando a más de 18 millones de habitantes y a las principales bases de apoyo logístico de las fuerzas armadas sin suministro eléctrico por un período prolongado e indeterminado.

2. Diagnóstico Técnico y Datos Operativos de Vulnerabilidad
El análisis operativo sustentado en las auditorías de inspección física, termografía aérea y revisiones electromecánicas efectuadas por los equipos conjuntos de técnicos civiles y oficiales ingenieros arrojó datos empíricos concluyentes respecto a las severas demoras logísticas ante fallas catastróficas. El tiempo medio de reparación y restablecimiento de servicio (Mean Time to Repair, MTTR) ante la avería completa o destrucción de un banco de autotransformadores monofásicos de 500/220/33 kV de 200 MVA se sitúa en la actualidad en 96 horas mínimas, asumiendo condiciones climáticas favorables y disponibilidad inmediata de transporte vial pesado. Este valor resulta inaceptable desde el punto de vista de la resiliencia estratégica de la defensa en un escenario de crisis o movilización nacional.

La causa principal de esta demora crítica radica en la alarmante carencia de reservas móviles estratégicas preposicionadas. Actualmente, en todo el territorio nacional existen únicamente dos transformadores de reserva fría compatibles con las especificaciones técnicas del anillo troncal de 500 kV, encontrándose ambos almacenados en un único depósito centralizado en la provincia de Buenos Aires, a más de 800 kilómetros de los nodos críticos del norte del país y de la región del Comahue. La logística requerida para movilizar una unidad transformadora de 140 toneladas mediante carretones viales especiales de múltiples líneas de ejes demanda permisos viales extraordinarios y una coordinación logística compleja que insume entre 48 y 72 horas antes de arribar al nodo averiado, sin contemplar posibles interrupciones en la infraestructura de puentes y calzadas.

En lo concerniente a las medidas de seguridad perimetral y protección de ingeniería civil, las inspecciones de campo revelaron que solo 3 de las 14 instalaciones clasificadas como OVE (21.4%) disponen de sistemas integrados de televigilancia electrónica con cámaras térmicas de visión infrarroja de 360 grados, radar de barrido perimétrico y doble vallado concertina con detección por fibra sensorial activa. Las 11 subestaciones restantes presentan deficiencias operacionales graves: cerramientos olímpicos estándar de malla de alambre tejido sin sensores volumétricos, iluminación perimetral precaria con puntos ciegos notorios y destacamentos de custodia policial o de agencias de seguridad privada que no superan los cuatro agentes por turno. Estas dotaciones carecen de comunicaciones satelitales autónomas redundantes y de armamento adecuado para repeler incursiones de fuerzas hostiles organizadas o comandos de sabotaje.

Adicionalmente, se constató una alta vulnerabilidad en los parques de intemperie respecto a la falta de muros cortafuegos blindados entre fases de transformadores y a la exposición aérea de los aisladores pasamuros de porcelana, los cuales pueden ser destruidos a distancia mediante disparos de fusilería de precisión o drones comerciales modificados con cargas explosivas ligeras. Los sistemas auxiliares de refrigeración forzada por aceite (ONAN/ONAF) y los bancos de interruptores de potencia aislados en gas SF6 no cuentan con resguardo balístico ni estructuras de contención secundaria ante derrames de fluidos dieléctricos. Asimismo, la red de supervisión SCADA que enlaza las subestaciones con el despacho de cargas depende de tendidos de fibra óptica que en sus últimos 5 kilómetros ingresan de forma aérea compartiendo postes con cables de distribución local, exponiéndolos a cortes manuales deliberados o interferencias inductivas sin requerir intrusión física al predio principal.

3. Conclusiones Operativas y Recomendaciones
El balance operativo 2024 demuestra de manera inequívoca que la infraestructura de transporte de energía eléctrica de extra alta tensión de la nación exhibe un nivel de vulnerabilidad inaceptable frente a contingencias bélicas, desastres naturales severos o atentados terroristas, constituyendo un punto de asfixia estratégico para la continuidad de las operaciones del país. La protección de los Objetivos de Valor Estratégico energéticos no puede concebirse como una responsabilidad exclusiva de las empresas distribuidoras privadas, sino que debe asumirse como una prioridad indivisible de la política de defensa nacional y de la seguridad interior del Estado.

En función de las evidencias técnicas recabadas, se recomienda a las autoridades competentes adoptar con carácter urgente las siguientes medidas: primero, tramitar la asignación presupuestaria de emergencia para la adquisición de tres unidades autotransformadoras móviles de 500 kV montadas sobre semirremolques viales de despliegue rápido, preposicionándolas estratégicamente en el interior del país para reducir el MTTR a menos de 24 horas; segundo, ordenar el despliegue permanente de destacamentos de Gendarmería Nacional o tropas de infantería con protocolos de combate perimétrico en las cuatro subestaciones nodales del corredor pampeano; y tercero, ejecutar el soterrado y blindaje físico de los tramos de acceso de las comunicaciones de telemetría y control SCADA, construyendo además muros parapeto anti-dron en los patios de potencia para evitar el aislamiento de mando de las plantas ante ataques convencionales o electromagnéticos."""

# Doc 4: Análisis Teórico - Inteligencia Militar (Target: ~1.100 - 1.180 palabras)
doc4 = """TÍTULO: Hacia una Epistemología de la Inteligencia Prospectiva: Integración del Ciclo de Inteligencia Clásico con Sistemas de Razonamiento Automatizado

1. Introducción y Planteamiento del Problema Epistemológico
La acelerada evolución del escenario geopolítico global, marcada por la emergencia de conflictos híbridos, la proliferación de zonas grises de confrontación interestatal y la contracción drástica de los tiempos de reacción para la toma de decisiones político-militares, ha puesto en jaque el modelo secuencial tradicional del ciclo de inteligencia militar (dirección, reunión, procesamiento, producción y difusión). Durante décadas, la producción de apreciaciones de inteligencia estratégica en los estados mayores conjuntos se estructuró a partir del juicio analítico cualitativo de oficiales y analistas civiles encargados de transformar información fragmentaria en advertencias tempranas. Sin embargo, en el entorno informacional contemporáneo, la proliferación masiva de datos abiertos digitales (OSINT), imágenes satelitales comerciales de alta resolución, intercepciones de señales electromagnéticas y telemetría de campo genera una paradoja epistemológica insidiosa: los comandantes disponen de un volumen de datos infinitamente mayor que en cualquier época pretérita, pero la claridad conceptual para anticipar discontinuidades estratégicas y evitar sorpresas tácticas ha disminuido sensiblemente debido a la saturación cognitiva de los escalones de análisis.

El presente trabajo examina las tensiones teóricas y metodológicas que surgen a raíz de la incorporación de sistemas de razonamiento automatizado, modelos de aprendizaje automático y arquitecturas de inteligencia artificial generativa en las fases analíticas del ciclo de inteligencia militar. La pregunta fundamental que guía esta investigación es: ¿en qué medida la delegación de tareas de inferencia y síntesis prospectiva en sistemas computacionales altera los criterios de validez, trazabilidad epistémica y refutabilidad de las estimaciones estratégicas elevadas a los escalones de conducción superior? El objetivo central es formular un análisis epistemológico riguroso sobre la naturaleza del juicio analítico en defensa, evaluando si las herramientas algorítmicas mitigan los sesgos cognitivos humanos o si, por el contrario, introducen nuevas patologías epistémicas opacas que amplifican el riesgo de error en la apreciación de amenazas a la seguridad nacional.

2. Marco Teórico y Fundamentación Conceptual
Para sustentar este debate, la investigación se ancla en los fundamentos clásicos de la epistemología de la inteligencia estratégica formulados por Sherman Kent, articulados con las contribuciones indispensables de Richard Betts sobre los fallos de percepción y las causas institucionales de la sorpresa estratégica, así como en las teorías de heurística y sesgo cognitivo desarrolladas por Daniel Kahneman y Amos Tversky. Kent sostenía que la producción de inteligencia debe concebirse como un ejercicio de metodología científica rigurosa, donde las hipótesis explicativas deben ser transparentes, explícitas y permanentemente expuestas a la verificación empírica frente a la evidencia emergente. Betts, por su parte, demostró que la mayoría de los desastres estratégicos en la historia militar moderna no se debieron a la falta de información, sino a la incapacidad cognitiva de las burocracias de inteligencia para aceptar advertencias que contradecían las premisas y modelos mentales preexistentes del comando político.

A diferencia de las aproximaciones puramente tecnológicas que presentan a la inteligencia artificial como un oráculo de objetividad matemática neutral, este estudio adopta el enfoque de la cognición distribuida y la epistemología social crítica. Se postula que los modelos predictivos y los transformadores de lenguaje no constituyen agentes neutrales, sino intermediarios cognitivos opacos que codifican los sesgos implícitos presentes en sus datos de entrenamiento históricos. En el ámbito de la inteligencia militar, donde los adversarios recurren intencionalmente a la decepción estratégica (maskirovka) y a la guerra de desinformación, un algoritmo entrenado en patrones del pasado tiende a sobreponderar la normalidad histórica y a descartar como ruido estadístico los indicios sutiles que anuncian eventos de ruptura o agresiones asimétricas inesperadas.

Mientras que el análisis bayesiano tradicional en inteligencia permite calibrar probabilidades a priori mediante la incorporación transparente de nueva evidencia observacional, las redes neuronales profundas operan bajo representaciones latentes distribuidas que impiden al analista reconstruir la cadena causal del razonamiento inferencial. Este fenómeno de opacidad epistémica resulta incompatible con las exigencias de auditoría y responsabilidad del mando en defensa. Si un sistema autónomo alerta sobre una inminente movilización de tropas pero no puede explicitar las premisas lógicas de su deducción, el comandante se enfrenta al dilema de acatar ciegamente una recomendación algorítmica inescrutable o descartarla a riesgo de sufrir una sorpresa estratégica catastrófica. La literatura doctrinal reciente en el ámbito castrense ha eludido este debate, asumiendo acríticamente que la velocidad de procesamiento algorítmico equivale a calidad de análisis. Este trabajo justifica su relevancia al identificar ese vacío teórico en la doctrina conjunta de inteligencia.

3. Discusión Conceptual y Conclusiones Doctrinales
Es menester señalar con honestidad académica la principal limitación metodológica de este trabajo: al tratarse de un estudio estrictamente conceptual y epistemológico, no incluye ensayos de laboratorio ni validaciones experimentales cuantitativas utilizando datos clasificados reales de ejercicios de estado mayor. La naturaleza reservada de los sistemas analíticos de las fuerzas armadas y las restricciones éticas sobre la manipulación de información clasificada impiden en esta etapa realizar contrastaciones empíricas controladas en simulaciones de toma de decisiones operativas bajo fuego. Asimismo, el análisis se circunscribe al escalón estratégico de conducción, dejando para investigaciones complementarias el estudio del impacto en el nivel táctico inmediato de combate donde los tiempos de respuesta demandan mayor grado de automatización reflexiva.

No obstante esta delimitación, el desarrollo teórico permite arribar a conclusiones doctrinales de alta relevancia para el planeamiento militar. Se concluye que la integración de sistemas de razonamiento automatizado en el ciclo de inteligencia no debe concebirse bajo un paradigma de sustitución automatizada, sino bajo un principio de hibridación epistémica supervisada. Los algoritmos deben restringirse a tareas de filtrado, procesamiento masivo y detección preliminar de patrones en grandes volúmenes de datos, preservando de manera inviolable el juicio analítico humano en la etapa de síntesis prospectiva y formulación de advertencias al mando. Se postula la necesidad de crear comités de auditoría de explicabilidad algorítmica en los estados mayores, asegurando que ninguna estimación estratégica que fundamente el empleo del poder militar de la nación sea adoptada sin una comprensión total y refutable de las premisas que guiaron el razonamiento analítico. La confianza ciega en la automatización no es modernización doctrinal, sino una renuncia culposa a la responsabilidad indelegable del mando en la conducción de la defensa nacional."""

# Doc 5: Científico Fuera de Dominio - Pedagogía (Target: ~1.100 - 1.180 palabras)
doc5 = """TÍTULO: Estrategias Didácticas para la Enseñanza de la Historia Colonial en el Nivel Secundario: Un Enfoque Constructivista en Aulas Urbanas

1. Introducción y Planteamiento del Problema Educativo
La enseñanza de la historia en la educación secundaria contemporánea atraviesa una crisis estructural que interpela profundamente el sentido de las prácticas pedagógicas tradicionales en las instituciones escolares. En las aulas de las escuelas secundarias públicas situadas en contextos urbanos, el alumnado suele manifestar un marcado desinterés hacia los contenidos curriculares del área de ciencias sociales, percibiendo los acontecimientos históricos como narraciones lejanas, estáticas y desvinculadas de su realidad socioeconómica cotidiana. Diversas investigaciones en el campo de la didáctica han documentado la persistencia de un paradigma transmisionista y enciclopédico centrado en la memorización acrítica de fechas, batallas y biografías heroicas, lo que obtura el desarrollo de competencias de pensamiento histórico complejo y reduce la historia a un relato memorístico sin significado formativo para la vida cívica.

El presente estudio examina el impacto de la implementación de secuencias didácticas basadas en el aprendizaje por descubrimiento guiado y el trabajo directo con fuentes documentales primarias digitalizadas para la enseñanza del período colonial rioplatense (siglos XVII y XVIII) en alumnos de 3.° año de la educación secundaria. La pregunta de investigación que orientó el trabajo fue: ¿en qué medida la utilización sistemática de fuentes primarias coloniales combinada con técnicas de dramatización y juego de roles de actores sociopolíticos subalternos (esclavizados, pueblos originarios y mestizos) mejora la adquisición de nociones temporales complejas y la empatía histórica en estudiantes secundarios urbanos en comparación con los métodos de enseñanza expositiva tradicionales? El objetivo central fue diseñar, ejecutar y evaluar un dispositivo pedagógico constructivista que promueva la multiperspectividad y la comprensión crítica de los conflictos sociales de la sociedad colonial.

Desde el punto de vista teórico, la investigación se fundamenta en la teoría del aprendizaje significativo desarrollada por David Ausubel, articulada con los aportes de la transposición didáctica de Yves Chevallard y los desarrollos contemporáneos de la didáctica específica de la historia promovidos por Mario Carretero y Peter Seixas, incorporando la teoría sociohistórica de Lev Vygotsky respecto al andamiaje pedagógico entre pares. La literatura educativa previa coincide en señalar la necesidad de transformar las metodologías áulicas en el nivel medio, pero se constata una marcada escasez de investigaciones cuasiexperimentales empíricas que midan con rigor estadístico y rúbricas estandarizadas la efectividad de las fuentes primarias digitalizadas en escuelas de sectores populares urbanos. Se adopta la hipótesis de que el contacto directo con la materialidad del documento histórico y la problematización de sus contradicciones favorece la construcción activa del conocimiento histórico en el aula.

2. Metodología y Resultados Cuasiexperimentales
Para someter a prueba la hipótesis, se implementó un diseño de investigación cuasiexperimental de dos grupos no equivalentes con mediciones previas (pretest) y posteriores (postest). La muestra estuvo conformada por N = 142 estudiantes pertenecientes a cuatro divisiones de dos escuelas secundarias públicas del conurbano bonaerense durante el ciclo lectivo 2023. Dos divisiones integraron el grupo experimental (n = 72 alumnos), el cual transitó durante ocho semanas una secuencia de diez talleres didácticos basados en el análisis guiado de expedientes judiciales del Cabildo de Buenos Aires, cartas de compraventa de personas esclavizadas y representaciones cartográficas coloniales, complementadas con debates de roles y dramatizaciones de juicios históricos. Las otras dos divisiones conformaron el grupo de control (n = 70 alumnos), que abordó la misma unidad temática a través del manual escolar estándar y exposiciones magistrales del docente a cargo del curso.

El instrumento de evaluación consistió en una prueba pedagógica estandarizada y una rúbrica analítica calibrada que midió cuatro variables dependientes fundamentales: ubicación temporal y sincronía histórica, identificación de actores sociales colectivos, análisis crítico de contradicciones en testimonios históricos y capacidad de argumentación causal fundamentada. La recolección de datos se efectuó antes del inicio de las secuencias y al término de las ocho semanas lectivas. Los datos cuantitativos fueron analizados mediante el software estadístico SPSS v26, aplicándose la prueba t de Student para muestras independientes y el cálculo del tamaño del efecto mediante la d de Cohen para contrastar las medias intergrupales.

Los resultados obtenidos arrojaron diferencias altamente significativas en el rendimiento del postest a favor del grupo experimental (t = 5.24, p < 0.001, d = 0.88), evidenciando un tamaño del efecto grande según los baremos estándar. En la dimensión de argumentación histórica causal, el grupo experimental alcanzó una media de 8.35 puntos (sobre 10) frente a 5.92 puntos del grupo de control, registrando un incremento del 41.0% en la capacidad de fundamentar afirmaciones históricas recurriendo a evidencias textuales directas. Asimismo, en el análisis de fuentes primarias, el 78.4% de los alumnos del grupo constructivista logró identificar contradicciones de clase y etnia en los relatos coloniales, frente a solo un 31.2% en el grupo tradicional. Las entrevistas cualitativas semiestructuradas administradas a una submuestra de 24 estudiantes confirmaron que la recreación empática de dilemas históricos transformó la percepción de la disciplina, transitando desde un saber escolar inerte hacia una herramienta comprensiva de la desigualdad social en el presente.

3. Discusión y Conclusiones Educativas
Los hallazgos confirman de manera concluyente la hipótesis de investigación: la mediación pedagógica activa a través de fuentes primarias y la problematización de la voz de los actores subalternos produce mejoras sustanciales en el pensamiento crítico y la comprensión histórica del alumnado adolescente. El estudio demuestra que el desinterés de los jóvenes no es una apatía intrínseca, sino una respuesta previsible a metodologías pedagógicas desvitalizadas y mecánicas que no interpelan su capacidad de razonamiento. Se constata que el trabajo colaborativo con fuentes documentales digitalizadas genera un andamiaje sociohistórico que favorece la descentración cognitiva, permitiendo a los adolescentes comprender que las acciones humanas del pasado estuvieron condicionadas por sistemas de valores específicos y conflictos de intereses antagónicos.

Se concluye que es indispensable actualizar los diseños curriculares jurisdiccionales y los programas de formación docente inicial, promoviendo la incorporación sistemática de talleres de indagación histórica en las escuelas secundarias. La democratización del conocimiento histórico en las aulas constituye una herramienta formativa insustituible para el ejercicio de una ciudadanía democrática consciente, participativa y crítica en el siglo XXI. La historia escolar debe dejar de ser una galería de próceres de bronce para transformarse en un laboratorio vivo de reflexión sobre los dilemas de la sociedad."""

docs = [doc1, doc2, doc3, doc4, doc5]
for i, d in enumerate(docs):
    w = len(d.split())
    print(f"Doc {i + 1}: {w} palabras, {len(d)} caracteres")
    assert 1000 <= w <= 1250, f"Doc {i + 1} has {w} words, outside 1000-1250 range!"

samples = [
    {
        "state": doc1,
        "questions": questions,
        "expected": {
            "s4_intent": "SI",
            "s5_evidence": "SI",
            "s6_theory": "SI",
            "editorial_verdict": "SUSTENTADA",
            "research_line": "4",
            "score_clarity": 9.0,
            "score_coherence": 9.0,
            "score_argumentation": 9.0,
            "score_conclusions": 8.5,
        },
        "language": "es",
        "tags": ["scientific", "cyber", "full_imryd", "defense"],
    },
    {
        "state": doc2,
        "questions": questions,
        "expected": {
            "s4_intent": "NO",
            "s5_evidence": "NO",
            "s6_theory": "NO",
            "editorial_verdict": "NO SUSTENTADA",
            "research_line": "4",
            "score_clarity": 7.0,
            "score_coherence": 6.5,
            "score_argumentation": 5.0,
            "score_conclusions": 4.5,
        },
        "language": "es",
        "tags": ["opinion", "cyber", "rhetorical", "defense"],
    },
    {
        "state": doc3,
        "questions": questions,
        "expected": {
            "s4_intent": "NO",
            "s5_evidence": "SI",
            "s6_theory": "NO",
            "editorial_verdict": "PARCIAL",
            "research_line": "5",
            "score_clarity": 8.5,
            "score_coherence": 8.0,
            "score_argumentation": 6.0,
            "score_conclusions": 6.5,
        },
        "language": "es",
        "tags": ["technical_report", "strategic_resources", "data_rich", "defense"],
    },
    {
        "state": doc4,
        "questions": questions,
        "expected": {
            "s4_intent": "SI",
            "s5_evidence": "NO",
            "s6_theory": "SI",
            "editorial_verdict": "PARCIAL",
            "research_line": "6",
            "score_clarity": 8.5,
            "score_coherence": 8.5,
            "score_argumentation": 8.0,
            "score_conclusions": 6.5,
        },
        "language": "es",
        "tags": ["theoretical", "intelligence", "epistemological", "defense"],
    },
    {
        "state": doc5,
        "questions": questions,
        "expected": {
            "s4_intent": "SI",
            "s5_evidence": "SI",
            "s6_theory": "SI",
            "editorial_verdict": "NO SUSTENTADA",
            "research_line": "NINGUNA",
            "score_clarity": 8.5,
            "score_coherence": 8.5,
            "score_argumentation": 8.0,
            "score_conclusions": 7.5,
        },
        "language": "es",
        "tags": ["scientific", "pedagogy", "out_of_domain"],
    },
]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Generated {len(samples)} realistic canonical samples in {OUTPUT_FILE}")
