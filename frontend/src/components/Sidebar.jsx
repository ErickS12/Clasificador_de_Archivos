import React from 'react';
import { LayoutDashboard, Users, LogOut } from 'lucide-react';
import { useNavigate } from "react-router-dom";

const Sidebar = () => {

  const navigate = useNavigate();

  // 🔥 Obtener datos reales
  const username = localStorage.getItem("username") || "Admin";
  const rol = localStorage.getItem("rol") || "admin";

  const handleLogout = () => {

    localStorage.clear();

    navigate("/", { replace: true });
  };

  return (
  <aside className="w-72 min-h-screen bg-gradient-to-b from-[#0b1120] via-[#111827] to-[#0f172a] border-r border-white/10 text-slate-300 flex flex-col relative overflow-hidden">

    {/* Glow Effects */}
    <div className="absolute top-[-100px] right-[-80px] w-64 h-64 bg-cyan-500/10 blur-3xl rounded-full"></div>
    <div className="absolute bottom-[-120px] left-[-80px] w-64 h-64 bg-blue-500/10 blur-3xl rounded-full"></div>

    {/* LOGO */}
    <div className="relative p-6 border-b border-white/10">

      <div className="flex items-center gap-4">

        {/* Icon */}
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-2xl shadow-cyan-500/20">

          <LayoutDashboard className="text-white w-7 h-7" />

        </div>

        {/* Text */}
        <div className="text-left">

          <h2 className="text-white font-bold text-lg leading-tight tracking-tight">
            Sistema Clasificador
          </h2>

          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-400 font-semibold mt-1">
            Panel Administrador
          </p>
        </div>
      </div>
    </div>

    {/* NAVIGATION */}
    <nav className="relative flex-1 p-5">

      <div className="mb-4 px-3">

        <p className="text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold">
          Navegación
        </p>
      </div>

      {/* ACTIVE ITEM */}
      <button className="group w-full flex items-center justify-between px-4 py-4 rounded-2xl bg-gradient-to-r from-blue-500/20 to-cyan-400/10 border border-cyan-400/10 hover:border-cyan-400/20 transition-all shadow-xl shadow-cyan-500/5">

        <div className="flex items-center gap-4">

          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">

            <Users className="w-5 h-5 text-white" />

          </div>

          <div className="text-left">

            <p className="text-white font-semibold text-sm">
              Gestión de Usuarios
            </p>

            <p className="text-[11px] text-slate-400 mt-0.5">
              Administración del sistema
            </p>
          </div>
        </div>

        <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.8)]"></div>
      </button>
    </nav>

    {/* PROFILE */}
    <div className="relative p-5 border-t border-white/10 backdrop-blur-xl">

      {/* User Card */}
      <div className="bg-white/5 border border-white/10 rounded-3xl p-4 mb-4">

        <div className="flex items-center gap-4">

          {/* Avatar */}
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-red-500 to-orange-400 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-red-500/20">

            {username.charAt(0).toUpperCase()}

          </div>

          {/* Info */}
          <div className="overflow-hidden text-left">

            <p className="text-sm font-bold text-white truncate uppercase tracking-wide">
              {username}
            </p>

            <p className="text-xs text-slate-400 mt-1">
              {rol === "admin" ? "Administrador" : "Usuario"}
            </p>
          </div>
        </div>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full flex items-center gap-4 px-4 py-4 rounded-2xl bg-red-500/5 hover:bg-red-500/10 border border-red-400/10 hover:border-red-400/20 transition-all group"
      >

        <div className="w-11 h-11 rounded-xl bg-red-500/10 group-hover:bg-red-500/20 flex items-center justify-center transition-all">

          <LogOut className="w-5 h-5 text-red-400" />

        </div>

        <div className="text-left">

          <p className="text-sm font-semibold text-white">
            Cerrar Sesión
          </p>

          <p className="text-[11px] text-slate-500">
            Salir del panel
          </p>
        </div>
      </button>
    </div>
  </aside>
);
};

export default Sidebar;