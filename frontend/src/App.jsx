import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

// Páginas
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import GeneradorAPA from "./pages/GeneradorAPA";
import TemaDetalle from "./pages/TemaDetalle";

function App() {
  return (
    <Router>
      <Routes>

        {/* Login */}
        <Route path="/" element={<Login />} />

        {/* Admin */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* Usuario */}
        <Route path="/dashboard" element={<UserDashboard />} />
        <Route path="/generador-apa" element={<GeneradorAPA />} />

        {/* Temáticas dinámicas */}
        <Route path="/tema/:nombre" element={<TemaDetalle />} />

        {/* Redirección por defecto */}
        <Route path="*" element={<Navigate to="/" />} />

      </Routes>
    </Router>
  );
}

export default App;