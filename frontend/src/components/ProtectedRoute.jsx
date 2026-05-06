import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');

  //No hay token → regresa a login
  if (!token) {
    return <Navigate to="/" />;
  }

  // Sí hay token → deja pasar
  return children;
};

export default ProtectedRoute;