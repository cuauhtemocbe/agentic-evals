# Proyecto_3 — Errores encontrados al levantar la app

Registro de los problemas que aparecieron al poner a correr `app.py` (DeepEval Academy)
en el entorno Docker del repo, con la causa real y el fix aplicado en cada caso.

Fecha del diagnóstico: **2026-08-26**. Los modelos de Gemini disponibles cambian con el
tiempo — ver [Modelos de Gemini](#7-modelos-de-gemini-3-de-4-opciones-estaban-muertas)
antes de asumir que la tabla sigue vigente.

## Cómo levantar la app

```bash
make streamlit-m03-p3        # Docker → http://localhost:8503
make streamlit-m03-p3-local  # fallback con poetry, sin Docker
```

---

## Errores de entorno

### 1. `deepeval` no estaba declarado como dependencia

**Síntoma**: ninguno inmediato — el contenedor en uso ya lo tenía. El problema aparecía
al correr `make build` o al recrear el contenedor: `ModuleNotFoundError: No module named
'deepeval'`.

**Causa**: `deepeval` se había instalado *ad-hoc* dentro del contenedor (probablemente con
un `pip install` desde un notebook), pero nunca se agregó a `pyproject.toml`. Como
`Dockerfile.dev` instala dependencias con `poetry install` a partir del lock, cualquier
reconstrucción de la imagen lo perdía silenciosamente.

**Fix**: agregado al grupo `notebooks` de `pyproject.toml` y regenerado el lock.

```toml
[tool.poetry.group.notebooks.dependencies]
deepeval = "^4.1.8"
```

> **Nota**: el `requirements.txt` de esta carpeta **no** se usa en el flujo Docker del
> repo; es solo referencia del material original del curso. La fuente de verdad es
> `pyproject.toml` + `poetry.lock` en la raíz.

### 2. `GeminiModel` requiere el paquete `google-genai`

**Síntoma**:

```
deepeval.errors.DeepEvalError: GeminiModel requires the `google.genai` package.
Install it with `pip install google-genai`.
```

**Causa**: en DeepEval 4.x, `GeminiModel` usa el SDK nuevo `google-genai`, no el viejo
`google-generativeai` (que además ya está deprecado y emite un `FutureWarning` al
importarse). El repo solo tenía el viejo, que es el que usa `rag_system.py`.

El detalle que lo hace difícil de diagnosticar: **el error salta al *instanciar* el
modelo, no al importarlo**. `from deepeval.models import GeminiModel` funciona sin
problema, así que la app arrancaba y la UI cargaba entera — reventaba recién al apretar
"Iniciar Evaluación".

**Fix**: agregado `google-genai = "^1.0.0"` a `pyproject.toml`. Ambos SDK conviven sin
conflicto: `rag_system.py` sigue usando el viejo, `eval_utils.py` el nuevo vía DeepEval.

### 3. El puerto 8503 no estaba publicado

**Causa**: `docker-compose.yml` mapeaba 8501 (Módulo 01) y 8502 (Módulo 02), pero no había
puerto libre asignado a esta app.

**Fix**: agregado `"8503:8503"` a `docker-compose.yml` y creados los targets
`streamlit-m03-p3` / `streamlit-m03-p3-local` en el `Makefile`.

Convención de puertos del repo:

| Puerto | App |
|--------|-----|
| 8501 | Módulo 01 / Proyecto_01 |
| 8502 | Módulo 02 / Proyecto_02 |
| 8503 | Módulo 03 / Proyecto_3 |
| 8888 | JupyterLab |

---

## Errores en el código del proyecto

Los tres salieron a la luz a partir de un único síntoma:

```
Ocurrió un error al ejecutar la evaluación: 503 UNAVAILABLE.
{'error': {'code': 503, 'message': 'This model is currently experiencing high demand.
Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
```

Ese 503 venía **de Google**, no del código: `gemini-3.1-flash-lite` estaba saturado en ese
momento (confirmado con una llamada directa a la API, fuera de DeepEval). El problema es
que el código convertía un error temporal en un callejón sin salida.

### 4. El selector de modelo del sidebar no hacía nada

**Causa**: `app.py` calculaba `model_name` con un `st.selectbox`, pero las funciones de
evaluación llamaban a `get_gemini_model()` **sin argumento**, cayendo siempre en el valor
por defecto del parámetro. El valor elegido en la UI se descartaba.

```python
# app.py — el usuario elige un modelo...
model_name = st.selectbox("Modelo de LLM Judge:", [...])

# eval_utils.py — ...y acá se ignora por completo
def evaluate_rag(query, response, contexts, threshold=0.5):
    model = get_gemini_model()   # ← sin model_name
```

Consecuencia práctica: frente al 503, cambiar de modelo en el sidebar no servía de nada —
seguías pegándole al modelo saturado.

**Fix**: `evaluate_rag()` y `generate_synthetic_goldens()` ahora reciben `model_name`, y
`app.py` les pasa el valor del sidebar.

### 5. `get_gemini_model()` era un singleton global

**Causa**: la instancia se cacheaba en una única variable global, sin tener en cuenta qué
modelo se había pedido.

```python
_model_instance = None

def get_gemini_model(model_name="gemini-3.1-flash-lite"):
    global _model_instance
    if _model_instance is None:          # ← ignora model_name si ya hay una instancia
        _model_instance = GeminiModel(model=model_name, api_key=api_key)
    return _model_instance
```

Aun arreglando el bug anterior, la primera instancia creada quedaba fija para toda la vida
del proceso: cambiar de modelo habría exigido reiniciar la app.

**Fix**: cache por nombre de modelo.

```python
_model_instances = {}

def get_gemini_model(model_name=DEFAULT_MODEL):
    if model_name not in _model_instances:
        _model_instances[model_name] = GeminiModel(model=model_name, api_key=api_key)
    return _model_instances[model_name]
```

### 6. Cero reintentos ante errores temporales de la API

**Causa**: un 503 en cualquiera de las tres métricas abortaba la evaluación completa. Los
503 de Gemini por saturación suelen resolverse en segundos, así que fallar al primer
intento es tirar el trabajo a la basura por nada.

**Fix**: helper `_with_retries()` en `eval_utils.py`, con backoff exponencial
(4 intentos: 2s, 4s, 8s), aplicado a las tres métricas y al `Synthesizer`.

Distingue errores **temporales** (reintenta) de **permanentes** (falla rápido):

| Reintenta | No reintenta |
|-----------|--------------|
| `503` / `UNAVAILABLE` | `404` (modelo inexistente) |
| `429` / `RESOURCE_EXHAUSTED` | `401` / `403` (API key inválida) |
| `500` / `INTERNAL` | Errores de validación |

Verificado: ante un fallo transitorio simulado se recupera al 3.er intento; ante un 404
corta en el primero sin dormir.

### 7. Modelos de Gemini: 3 de 4 opciones estaban muertas

El `selectbox` original ofrecía cuatro modelos, de los cuales **tres ya no existen** —
devuelven `404 NOT_FOUND`, no 503. Es decir: aunque el selector hubiera estado bien
cableado, tres de las cuatro opciones habrían fallado igual, por un motivo distinto.

Resultado de probar cada modelo contra la API key del repo (2026-08-26):

| Estado | Modelos |
|--------|---------|
| ❌ `404` — retirados | `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` |
| ⚠️ `503` — saturados en ese momento | `gemini-3.1-flash-lite`, `gemini-flash-latest` |
| ✅ OK | `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.7-flash`, `gemini-3-flash-preview`, `gemini-flash-lite-latest` |

**Los alias `-latest` no son inmunes al 503**: `gemini-flash-latest` también estaba caído,
mientras que `gemini-flash-lite-latest` respondía bien. No sirven como fallback garantizado.

**Fix**: la lista del selector se reemplazó por modelos verificados como existentes.
Si uno devuelve 503, la salida es elegir otro en el sidebar.

Para listar los modelos realmente disponibles con tu API key en cualquier momento:

```bash
docker compose exec -T -w "/app/docs/Modulo 03/Proyecto_3" api python -c "
import os, dotenv
from google import genai
dotenv.load_dotenv()
c = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
for m in c.models.list():
    if 'generateContent' in (m.supported_actions or []):
        print(m.name.replace('models/', ''))
"
```

---

## Verificación rápida del entorno

Comprobar que las dependencias, los módulos locales y el LLM judge funcionan de punta a
punta, sin pasar por la UI:

```bash
docker compose exec -T -w "/app/docs/Modulo 03/Proyecto_3" api python -c "
import rag_system, eval_utils
print('KB docs:', len(rag_system.KNOWLEDGE_BASE))
r = eval_utils.evaluate_rag(
    query='¿Cada cuánto se cambia la contraseña?',
    response='Cada 90 días de forma obligatoria.',
    contexts=['Las contraseñas de ActumLogos deben actualizarse obligatoriamente cada 90 días.'],
    threshold=0.5,
    model_name='gemini-3.5-flash-lite',
)
print('success:', r['success'])
print(r['metrics'] if r['success'] else r['error'])
"
```

Salida esperada: `success: True` y las tres métricas (faithfulness, answer_relevancy,
context_relevancy) en 1.0.

Chequeo de que la app responde:

```bash
curl -s http://localhost:8503/_stcore/health   # → ok
```

---

## Resumen de archivos tocados

| Archivo | Cambio |
|---------|--------|
| `pyproject.toml` / `poetry.lock` | + `deepeval`, + `google-genai` |
| `docker-compose.yml` | + puerto `8503:8503` |
| `Makefile` | + `streamlit-m03-p3`, + `streamlit-m03-p3-local`; fix de la regex de `help` (excluía dígitos, así que ningún target `streamlit-*` aparecía en `make help`) |
| `docs/Modulo 03/Proyecto_3/eval_utils.py` | cache por modelo, parámetro `model_name`, `_with_retries()` |
| `docs/Modulo 03/Proyecto_3/app.py` | pasa `model_name` a las funciones de eval; lista de modelos actualizada |
