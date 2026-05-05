# Frontend del Clasificador Distribuido

Guía de integración del cliente web con la API del sistema.

## Stack recomendado

- Vite + React
- React Router
- Axios
- Context API o Zustand para estado de autenticación

## Estructura sugerida

```text
src/
  api/
    client.js
  auth/
    auth-context.jsx
    auth-guard.jsx
  pages/
    Login.jsx
    Register.jsx
    Dashboard.jsx
    AdminUsers.jsx
  components/
    UploadForm.jsx
    FileTree.jsx
    VoteSummary.jsx
    Navbar.jsx
```

## Configuración de API

Archivo recomendado en src/api/client.js:

```js
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

Archivo .env del frontend:

```text
VITE_API_URL=http://localhost:8000
```

## Vistas funcionales

- Login y registro
- Dashboard de usuario para carga, listado, descarga y eliminación
- Vista de clasificación con votos por nodo
- Panel administrativo para gestión de usuarios

## Flujo recomendado

1. Usuario inicia sesion y guarda token
2. Consulta categorias globales disponibles
3. Sube PDF y visualiza resultado de clasificación
4. Consulta listado de documentos
5. Descarga o elimina documentos segun permisos

## Comandos de desarrollo

```bash
npm install
npm run dev
```

## Consideraciones de red

- En entorno local, usar localhost
- En LAN, configurar VITE_API_URL con la URL del nodo lider

