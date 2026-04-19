# Frontend — React.js
## ESTADO: 🔲 PENDIENTE — FASE 8

---

## Stack tecnológico

- **React.js** — framework principal (SPA)
- **React Router** — navegación entre vistas
- **Axios** — llamadas HTTP al backend
- **citation-js** — generación de citas APA 7
- **Tailwind CSS** (sugerido) — estilos

## Instalación

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios react-router-dom citation-js
```

---

## Pantallas a implementar

### Pantalla 1 — Login / Register
```
TODO FASE 8:
  - Formulario: username + password
  - POST /register  → crear cuenta
  - POST /auth/login → obtener token JWT
  - Guardar token en localStorage
  - Redirigir según rol (admin → panel admin, user → panel usuario)
```

### Pantalla 2 — Panel de Usuario
```
TODO FASE 8:
  - GET /themes → mostrar árbol de 2 niveles (temáticas y subtemáticas)
  - Botón "Nueva temática" → POST /themes
  - Botón "Nueva subtemática" → POST /themes/{id}/sub
  - Botón "Eliminar" en temática/subtemática vacía → DELETE /themes/{id}
  - Botón "Subir PDF" → POST /upload (con token en header)
  - Para cada archivo: botón "Descargar" y "Eliminar"
  - Checkbox en archivos para selección múltiple (para APA 7)
```

### Pantalla 3 — Generador APA 7
```
TODO FASE 8:
  - Selección múltiple de documentos del árbol
  - Botón "Generar referencias" → POST /apa con lista de IDs
  - Mostrar lista de citas formateadas en APA 7
  - Botón "Copiar al portapapeles"

  Opción alternativa (procesamiento en frontend):
    - Extraer metadatos del PDF con pdf-parse o similar
    - Formatear con citation-js directamente en el navegador
    - Sin necesidad del endpoint POST /apa
```

### Pantalla 4 — Panel de Administrador
```
TODO FASE 8:
  - Tabla de todos los usuarios con sus roles
  - Botón "Dar de alta" → formulario → POST /admin/users
  - Botón "Dar de baja" → DELETE /admin/users/{id}
  - Botón "Editar" → modal con username/password → PUT /admin/users/{id}
  - Para cada usuario: ver su árbol de temáticas
  - Botón "Eliminar temática" (aunque no esté vacía) → DELETE /themes/{id} con rol admin
```

---

## Manejo del token JWT en todas las peticiones

```javascript
// utils/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## Variables de entorno

```env
# frontend/.env
VITE_API_URL=http://localhost:8000

# TODO FASE 7: cambiar a IP del maestro en la LAN
# VITE_API_URL=http://192.168.1.100:8000
```
