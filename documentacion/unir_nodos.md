# Guía: Cómo unir nodos del clúster

Objetivo
- Explicar paso a paso cómo conectar varias máquinas que ejecutan este proyecto para formar un clúster.

Resumen rápido
- El módulo `shared/cluster_config.py` usa variables de entorno para configurar los nodos. No es necesario editar el código si usas `CLUSTER_NODES_JSON` o `CLUSTER_NODE_<id>_URL`.

Requisitos previos (en cada máquina)
- Mismo código fuente (mismo commit) y dependencias: `requirements.txt` instalado.
- Python y dependencias iguales (recomiendo crear un `venv`).
- Reloj sincronizado (NTP).
- Acceso de red entre máquinas (IP/hostname & puertos abiertos).
- Firewall/antivirus configurado para permitir el puerto de la aplicación.
- Si usas DB/servicios compartidos, las credenciales y accesos deben funcionar desde cada nodo.

Puertos y binding
- Asegúrate de que la aplicación escuche en `0.0.0.0` para aceptar conexiones externas (no `localhost`).
- Abre el puerto configurado (ej. `5001`, `5002`, `8000`) en el firewall y, si aplica, en el router (port-forward).

Opciones de configuración de nodos
1. Usar `CLUSTER_NODES_JSON` (recomendado para despliegues reproducibles):
   - Valor ejemplo:

```json
[{"id":1,"url":"http://192.168.1.10:5001"},{"id":2,"url":"http://192.168.1.11:5001"},{"id":3,"url":"http://192.168.1.12:5001"}]
```
   - Exportar en PowerShell:

```powershell
$env:CLUSTER_NODES_JSON='[{"id":1,"url":"http://192.168.1.10:5001"},{"id":2,"url":"http://192.168.1.11:5001"}]'
python main.py
```

2. Usar variables `CLUSTER_NODE_1_URL`, `CLUSTER_NODE_2_URL`, ...

```powershell
$env:CLUSTER_NODE_1_URL='http://192.168.1.10:5001'
$env:CLUSTER_NODE_2_URL='http://192.168.1.11:5001'
python main.py
```

3. Editar `DEFAULT_NODES` en `shared/cluster_config.py` (no recomendado para producción porque requiere cambiar código en cada máquina).

Checklist por máquina (paso a paso)
1. Clonar el repositorio y posicionarse en la rama/commit deseado.

```bash
git clone <repo> && cd Clasificador_de_Archivos
git checkout <commit-o-rama>
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Configurar la URL del nodo (usar `CLUSTER_NODES_JSON` o `CLUSTER_NODE_<id>_URL`).
3. Asegurar binding a `0.0.0.0` en el archivo de arranque (por ejemplo, si se usa `app.run(host='127.0.0.1')`, cambiar a `0.0.0.0`).
4. Abrir/permitir puerto en firewall.
5. Iniciar la aplicación:

```powershell
python main.py
```

6. Desde otra máquina, probar conectividad:

```bash
curl -v http://192.168.1.10:5001/health  # o el endpoint de prueba
```

Pruebas y verificación
- Comprobar que `obtener_nodos_cluster()` devuelve la lista esperada (puedes añadir un `print()` temporal o endpoint de diagnóstico).
- Revisar logs para errores de conexión.

Seguridad y despliegue por Internet
- No expongas puertos directamente a internet sin TLS y autenticación.
- Usar VPN o túnel seguro (SSH tunnel, WireGuard) o poner un proxy HTTPS delante.
- Considerar autenticación mutua o tokens entre nodos.

Problemas comunes y soluciones
- "No responde": verificar firewall y que la app escucha en `0.0.0.0`.
- "Dirección inválida": revisar que la URL incluya esquema `http://` o `https://`.
- "Variables de entorno no aplicadas": asegurarse de exportarlas en la misma sesión que arranca la app.

Ejemplos de script de arranque (opcional)
- `run_cluster.ps1` (PowerShell) ejemplo para un nodo:

```powershell
# run_cluster.ps1
$env:CLUSTER_NODE_1_URL='http://192.168.1.10:5001'
$env:CLUSTER_NODE_2_URL='http://192.168.1.11:5001'
python main.py
```

Notas finales
- Es recomendable mantener la misma versión de código y dependencias en todas las máquinas.
- Para roles distintos (por ejemplo, un nodo maestro que coordina borrados y nodos worker que solo procesan), puedes mantener la base de código pero activar/desactivar módulos mediante variables de entorno o flags de configuración.

Si quieres, creo también `run_cluster.ps1` y `run_cluster.sh` de ejemplo y añado un endpoint de diagnóstico en `master/main.py` para listar nodos en ejecución.
