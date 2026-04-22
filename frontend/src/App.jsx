import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

// 1. Importamos las "Páginas" (Vistas completas)
// Asegúrate de que el nombre coincida exactamente con tus archivos en src/pages/
import Login from "./pages/login"; 
import AdminDashboard from "./pages/AdminDashboard";

function App() {
  return (
    <Router>
      <Routes>
        {/* RUTA 1: El Login es la pantalla de inicio (http://localhost:5173/) */}
        <Route path="/" element={<Login />} />
        
        {/* RUTA 2: El Dashboard (http://localhost:5173/admin) */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* RUTA DE SEGURIDAD: Si el usuario escribe una ruta que no existe, 
            lo redirigimos automáticamente al Login */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;