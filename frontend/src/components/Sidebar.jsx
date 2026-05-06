import React from 'react';
import { LayoutDashboard, Users, LogOut } from 'lucide-react';
import { NavLink, useNavigate } from "react-router-dom";

const Sidebar = () => {

  
     const navigate = useNavigate();
  
    const handleLogout = () => {
      // limpiar sesión
      localStorage.clear(); // elimina token, rol, etc.
  
      // redirigir sin recargar la app
      navigate("/", { replace: true });
    };

  return (
    <aside className="w-64 bg-[#0f172a] text-slate-300 flex flex-col min-h-screen">
      {/* Logo y Nombre del Sistema */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
        <div className="bg-blue-600 p-2 rounded-lg">
          <LayoutDashboard className="text-white w-6 h-6" />
        </div>
        <div>
          <h2 className="text-white font-bold text-sm leading-tight text-left">Sistema Clasificador</h2>
          <p className="text-[10px] text-slate-400 uppercase tracking-tighter text-left font-semibold">Panel Administrador</p>
        </div>
      </div>

      {/* Menú de Navegación */}
      <nav className="flex-1 p-4 space-y-2">
        <button className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-blue-900/20">
          <Users className="w-5 h-5" />
          Gestión de Usuarios
        </button>
      </nav>

      {/* Perfil inferior y Cerrar Sesión */}
      <div className="p-4 border-t border-slate-700/50 space-y-4">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold ring-2 ring-slate-700">A</div>
          <div className="overflow-hidden text-left">
            <p className="text-xs font-bold text-white truncate uppercase">Administrador</p>
            <p className="text-[10px] text-slate-400 truncate">admin@sistema.com</p>
          </div>
        </div>
        <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-800 rounded-xl text-sm transition-colors text-slate-400 hover:text-white">
          <LogOut className="w-5 h-5" />
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;