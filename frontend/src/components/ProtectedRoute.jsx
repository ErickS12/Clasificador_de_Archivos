import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, role }) => {
  const token = localStorage.getItem('token');
  const rolUsuario = localStorage.getItem('rol');

  // No hay token → regresa a login
  if (!token) {
    return <Navigate to="/" />;
  }

  // Si se especifica un rol requerido, verificar que coincida
  if (role && rolUsuario !== role) {
    // Redirigir al dashboard correspondiente si no tiene el rol requerido
    return <Navigate to={rolUsuario === 'admin' ? '/admin' : '/dashboard'} />;
  }

  // Tiene token y rol correcto → deja pasar
  return children;
};

export default ProtectedRoute;