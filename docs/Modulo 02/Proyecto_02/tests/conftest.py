import os
import sys

# Anclado al directorio src/ del proyecto (no al cwd del proceso que invoca pytest),
# para poder hacer imports planos como `from anonymizer import PIIAnonymizer`.
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_DIR)
