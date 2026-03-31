# Proyecto de Extracción: Perfil de Ingeniero de Software demandado online

Este plan está diseñado para cumplir con la primera etapa del modelamiento de perfiles de software requeridos en plataformas de empleo. El enfoque principal será **utilizar exclusivamente plataformas tecnológicas que provean mecanismos de extracción directos basados en APIs públicas y gratuitas**.

## Decisiones y Análisis de Fuentes

Para cumplir con el requerimiento de usar plataformas con API como mecanismo principal y descartar el web scraping debido a restricciones y complejidades legales/técnicas, se ha tomado la siguiente resolución:

### Módulo 1: Plataformas Aceptadas (APIs Gratuitas)
- ✅ **Get on Board**: Fuente principal. Orientada íntegramente a perfiles tecnológicos y de LATAM. Provee la API pública `https://www.getonbrd.com/api/v0`.
- ✅ **Remotive**: Plataforma de trabajos remotos tech. Provee el endpoint JSON abierto `https://remotive.com/api/remote-jobs`. 
- ✅ **RemoteOK**: Plataforma internacional orientada a software. Provee un endpoint directo de Array JSON en `https://remoteok.com/api`. 

### Módulo 2: Fuentes Descartadas (Justificación)
- ❌ **Chiletrabajos / BNE Chile**: Se descartan temporalmente. No poseen APIs públicas documentadas. Su extracción requiere **Web Scraping**, contraviniendo la prioridad actual.
- ❌ **Upwork**: Se descarta. Su [API GraphQL](https://www.upwork.com/developer/documentation/graphql/api/docs/index.html) no es pública. Exige llaves de desarrollador aprobadas mediante OAuth 2.0.
- ❌ **Indeed**: Se descarta al no poseer API Publisher pública (solo ecosistema pagado/ATS).

---

## Comparativa Estructural de las APIs

Al analizar el JSON de retorno de cada una de las 3 APIs seleccionadas, identificamos la siguiente disponibilidad y nomenclatura de campos. Esta tabla justifica el diseño de nuestro esquema intermedio `JobOffer`:

| Información Solicitada | Get On Board (`/api/...`) | Remotive (`/api/...`) | RemoteOK (`/api`) | **Esquema Unificado (`JobOffer`)** |
| :--- | :--- | :--- | :--- | :--- |
| **Identificador** | `id` | `id` | `id` / `slug` | `id` (prefijado por fuente) |
| **Título del Puesto** | `attributes.title` | `title` | `position` | `titulo` |
| **Empresa (Nombre)** | `company.name` | `company_name` | `company` | `empresa` |
| **Ubicación Exigida** | `attributes.countries` | `candidate_required_location` | `location` | `ubicacion` |
| **Fecha Publicación** | `attributes.published_at` (Epoch) | `publication_date` (ISO) | `date` (ISO) | `fecha_publicacion` (ISO 8601) |
| **Tags / Tecnologías** | `tags[].name` | `tags[]` | `tags[]` | `tags` (Array de strings) |
| **Modalidad** | `attributes.remote_modality` | Constante ("remoto") | Constante ("remoto") | `modalidad` |
| **Salario Rango** | `min_salary`, `max_salary` | `salary` (String libre) | `salary_min`, `salary_max` | `salario.min`, `salario.max` |
| **Cuerpo / Descripción**| `description` + `functions` (HTML) | `description` (HTML) | `description` (HTML) | `descripcion` (Texto plano limpio) |
| **Categoría** | `category_name` | `category` | Ingerida desde `tags` | `categoria` |

> *Conclusión:* A excepción del salario (donde Remotive devuelve un texto sin normalizar y RemoteOK devuelve enteros en USD), **todos comparten estructuralmente el título, la empresa, descripción HTML, los tags de tecnologías y la fecha de publicación**.

---

## Sugerencia de Segunda Transformación (Post-procesamiento)

Dado el objetivo del proyecto ("Modelar el perfil del ingeniero de software demandado"), unificar los datos extraerá una base sólida. Sin embargo, para **modelar analíticamente** se sugiere que, una vez extraídos todos los JSONs brutos, se ejecute un script de **Segunda Transformación / NLP** sobre la variable `descripcion` (que consolida el cuerpo total de la oferta):

### Nuevos Atributos a extraer (Minables):
1. **Años de Experiencia (`experiencia_minima`)**:
   - *Viabilidad*: **Alta**. Se puede aplicar Expresiones Regulares (Regex) detectando patrones como `(\d+)[\+]* (years|años) de experiencia` o `(\d+)\+ years of experience`.
2. **Nivel Educativo Requerido (`nivel_educativo`)**:
   - *Viabilidad*: **Media**. Se puede buscar en el texto palabras clave cerradas: `[Ingeniería, Civil, Bachiller, Degree, Master, PhD]`.
3. **Pila Tecnológica Extendida (`stack_extendido`)**:
   - *Viabilidad*: **Alta**. Aunque la API entrega un arreglo `tags`, estos suelen estar incompletos. Se puede cruzar la descripcion de la oferta con un diccionario maestro predefinido de lenguajes y frameworks (React, Java, Python, Docker, Go, AWS) para extraer *todas* las habilidades nombradas en texto.
4. **Nivel de Inglés (`english_level`)**:
   - *Viabilidad*: **Alta**. Detectar patrones como `(Inglés|English)\s(C1|B2|Avanzado|Conversacional)`.
5. **Pretensiones de Rango Salarial (Remotive)**:
   - *Viabilidad*: **Media**. Al ser un string libre (`$90k - $120k`), se requerirá una función iterativa separadora que intente parsear y limpiar la moneda al sub-array `salario.min/max`.

---

## Tareas a Ejecutar en Base de Código

1. Depurar el código de extractores de scraping base previos (Chiletrabajos, BNE).
2. Construir `remotive.py` / `remoteok.py` y sus parsers respetando los campos de la 'Comparativa Estructural'.
3. Ajustar `main.py` para correr solo las 3 APIs gratuitas: GetonBoard, Remotive y RemoteOk.
4. Generar el dataset representativo con el comando CLI (`--max-items 50`).
