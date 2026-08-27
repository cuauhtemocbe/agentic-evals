import os
import time
import dotenv
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.synthesizer import Synthesizer

# Cargar variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

DEFAULT_MODEL = "gemini-3.1-flash-lite"

# Cache por nombre de modelo: un singleton global impedía cambiar de modelo
# desde la UI sin reiniciar la app.
_model_instances = {}


def get_gemini_model(model_name=DEFAULT_MODEL):
    """Devuelve (y cachea) la instancia del modelo Gemini para DeepEval."""
    if not api_key:
        raise ValueError("No se encontró la API Key de Gemini en el archivo .env. Configura GEMINI_API_KEY.")
    if model_name not in _model_instances:
        _model_instances[model_name] = GeminiModel(
            model=model_name,
            api_key=api_key
        )
    return _model_instances[model_name]


def _is_transient(exc):
    """True si el error de la API es temporal y vale la pena reintentar."""
    text = str(exc)
    return any(
        marker in text
        for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "INTERNAL")
    )


def _with_retries(fn, attempts=4, base_delay=2.0):
    """Ejecuta fn() reintentando con backoff exponencial ante errores temporales.

    Gemini devuelve 503 UNAVAILABLE cuando el modelo está saturado; suele
    resolverse en unos segundos, así que no tiene sentido fallar al primer intento.
    """
    last_exc = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if not _is_transient(exc) or attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
    raise last_exc

def evaluate_rag(
    query: str,
    response: str,
    contexts: list,
    threshold: float = 0.5,
    model_name: str = DEFAULT_MODEL,
):
    """
    Evalúa una respuesta RAG en base a una consulta y su contexto de recuperación.
    Métricas utilizadas:
    - Faithfulness (Fidelidad / Si hay alucinaciones)
    - Answer Relevancy (Relevancia de la respuesta con la pregunta)
    - Contextual Relevancy (Relevancia del contexto recuperado con la pregunta)
    """
    try:
        model = get_gemini_model(model_name)
        test_case = LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=contexts
        )
        
        # Inicializar métricas
        faithfulness = FaithfulnessMetric(threshold=threshold, model=model)
        answer_relevancy = AnswerRelevancyMetric(threshold=threshold, model=model)
        context_relevancy = ContextualRelevancyMetric(threshold=threshold, model=model)
        
        # Ejecutar métricas (con reintentos ante 503/429 de la API)
        _with_retries(lambda: faithfulness.measure(test_case))
        _with_retries(lambda: answer_relevancy.measure(test_case))
        _with_retries(lambda: context_relevancy.measure(test_case))
        
        return {
            "success": True,
            "metrics": {
                "faithfulness": {
                    "score": faithfulness.score,
                    "reason": faithfulness.reason,
                    "success": faithfulness.is_successful()
                },
                "answer_relevancy": {
                    "score": answer_relevancy.score,
                    "reason": answer_relevancy.reason,
                    "success": answer_relevancy.is_successful()
                },
                "context_relevancy": {
                    "score": context_relevancy.score,
                    "reason": context_relevancy.reason,
                    "success": context_relevancy.is_successful()
                }
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_synthetic_goldens(
    contexts: list,
    max_goldens_per_context: int = 1,
    model_name: str = DEFAULT_MODEL,
):
    """
    Genera casos de prueba de evaluación (Goldens) a partir de una lista de contextos
    de forma sintética, utilizando el módulo Synthesizer de DeepEval.
    """
    try:
        model = get_gemini_model(model_name)
        synthesizer = Synthesizer(model=model)
        
        # El Synthesizer en generate_goldens_from_contexts requiere una lista de listas de strings
        formatted_contexts = [[ctx] for ctx in contexts]
        
        goldens = _with_retries(
            lambda: synthesizer.generate_goldens_from_contexts(
                contexts=formatted_contexts,
                max_goldens_per_context=max_goldens_per_context
            )
        )
        
        results = []
        for g in goldens:
            results.append({
                "input": g.input,
                "expected_output": g.expected_output,
                "context": g.context[0] if g.context else ""
            })
        return {
            "success": True,
            "goldens": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
