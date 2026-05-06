# Test Bench — Métricas de capacidades

**Generado:** 2026-05-06 16:43:54

## Resumen

- **APIs distintas evaluadas:** 14
- **Runs totales:** 40
- **PASS:** 40  |  **FAIL:** 0  |  **SKIP:** 0
- **Tiempo total wall-clock:** 65450.1 ms (65.45 s)
- **Tokens aprox totales (output):** 1,555,346 (chars/4)

> _Nota sobre tokens:_ aproximación honesta `chars/4` sin dependencias externas (DT-008). Para outputs binarios (xlsx) se reporta tamaño en bytes pero NO se cuentan tokens.

## Latencia por API (ms) — promedio sobre 3 L5X

| API | CINTA | AQL | CPPIM | Promedio | Tokens (avg) | PASS |
|-----|------:|----:|------:|---------:|-------------:|:----:|
| `detect_motion_patterns` | 101.6 | 905.6 | 2779.5 | **1262.2** | 1,044 | 3/3 |
| `detect_smells` | 55.4 | 400.1 | 1112.5 | **522.7** | 16,025 | 3/3 |
| `diff_projects` | — | — | — (cross: 18.9) | **18.9** | 2,924 | 1/1 |
| `identify_domain` | 4.7 | 3.4 | 2.6 | **3.6** | 204 | 3/3 |
| `load_project` | 218.4 | 371.6 | 6559.0 | **2383.0** | 0 | 3/3 |
| `mapa_mental` | 7.8 | 17.5 | 484.9 | **170.1** | 4,096 | 3/3 |
| `program_inference` | 18.4 | 552.6 | 2573.6 | **1048.2** | 266 | 3/3 |
| `references_of` | 241.8 | 1762.9 | 3901.5 | **1968.7** | 86 | 3/3 |
| `search('Splice')` | 0.5 | 0.9 | 34.9 | **12.1** | 360 | 3/3 |
| `tag_dictionary` | 24.5 | 103.4 | 232.1 | **120.0** | 48,880 | 3/3 |
| `to_excel` | 679.3 | 3248.1 | 7384.7 | **3770.7** | 0 | 3/3 |
| `to_html_explorer` | 536.4 | 6486.6 | 20240.5 | **9087.8** | 264,524 | 3/3 |
| `to_markdown` | 25.7 | 163.5 | 515.9 | **235.1** | 172,664 | 3/3 |
| `to_tdr_html` | 115.7 | 1014.4 | 2548.7 | **1226.3** | 9,321 | 3/3 |

## Resultados detallados

| API | Project | ms | chars | tokens (~) | items | mem peak (KB) | result | detail |
|-----|---------|---:|------:|-----------:|------:|--------------:|:------:|--------|
| `load_project` | CINTA | 218.4 | 0 | 0 | 42 | 6,846 | ✅ | 12 modules + 26 aois + 4 programs |
| `mapa_mental` | CINTA | 7.8 | 5,404 | 1,351 | 5,404 | 67 | ✅ | 5404 chars |
| `search('Splice')` | CINTA | 0.5 | 1,232 | 308 | 14 | 21 | ✅ | 14 hits |
| `references_of` | CINTA | 241.8 | 160 | 40 | 2 | 1,277 | ✅ | sample tag 'ABS_Master_Velocity' → 2 refs |
| `identify_domain` | CINTA | 4.7 | 1,025 | 256 | 13 | 176 | ✅ | 13 hits (top conf=1.00) |
| `detect_smells` | CINTA | 55.4 | 20,798 | 5,199 | 130 | 189 | ✅ | 130 smells (15 reglas activas) |
| `detect_motion_patterns` | CINTA | 101.6 | 2,460 | 615 | 21 | 219 | ✅ | 21 matches |
| `tag_dictionary` | CINTA | 24.5 | 123,240 | 30,810 | 1,027 | 214 | ✅ | 1027 tags clasificados |
| `program_inference` | CINTA | 18.4 | 723 | 180 | 4 | 99 | ✅ | 4 programs inferidos |
| `to_markdown` | CINTA | 25.7 | 240,480 | 60,120 | 240,480 | 50 | ✅ | 240480 bytes |
| `to_excel` | CINTA | 679.3 | 44,440 | 0 | 44,440 | 2,627 | ✅ | 44440 bytes (xlsx) |
| `to_html_explorer` | CINTA | 536.4 | 253,181 | 63,295 | 253,181 | 4,125 | ✅ | 253181 bytes (html) |
| `to_tdr_html` | CINTA | 115.7 | 22,385 | 5,596 | 22,385 | 221 | ✅ | 22385 bytes (TDR) |
| `load_project` | AQL | 371.6 | 0 | 0 | 75 | 15,265 | ✅ | 44 modules + 24 aois + 7 programs |
| `mapa_mental` | AQL | 17.5 | 8,106 | 2,026 | 8,106 | 69 | ✅ | 8106 chars |
| `search('Splice')` | AQL | 0.9 | 1,882 | 470 | 24 | 51 | ✅ | 24 hits |
| `references_of` | AQL | 1762.9 | 80 | 20 | 1 | 2,408 | ✅ | sample tag 'AB_M10' → 1 refs |
| `identify_domain` | AQL | 3.4 | 988 | 247 | 13 | 7 | ✅ | 13 hits (top conf=1.00) |
| `detect_smells` | AQL | 400.1 | 38,527 | 9,631 | 230 | 140 | ✅ | 230 smells (15 reglas activas) |
| `detect_motion_patterns` | AQL | 905.6 | 4,974 | 1,243 | 43 | 503 | ✅ | 43 matches |
| `tag_dictionary` | AQL | 103.4 | 168,120 | 42,030 | 1,401 | 278 | ✅ | 1401 tags clasificados |
| `program_inference` | AQL | 552.6 | 1,227 | 306 | 7 | 359 | ✅ | 7 programs inferidos |
| `to_markdown` | AQL | 163.5 | 425,275 | 106,318 | 425,275 | 76 | ✅ | 425275 bytes |
| `to_excel` | AQL | 3248.1 | 61,338 | 0 | 61,338 | 3,775 | ✅ | 61338 bytes (xlsx) |
| `to_html_explorer` | AQL | 6486.6 | 583,060 | 145,765 | 583,060 | 8,955 | ✅ | 583060 bytes (html) |
| `to_tdr_html` | AQL | 1014.4 | 26,263 | 6,565 | 26,263 | 268 | ✅ | 26263 bytes (TDR) |
| `load_project` | CPPIM | 6559.0 | 0 | 0 | 445 | 94,598 | ✅ | 410 modules + 28 aois + 7 programs |
| `mapa_mental` | CPPIM | 484.9 | 35,648 | 8,912 | 35,648 | 406 | ✅ | 35648 chars |
| `search('Splice')` | CPPIM | 34.9 | 1,210 | 302 | 14 | 5,768 | ✅ | 14 hits |
| `references_of` | CPPIM | 3901.5 | 800 | 200 | 10 | 4,436 | ✅ | sample tag 'ABP_ParameterSelect' → 10 refs |
| `identify_domain` | CPPIM | 2.6 | 445 | 111 | 6 | 4 | ✅ | 6 hits (top conf=0.70) |
| `detect_smells` | CPPIM | 1112.5 | 132,981 | 33,245 | 755 | 3,727 | ✅ | 755 smells (15 reglas activas) |
| `detect_motion_patterns` | CPPIM | 2779.5 | 5,102 | 1,275 | 45 | 1,658 | ✅ | 45 matches |
| `tag_dictionary` | CPPIM | 232.1 | 295,200 | 73,800 | 2,460 | 466 | ✅ | 2460 tags clasificados |
| `program_inference` | CPPIM | 2573.6 | 1,258 | 314 | 7 | 1,751 | ✅ | 7 programs inferidos |
| `to_markdown` | CPPIM | 515.9 | 1,406,220 | 351,555 | 1,406,220 | 3,035 | ✅ | 1406220 bytes |
| `to_excel` | CPPIM | 7384.7 | 115,854 | 0 | 115,854 | 6,576 | ✅ | 115854 bytes (xlsx) |
| `to_html_explorer` | CPPIM | 20240.5 | 2,338,059 | 584,514 | 2,338,059 | 35,876 | ✅ | 2338059 bytes (html) |
| `to_tdr_html` | CPPIM | 2548.7 | 63,212 | 15,803 | 63,212 | 3,889 | ✅ | 63212 bytes (TDR) |
| `diff_projects` | CINTA→AQL | 18.9 | 11,697 | 2,924 | 487 | 122 | ✅ | 487 entries en diff total |

## Top 5 APIs por latencia (peor caso CPPIM)

| Rank | API | ms | tokens (~) |
|-----:|-----|---:|-----------:|
| 1 | `to_html_explorer` | 20240.5 | 584,514 |
| 2 | `to_excel` | 7384.7 | 0 |
| 3 | `load_project` | 6559.0 | 0 |
| 4 | `references_of` | 3901.5 | 200 |
| 5 | `detect_motion_patterns` | 2779.5 | 1,275 |

## Top 5 APIs por output token-count

| Rank | API | Project | tokens (~) | chars |
|-----:|-----|---------|-----------:|------:|
| 1 | `to_html_explorer` | CPPIM | 584,514 | 2,338,059 |
| 2 | `to_markdown` | CPPIM | 351,555 | 1,406,220 |
| 3 | `to_html_explorer` | AQL | 145,765 | 583,060 |
| 4 | `to_markdown` | AQL | 106,318 | 425,275 |
| 5 | `tag_dictionary` | CPPIM | 73,800 | 295,200 |

## Lectura honesta

- **0 fallos** sobre 40 runs — todas las APIs evaluadas cumplen sus invariantes en los 3 L5X del parque.
- **Wall-clock total** ~65450 ms para ejecutar todas las capacidades sobre los 3 L5X. Costo amortizado ~1636 ms por API+project.
- **Tokens estimados de output:** 1,555,346 acumulados. Esto representa el costo de **leer todos los outputs** como input a un LLM.
- **Stack mínimo (DT-008) preservado:** medición sin dependencias externas (`time.perf_counter`, `tracemalloc`, aproximación `chars/4`).