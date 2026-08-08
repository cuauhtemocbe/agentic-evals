import json
import os
import sys

import pytest

# Anclado al directorio del proyecto (no al cwd del proceso que invoca pytest)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

import generate_mock_data
from agent import DataClassifierAgent


@pytest.fixture(scope="session", autouse=True)
def setup_mock_data():
    """
    Fixture que se ejecuta una vez al inicio de la sesión de pruebas.
    Llama al script de generación para crear las imágenes y el dataset.json.
    """
    print("\n[Pytest Setup] Generando imágenes y datos mock...")
    generate_mock_data.main()
    yield
    print("\n[Pytest Teardown] Sesión de pruebas completada.")

@pytest.fixture
def dataset_content():
    """
    Fixture que lee y retorna el contenido estructurado del dataset de prueba.
    """
    dataset_path = os.path.join(PROJECT_ROOT, "data", "dataset.json")
    with open(dataset_path, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def agent():
    """
    Fixture que retorna una instancia limpia de DataClassifierAgent.
    """
    return DataClassifierAgent()
