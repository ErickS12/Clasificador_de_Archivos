<<<<<<< HEAD
Sistema Clasificador Científico - Frontend.

Tecnologías Utilizadas
React 18: Biblioteca principal para la interfaz de usuario.

Vite: Herramienta de construcción para un desarrollo rápido y optimizado.

Tailwind CSS: Framework de CSS para el diseño estilizado y responsivo.

React Router DOM: Gestión de navegación entre el Login y el Dashboard.

Lucide React: Set de iconos vectoriales para una interfaz intuitiva.

Axios: Cliente HTTP para futuras conexiones con el backend de Programación Distribuida


Estructura del Proyecto
Implementamos una estructura modular para separar las responsabilidades del sistema:

Plaintext
src/
├── components/   # Piezas reutilizables (Sidebar, Navbar)
├── pages/        # Vistas completas (Login, AdminDashboard)
├── assets/       # Recursos estáticos (Imágenes, logos)
├── App.jsx       # Director de rutas (Enrutador central)
└── main.jsx      # Punto de entrada de la aplicación

Instalación y Configuración
Para replicar este entorno de desarrollo, se ejecutaron los siguientes comandos:

Creación del proyecto:

Bash
npm create vite@latest frontend -- --template react
Instalación de dependencias clave:

Bash
npm install react-router-dom axios lucide-react
Configuración de estilos:
Instalación de Tailwind CSS para el diseño basado en utilidades.

Avances del Proyecto
Hasta el momento, el sistema cuenta con:

1. Sistema de Autenticación (Login/Registro)
Interfaz dual para inicio de sesión e inicio de registro de investigadores.

Validación básica de coincidencia de contraseñas.

Diseño responsivo con estados dinámicos en React.

2. Panel de Administración (Dashboard)
Sidebar Pro: Navegación lateral con perfil de administrador y cierre de sesión.

Navbar: Barra superior con buscador integrado y notificaciones.

Tarjetas de Estadísticas: Visualización de total de usuarios, usuarios activos y administradores.

Gestión de Usuarios: Tabla dinámica con acciones de visualización, edición, bloqueo y eliminación.

⚙️ Ejecución
Para iniciar el servidor de desarrollo local:

Bash
npm run dev
=======
# Frontend del Clasificador Distribuido

Guia de integracion del cliente web con la API del sistema.

## Stack recomendado

- Vite + React
- React Router
- Axios
- Context API o Zustand para estado de autenticacion

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

## Configuracion de API

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
- Dashboard de usuario para carga, listado, descarga y eliminacion
- Vista de clasificacion con votos por nodo
- Panel administrativo para gestion de usuarios y areas

## Flujo recomendado

1. Usuario inicia sesion y guarda token
2. Navega areas y subareas permitidas
3. Sube PDF y visualiza resultado de clasificacion
4. Consulta arbol de documentos
5. Descarga o elimina documentos segun permisos

## Comandos de desarrollo

```bash
npm install
npm run dev
```

## Consideraciones de red

- En entorno local, usar localhost
- En LAN, configurar VITE_API_URL con la URL del nodo lider
>>>>>>> origin/main
