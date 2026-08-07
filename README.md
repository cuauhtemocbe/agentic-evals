# agentic-evals

Repositorio de prácticas del curso de evaluación de agentes (agentic evals). Incluye el entorno de desarrollo (Docker + Poetry) y las prácticas de cada módulo del curso.

## Overview rápido

1. Instalar Docker (o Python 3.13 + Poetry + make si vas por la vía local) — ver [Instalación de las herramientas](#instalación-de-las-herramientas).
2. Clonar el repositorio.
3. `make build`
4. `make up-d`
5. `make notebook` → abrí [http://localhost:8888](http://localhost:8888).

Con eso ya tenés el entorno levantado y JupyterLab disponible para trabajar sobre `docs/`. Para más detalle de cada paso, o para la vía local sin Docker, ver las secciones siguientes.

## Requisitos previos

Elegí una de las dos formas de trabajar:

- **Con Docker (recomendado):** Docker y Docker Compose.
- **Local (sin Docker):** Python 3.13, [Poetry](https://python-poetry.org/docs/#installation) y `make`.

### Instalación de las herramientas

**Docker**
- Linux: https://docs.docker.com/engine/install/
- Windows: https://docs.docker.com/desktop/setup/install/windows-install/

**Poetry**
- Linux: https://python-poetry.org/docs/#installing-with-the-official-installer
- Windows: https://python-poetry.org/docs/#installing-with-the-official-installer (mismo instalador, ejecutado desde PowerShell — ver instrucciones para Windows en esa página)

**Make**
- Linux: viene preinstalado en la mayoría de las distros, o se instala vía el gestor de paquetes (ej. `apt install make`, `dnf install make`). Referencia: https://www.gnu.org/software/make/
- Windows: https://community.chocolatey.org/packages/make (vía Chocolatey) o https://gnuwin32.sourceforge.net/packages/make.htm

## Configuración del entorno

### Opción A: con Docker

1. Clonar el repositorio y ubicarte en la raíz del proyecto.
2. (Opcional) Crear un archivo `.env` en la raíz si necesitás definir variables de entorno para los servicios levantados por `docker-compose.yml`. No es obligatorio: `docker compose` sigue funcionando si no existe.
3. Construir la imagen:
   ```bash
   make build
   ```
4. Levantar los servicios:
   ```bash
   make up
   ```
   o en background:
   ```bash
   make up-d
   ```
5. Levantar JupyterLab (para trabajar con las prácticas de `docs/`):
   ```bash
   make notebook
   ```
   Esto expone JupyterLab en [http://localhost:8888](http://localhost:8888), sin token (ver nota de seguridad más abajo).
6. Para bajar los servicios:
   ```bash
   make down
   ```

> **Nota de seguridad:** `make notebook` (y `make notebook-local`) levantan JupyterLab sin token ni password, para simplificar la configuración en local. Esto significa que cualquiera que llegue al puerto 8888 puede ejecutar código. Es un trade-off aceptable para un entorno de desarrollo local de prácticas, pero no debería usarse así en un servidor expuesto a una red compartida o pública.

### Opción B: local con Poetry

1. Clonar el repositorio y ubicarte en la raíz del proyecto.
2. Instalar las dependencias:
   ```bash
   make install
   ```
   (equivale a `poetry install`)
3. Trabajar con las prácticas usando Jupyter dentro del entorno de Poetry:
   ```bash
   poetry run jupyter lab
   ```

> Para ver todos los comandos disponibles (incluyendo los de testing y linting), correr `make help`.

> **Nota sobre `make install-hooks`:** las reglas de `ruff`/`mypy` (`make lint`, `make format-check`, `make typecheck`) están pensadas para código de producción, no para los scripts de práctica de `docs/`. Si instalás el pre-commit hook (`make install-hooks`), es esperable que algunos commits sobre `docs/` fallen por estilo o tipado. Para commitear sin correr el hook en ese caso, usá:
> ```bash
> git commit --no-verify -m "tu mensaje"
> ```
> o simplemente no corras `make install-hooks` si vas a trabajar solo sobre `docs/`.

## Trabajar con los notebooks en VSCode

1. Instalar las extensiones de VSCode:
   - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
   - [Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
2. Seleccionar el kernel, según la opción de entorno que hayas elegido:
   - **Local con Poetry:** con las dependencias ya instaladas (`make install`), abrí cualquier notebook de `docs/Modulo XX/`, hacé clic en **Select Kernel** (arriba a la derecha) y elegí el entorno de Poetry del proyecto. Si no aparece en la lista, obtené la ruta del intérprete con:
     ```bash
     poetry env info --path
     ```
     y agregala manualmente con **Select Kernel → Select Another Kernel → Enter interpreter path...**.
   - **Con Docker:** levantá JupyterLab con `make notebook`. En VSCode, abrí la paleta de comandos (`Ctrl+Shift+P` / `Cmd+Shift+P`) y ejecutá **Jupyter: Specify Jupyter Server for Connections**, indicando `http://localhost:8888` (el server corre sin token, no hace falta pegar nada más). Luego seleccioná ese servidor como kernel del notebook.
3. Abrí el notebook (`.ipynb`) que quieras trabajar dentro de `docs/Modulo XX/` y corré las celdas normalmente.

## Estructura del repositorio

```
.
├── docs/               # Prácticas del curso, organizadas por módulo
├── pyproject.toml       # Dependencias del proyecto (Poetry)
├── poetry.lock
├── Dockerfile.dev
├── docker-compose.yml
└── Makefile             # Comandos del flujo de trabajo (make help)
```

### `docs/` — Prácticas del curso

Ahí van todas las prácticas y ejercicios del curso, organizados por módulo. Cada módulo vive en su propia carpeta dentro de `docs/`, con el nombre `Modulo XX` (por ejemplo, `Modulo 01`).

**Cómo agregar el Módulo 1:**

1. Crear la carpeta `docs/Modulo 01/`.
2. Copiar ahí los notebooks y archivos de la práctica correspondientes a ese módulo.
3. Si algún ejercicio del módulo necesita variables de entorno propias, incluí un `.env` dentro de la carpeta de ese ejercicio (no en la raíz del repo).

> **Nota sobre rutas en notebooks (`%%writefile`, archivos generados, etc.):** el directorio de trabajo del kernel no siempre coincide con la carpeta del notebook — JupyterLab nativo lo ubica ahí, pero VSCode conectado a un server remoto (ver [Trabajar con los notebooks en VSCode](#trabajar-con-los-notebooks-en-vscode)) lo deja en la raíz de `docs/`. Esto puede hacer que un notebook cree archivos en la carpeta equivocada (y hasta duplicados, si se corrió antes desde el otro cliente). Si tu módulo tiene notebooks que escriben archivos a disco, agregá una celda al principio que fije el directorio de trabajo, como se hizo en `docs/Modulo 01/Reto_03_pytest.ipynb`:
> ```python
> import os
>
> _target = "Modulo 0X"  # nombre de tu carpeta de módulo
> if os.path.basename(os.getcwd()) != _target and os.path.isdir(_target):
>     os.chdir(_target)
> print("Directorio de trabajo:", os.getcwd())
> ```

> **El mismo problema aplica a scripts `.py` que leen/escriben archivos con rutas relativas** (no solo notebooks). Por ejemplo, `docs/Modulo 01/Proyecto_01/generate_mock_data.py` generaba su carpeta `data/` con `os.makedirs("data/images", ...)`, una ruta relativa al directorio de trabajo — si se ejecutaba desde otro lugar (otra carpeta, otro cliente de Jupyter), `data/` terminaba creándose en el sitio equivocado. El fix fue anclar las rutas a la ubicación del propio archivo en vez del directorio de trabajo:
> ```python
> import os
>
> BASE_DIR = os.path.dirname(os.path.abspath(__file__))
> DATA_DIR = os.path.join(BASE_DIR, "data")
> ```
> y usar `DATA_DIR` (en vez de `"data/..."`) para crear carpetas y guardar archivos. Si tu módulo tiene scripts que generan archivos a disco, aplicá el mismo patrón.
>
> Ojo: esto también aplica a **valores dentro de archivos generados** (no solo a dónde se guardan). `dataset.json` guardaba internamente rutas relativas (`"path": "data/images/factura.png"`) que otros tests leían y abrían directo — al arreglar solo la ubicación del archivo pero no ese valor interno, los tests seguían rompiendo. Terminó igual: generar esos valores con `os.path.join(IMAGES_DIR, ...)` en vez de strings relativos.

> El contenido de `docs/` se versiona en el repositorio (a diferencia de otros templates de curso donde queda en local sin trackear).

## Variables de entorno

- A nivel de repositorio, el `.env` en la raíz es opcional y solo lo usa `docker-compose.yml`.
- Cada módulo/ejercicio dentro de `docs/` puede definir su propio `.env` si lo necesita, independiente del de la raíz.
