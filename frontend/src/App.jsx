import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

// Páginas
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import GeneradorAPA from "./pages/GeneradorAPA";
import TemaDetalle from "./pages/TemaDetalle";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>

        {/* Login */}
        <Route path="/" element={<Login />} />

        {/* Admin (solo admin) */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute role="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Usuario */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute role="usuario">
              <UserDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/generador-apa"
          element={
            <ProtectedRoute role="usuario">
              <GeneradorAPA />
            </ProtectedRoute>
          }
        />

        {/* Temas */}
        <Route
          path="/tema/:nombre"
          element={
            <ProtectedRoute role="usuario">
              <TemaDetalle />
            </ProtectedRoute>
          }
        />

        {/* Redirección */}
        <Route path="*" element={<Navigate to="/" />} />

      </Routes>
    </Router>
  );
}

export default App;