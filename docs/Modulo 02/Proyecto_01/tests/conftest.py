import os
import sys

# Anclado al directorio del proyecto (no al cwd del proceso que invoca pytest),
# para poder hacer imports planos como `from anonymizer import PIIAnonymizer`.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
