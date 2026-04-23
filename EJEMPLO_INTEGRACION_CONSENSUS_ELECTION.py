"""
EJEMPLO: Como integrar database.py en consensus.py y election.py

Este archivo muestra como conectar el consenso y liderazgo con la BD.
"""

# ═══════════════════════════════════════════════════════════════════════════
# ARCHIVO: master/consensus.py
# ═══════════════════════════════════════════════════════════════════════════

from typing import Dict
from master.database import (
    insertar_voto_consenso,
    obtener_votos_documento,
    actualizar_documento_clasificacion
)

class MotorConsensoDISTRIBUIDO:
    """
    Motor de consenso: 3 workers votan, gana la mayoria (2/3).
    
    NUEVA INTEGRACION CON BD:
    - Registrar cada voto en tabla consenso_votos
    - Consultar votos para calcular resultado final
    - Actualizar documento_clasificacion con resultado
    """
    
    def __init__(self):
        self.nodos = ["node1", "node2", "node3"]
    
    def calcular_consenso(self, documento_id: str, contenido: bytes) -> Dict:
        """
        Flujo:
        1. Enviar contenido a cada worker
        2. NUEVO: Registrar voto en BD (insertar_voto_consenso)
        3. Contar votos por area
        4. Retornar area ganadora
        5. NUEVO: Actualizar documento en BD
        """
        
        votos = {}
        
        # 1+2. Consultar a cada worker y registrar en BD
        for nodo in self.nodos:
            try:
                # Llamar a worker
                resultado = self._consultar_worker(nodo, contenido)
                area = resultado['area']
                confianza = resultado.get('confianza', 0.0)
                
                votos[nodo] = {
                    'area': area,
                    'confianza': confianza
                }
                
                # NUEVO: Guardar voto en BD
                insertar_voto_consenso(
                    documento_id=documento_id,
                    nodo_worker=nodo,
                    area_predicha=area,
                    confianza_worker=confianza
                )
                
                print(f"[CONSENSO] {nodo} voto por {area} (conf: {confianza})")
                
            except Exception as e:
                print(f"[ERROR] Worker {nodo} fallo: {e}")
                votos[nodo] = {'area': 'error', 'confianza': 0.0}
        
        # 3. Calcular mayoria
        areas_votos = [v['area'] for v in votos.values() if v['area'] != 'error']
        if not areas_votos:
            return {'area': 'ERROR', 'confianza': 0.0, 'consenso': False}
        
        # Contar votos
        conteo = {}
        for area in areas_votos:
            conteo[area] = conteo.get(area, 0) + 1
        
        # Area con mas votos (mayoria)
        area_ganadora = max(conteo.keys(), key=lambda x: conteo[x])
        votos_ganador = conteo[area_ganadora]
        confianza_consenso = votos_ganador / len(areas_votos)
        
        print(f"[CONSENSO] Area ganadora: {area_ganadora} ({votos_ganador}/3 votos)")
        
        # 5. NUEVO: Actualizar documento en BD
        # Aqui falta resolver area_ganadora -> subtematica_id
        # (eso lo hace el adapter)
        actualizar_documento_clasificacion(
            documento_id=documento_id,
            subtematica_id=None,  # Se llena desde adapter
            confianza=confianza_consenso
        )
        
        return {
            'area': area_ganadora,
            'confianza': confianza_consenso,
            'votos': votos,
            'consenso': True
        }
    
    def _consultar_worker(self, nodo: str, contenido: bytes) -> Dict:
        """Consultar a worker por HTTP (ya existe en codigo actual)"""
        # ... implementacion existente
        pass


# ═══════════════════════════════════════════════════════════════════════════
# ARCHIVO: shared/election.py
# ═══════════════════════════════════════════════════════════════════════════

import time
from threading import Thread
from master.database import (
    obtener_lider,
    actualizar_lider,
    heartbeat_lider
)

class AlgoritmoLiderazgoDistribuido:
    """
    Algoritmo Bully para eleccion de lider.
    
    NUEVA INTEGRACION CON BD:
    - Registrar lider actual en tabla lider_actual
    - Enviar heartbeat cada 5 segundos
    - Auto-elect si lider muere (sin heartbeat 15 seg)
    
    Tabla: lider_actual (singleton con 1 fila)
    - nodo_id: quien es el lider
    - nodo_hostname: nombre/IP del lider
    - nodo_url: URL para contactar
    - ultimo_heartbeat: timestamp del ultimo latido
    - heartbeat_interval: esperado (default 5s)
    """
    
    def __init__(self, mi_nodo_id: int = 1):
        self.mi_nodo_id = mi_nodo_id
        self.heartbeat_thread = None
        self.corriendo = False
    
    def iniciar_eleccion(self):
        """
        Elegir nuevo lider usando Bully algorithm.
        
        1. Verificar si lider actual esta vivo (heartbeat reciente)
        2. Si murio, hacer eleccion: el nodo con ID mas alto gana
        3. NUEVO: Registrar ganador en BD
        4. Iniciar heartbeat periodico
        """
        
        # 1. Verificar lider actual
        lider_actual = obtener_lider()
        
        if lider_actual and self._lider_vivo(lider_actual):
            print(f"[ELECTION] Lider actual {lider_actual['nodo_id']} esta vivo")
            return
        
        print(f"[ELECTION] Lider murio o no existe. Iniciando eleccion...")
        
        # 2. Bully: nodo con ID mas alto gana
        # Aqui: si yo tengo el ID mas alto, yo gano
        if self.mi_nodo_id >= 3:  # Asumir max 3 nodos
            print(f"[ELECTION] Yo gane! Nodo {self.mi_nodo_id} es el nuevo lider")
            
            # 3. NUEVO: Registrar en BD
            actualizar_lider(
                nodo_id=self.mi_nodo_id,
                nodo_hostname=f"worker{self.mi_nodo_id}",
                nodo_url=f"http://localhost:500{self.mi_nodo_id}"
            )
            
            # 4. Iniciar heartbeat
            self.iniciar_heartbeat()
        else:
            print(f"[ELECTION] Nodo {self.mi_nodo_id} no puede ser lider (ID muy bajo)")
    
    def _lider_vivo(self, lider: Dict) -> bool:
        """
        Verificar si lider esta vivo segun heartbeat.
        
        Regla: si ultimo_heartbeat < hace 15 segundos -> MURIO
        """
        
        import datetime
        ahora = datetime.datetime.utcnow()
        ultimo_hb = datetime.datetime.fromisoformat(
            lider['ultimo_heartbeat'].replace('Z', '+00:00')
        )
        
        segundos_sin_hb = (ahora - ultimo_hb).total_seconds()
        umbral = lider.get('heartbeat_interval', 5) * 3  # 15 segundos por defecto
        
        if segundos_sin_hb > umbral:
            print(f"[ELECTION] Lider murio: {segundos_sin_hb}s sin heartbeat (umbral: {umbral}s)")
            return False
        
        return True
    
    def iniciar_heartbeat(self):
        """
        Iniciar heartbeat: actualizar timestamp cada 5 segundos.
        
        Flujo:
        1. Cada 5 segundos, llamar a heartbeat_lider(mi_nodo_id)
        2. Esto actualiza ultimo_heartbeat en tabla (trigger lo hace automatico)
        3. Si fallo de conexion, otro nodo puede detectarlo
        """
        
        if self.corriendo:
            return
        
        self.corriendo = True
        self.heartbeat_thread = Thread(target=self._loop_heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    def _loop_heartbeat(self):
        """Thread que envia heartbeat cada 5 segundos"""
        
        while self.corriendo:
            try:
                # NUEVO: Enviar heartbeat a BD
                heartbeat_lider(nodo_id=self.mi_nodo_id)
                print(f"[HEARTBEAT] Nodo {self.mi_nodo_id} latiendo... ♥")
                
            except Exception as e:
                print(f"[ERROR HEARTBEAT] {e}")
            
            time.sleep(5)  # Cada 5 segundos
    
    def detener_heartbeat(self):
        """Detener heartbeat cuando el nodo se apaga"""
        self.corriendo = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRACION EN master/main.py
# ═══════════════════════════════════════════════════════════════════════════

"""
Ejemplo de como integrar en main.py:

from fastapi import FastAPI
from shared.election import AlgoritmoLiderazgoDistribuido

app = FastAPI()
liderazgo = AlgoritmoLiderazgoDistribuido(mi_nodo_id=1)  # Este nodo

@app.on_event("startup")
async def startup():
    # Elegir lider al iniciar
    liderazgo.iniciar_eleccion()

@app.on_event("shutdown")
async def shutdown():
    # Detener heartbeat al apagar
    liderazgo.detener_heartbeat()
"""


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRACION EN worker/sync.py
# ═══════════════════════════════════════════════════════════════════════════

"""
Archivo: worker/sync.py

Despues de verificar que el archivo existe localmente:

from master.database import marcar_nodo_verificado

def sincronizar_replicacion(documento_id: str, nodo_origen: str):
    '''
    Sincronizar replica desde nodo_origen.
    
    Flujo:
    1. Recibir archivo desde nodo_origen
    2. Guardar localmente
    3. NUEVO: Llamar marcar_nodo_verificado() para actualizar BD
    '''
    
    # ... codigo de sincronizacion ...
    
    # Despues de confirmar que archivo existe:
    ruta_local = f"../storage/{mi_nodo}/doc_{documento_id}.pdf"
    if os.path.exists(ruta_local):
        # NUEVO: Marcar como verificado en BD
        marcar_nodo_verificado(
            documento_id=documento_id,
            nodo=mi_nodo
        )
        print(f"Nodo {mi_nodo} verificado para documento {documento_id}")
"""


# ═══════════════════════════════════════════════════════════════════════════
# TABLA lider_actual - DIAGRAMA DEL FLUJO
# ═══════════════════════════════════════════════════════════════════════════

"""
FLUJO DE LIDERAZGO:

T=0s  | Nodo 1 inicia
      | → actualizar_lider(1, "worker1", "http://localhost:5001")
      | → tabla: nodo_id=1, ultimo_heartbeat=T0
      | → inicia thread heartbeat

T=5s  | heartbeat_lider(1) 
      | → UPDATE lider_actual SET ultimo_heartbeat=now()
      | → trigger actualizar_heartbeat() actualiza timestamp

T=10s | heartbeat_lider(1)
      | → UPDATE lider_actual SET ultimo_heartbeat=now()

T=15s | Nodo 2 hace check_lider()
      | → obtener_lider() devuelve nodo_id=1, ultimo_heartbeat=(T15-5s)
      | → VIVO! Sigue adelante

T=20s | ERROR: Nodo 1 se cae, no envia heartbeat

T=35s | Nodo 2 hace check_lider()
      | → obtener_lider() devuelve nodo_id=1, ultimo_heartbeat=(T35-20s)
      | → MURIO! (15 segundos sin heartbeat)
      | → Nodo 2 hace eleccion
      | → actualizar_lider(2, "worker2", "http://localhost:5002")
      | → nueva fila: nodo_id=2, elegido_en=T35

T=40s | heartbeat_lider(2)
      | → Nodo 2 es nuevo lider
"""
