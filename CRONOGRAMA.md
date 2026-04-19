# Cronograma de Desarrollo
# Clasificador Distribuido de Archivos Científicos

Leyenda:
  ✅ Implementado y funcional
  🔲 Pendiente
  ⚠️  Implementado parcialmente (stub con TODO)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 1 — Sistema Base (MVP)                    ✅ COMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Levantar worker con FastAPI en :5001
  ✅ worker/extractor.py — extraer texto PDF con PyMuPDF
  ✅ worker/classifier.py — TF-IDF + LogisticRegression
  ✅ Endpoint POST /process en el worker
  ✅ Maestro básico: recibir PDF y reenviar al worker
  ✅ Guardar archivo en storage/node1/
  ✅ Guardar metadatos en JSON
  ✅ Endpoint GET /files — árbol de archivos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 2 — Distribución                          ✅ COMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Workers en :5001, :5002, :5003
  ✅ master/consensus.py — envía a los 3, mayoría de votos
  ✅ Replicación: copiar en node1/, node2/, node3/
  ✅ Metadatos con campo "nodes"
  ✅ Sistema continúa si un worker está caído

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 3 — Autenticación y Roles                 ✅ COMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ master/auth.py — hash PBKDF2 + tokens UUID
  ✅ POST /register — primer usuario = admin automático
  ✅ POST /login — devuelve token
  ✅ POST /logout — invalida token
  ✅ Todos los endpoints protegidos con Bearer token
  ✅ Permisos separados: usuario regular vs administrador
  ✅ master/gateway.py — validación + LoggingMiddleware

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 4 — Migración a Supabase                  🔲 PENDIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔲 Crear proyecto en Supabase
  🔲 Diseñar y crear tablas: usuarios, tematicas, documentos
  🔲 Configurar ON DELETE CASCADE en temáticas
  🔲 master/database.py — funciones de acceso a Supabase
  🔲 Migrar auth.py → tokens JWT de Supabase
  🔲 Migrar JSON de usuarios → tabla usuarios
  🔲 Migrar JSON de archivos → tabla documentos
  🔲 pip install supabase + python-dotenv
  🔲 Configurar .env con SUPABASE_URL y SUPABASE_KEY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 5 — Jerarquía y Control Administrativo    ✅/🔲 PARCIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Árbol de 2 niveles: temáticas y subtemáticas
  ✅ POST /areas — crear temática nivel 1
  ✅ POST /areas/{area}/sub — crear subtemática nivel 2
  ✅ DELETE /areas — usuario: solo si vacía
  ✅ DELETE /areas admin: mueve docs a General (con JSON)
  ✅ CRUD admin de usuarios (alta, baja, modificar)
  ✅ DELETE /document — borra de 3 nodos + JSON
  🔲 Borrado en 2 pasos real (requiere Supabase — Fase 4)
      master/deletion_coordinator.py — stub listo
  🔲 POST /delete-files en worker — stub listo
  🔲 ON DELETE CASCADE en Supabase tras borrado físico

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 6 — Tolerancia a Fallos y Sync            ✅/🔲 PARCIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Descarga con fallback: node1 → node2 → node3
  ✅ Consenso ignora workers caídos automáticamente
  🔲 Startup Sync al arrancar cada worker
      worker/sync.py — stub listo
  🔲 Endpoint GET /internal/file en maestro
      (para que el worker descargue archivos faltantes)
  🔲 Probar: apagar worker, subir archivos, encender, verificar sync

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 7 — Despliegue Físico en LAN              🔲 PENDIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔲 Configurar hotspot compartido entre las 4 laptops
  🔲 Asignar IPs fijas a cada laptop en la red
  🔲 Cambiar IPs en consensus.py (localhost → IPs reales)
  🔲 Levantar workers con --host 0.0.0.0
  🔲 Abrir puertos 5001-5003 y 8000 en firewall de cada laptop
  🔲 Cambiar VITE_API_URL en frontend a IP del maestro
  🔲 Probar subida de PDF end-to-end en la red real
  🔲 Probar tolerancia: desconectar una laptop físicamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 8 — Frontend React                        🔲 PENDIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔲 Crear proyecto con Vite + React
  🔲 Pantalla Login / Register
  🔲 Manejo de token JWT en todas las peticiones (axios interceptor)
  🔲 Panel de usuario: árbol de temáticas navegable
  🔲 Subida de PDF con feedback de clasificación y votos
  🔲 Descarga y eliminación de documentos
  🔲 Panel administrador: gestión de usuarios y temáticas
  🔲 Generador APA 7 (selección múltiple + citation-js)
  🔲 master/apa.py — stub listo para el endpoint POST /apa

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 9 — Pulido Final                          🔲 PENDIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔲 Manejo de errores consistente en todos los endpoints
  🔲 Pruebas de integración básicas (subir PDF end-to-end)
  🔲 Revisar consistencia de respuestas del Adaptador
  🔲 Documentar endpoints (FastAPI /docs automático)
  🔲 README final con instrucciones de ejecución completas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESUMEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Fases completas:    1, 2, 3
  Fases parciales:    5 (falta borrado real), 6 (falta sync)
  Fases pendientes:   4, 7, 8, 9

  Archivos con stubs listos para implementar:
    master/database.py          ← Fase 4
    master/deletion_coordinator.py ← Fase 5
    worker/sync.py              ← Fase 6
    master/apa.py               ← Fase 8
    frontend/README_FRONTEND.md ← Fase 8
