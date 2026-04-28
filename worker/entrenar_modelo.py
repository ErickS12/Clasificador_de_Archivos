"""
Script para entrenar y guardar el modelo de clasificación.

Uso:
    python worker/entrenar_modelo.py

Esto va a entrenar el modelo desde cero y guardarlo en:
    worker/modelo_clasificador.pkl

Si el modelo ya existe, lo sobrescribe.
"""

import os
import sys

# Agregar parent directory al path para importar classifier
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.classifier import _entrenar_modelo, MODELO_RUTA


def main():
    print("=" * 60)
    print("Entrenamiento de Modelo de Clasificación")
    print("=" * 60)
    
    # Si el modelo existe, advertir al usuario
    if os.path.exists(MODELO_RUTA):
        print(f"\n[ADVERTENCIA] El modelo ya existe en: {MODELO_RUTA}")
        respuesta = input("¿Deseas sobrescribirlo? (s/n): ").strip().lower()
        if respuesta != 's':
            print("Operación cancelada.")
            return
    
    print("\n[INFO] Iniciando entrenamiento...")
    pipeline = _entrenar_modelo()
    
    print(f"\n[EXITO] Modelo entrenado y guardado en: {MODELO_RUTA}")
    print("[INFO] El modelo será cargado automáticamente en el siguiente inicio del worker.")
    

if __name__ == "__main__":
    main()
