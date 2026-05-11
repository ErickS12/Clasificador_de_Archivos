import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from "react-router-dom";

import {
  FileText,
  BookOpen,
  LogOut,
  BrainCircuit
} from 'lucide-react';

const SidebarUsuario = () => {

  const navigate = useNavigate();

  const [tematicas, setTematicas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    const obtenerTematicas = async () => {

      try {

        const token = localStorage.getItem("token");

        const response = await fetch(
          "http://localhost:8000/categories",
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Error");
        }

        const areas = Object.keys(data.areas);

        setTematicas(areas);

      } catch (err) {

        console.error(err);

      } finally {

        setLoading(false);

      }
    };

    obtenerTematicas();

  }, []);

  const handleLogout = () => {

    localStorage.clear();

    navigate("/", { replace: true });
  };
  const username = localStorage.getItem("username") || "Usuario";

  return (

  <aside className="w-72 min-w-[280px] bg-gradient-to-b from-[#0f172a] via-[#111827] to-[#0f172a] text-slate-300 flex flex-col min-h-screen sticky top-0 flex-shrink-0 border-r border-slate-800/60 relative overflow-hidden">

    {/* Glow */}
    <div className="absolute top-0 left-0 w-72 h-72 bg-cyan-500/10 blur-3xl rounded-full"></div>
    <div className="absolute bottom-0 right-0 w-72 h-72 bg-blue-600/10 blur-3xl rounded-full"></div>

    {/* HEADER */}
    <div className="relative p-7 flex items-center gap-4 border-b border-slate-800/60 backdrop-blur-xl">

      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-2xl shadow-cyan-500/20">

        <FileText className="text-white w-7 h-7" />

      </div>

      <div className="text-left">

        <h2 className="text-white font-bold text-base leading-tight tracking-tight">
          Sistema Clasificador
        </h2>

        <p className="text-[10px] text-cyan-400 uppercase tracking-[0.25em] font-black mt-1">
          Portal Científico
        </p>

      </div>
    </div>

    {/* NAV */}
    <nav className="relative flex-1 px-4 py-6 space-y-8 overflow-y-auto">

      {/* GENERAL */}
      <div>

        <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.25em] mb-4">
          General
        </p>

        <div className="space-y-2">

          <NavLink
            to="/dashboard"
            end
            className={({ isActive }) =>
              `group relative w-full flex items-center gap-4 px-5 py-3.5 rounded-2xl text-sm transition-all duration-300 overflow-hidden
              ${isActive
                ? "bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-bold shadow-2xl shadow-cyan-500/20"
                : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
              }`
            }
          >

            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/10">

              <FileText className="w-5 h-5" />

            </div>

            <span>
              Documentos
            </span>

          </NavLink>

          <NavLink
            to="/generador-apa"
            className={({ isActive }) =>
              `group relative w-full flex items-center gap-4 px-5 py-3.5 rounded-2xl text-sm transition-all duration-300 overflow-hidden
              ${isActive
                ? "bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-bold shadow-2xl shadow-cyan-500/20"
                : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
              }`
            }
          >

            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/10">

              <BookOpen className="w-5 h-5" />

            </div>

            <span>
              Generador APA
            </span>

          </NavLink>

        </div>
      </div>

      {/* TEMÁTICAS */}
      <div>

        <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.25em] mb-4">
          Temáticas
        </p>

        <div className="space-y-2">

          {loading ? (

            <div className="px-4 py-3 text-sm text-slate-500 bg-slate-800/30 rounded-2xl">
              Cargando...
            </div>

          ) : (

            tematicas.map((tema, index) => (

              <NavLink
                key={index}
                to={`/tema/${tema.toLowerCase().replace(/\s+/g, "-")}`}
                className={({ isActive }) =>
                  `group w-full flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all duration-300
                  ${isActive
                    ? "bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-xl shadow-cyan-500/20"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
                  }`
                }
              >

                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-white/10 flex-shrink-0">

                  <BrainCircuit className="w-4 h-4" />

                </div>

                <span className="truncate font-medium">
                  {tema}
                </span>

              </NavLink>

            ))

          )}

        </div>
      </div>

    </nav>

    {/* FOOTER */}
    <div className="relative p-4 border-t border-slate-800/60 bg-slate-950/20 backdrop-blur-xl">

      {/* USER CARD */}
      <div className="flex items-center gap-4 p-4 rounded-3xl bg-white/5 border border-white/5 mb-3">

        {/* Avatar */}
        <div className="relative">

          <div className="absolute inset-0 bg-cyan-500 blur-xl opacity-30 rounded-full"></div>

          <div className="relative w-12 h-12 rounded-2xl overflow-hidden ring-2 ring-white/10">

            <img
              src={`https://ui-avatars.com/api/?name=${username}&background=2563eb&color=fff`}
              alt="perfil"
              className="w-full h-full object-cover"
            />

          </div>

          {/* Online */}
          <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 border-2 border-[#0f172a] rounded-full"></div>

        </div>

        {/* Info */}
        <div className="overflow-hidden text-left">

          <p className="text-sm font-bold text-white truncate uppercase tracking-wide">
            {username}
          </p>

          <p className="text-[11px] text-cyan-400 font-semibold truncate">
            En línea
          </p>

        </div>

      </div>

      {/* LOGOUT */}
      <button
        onClick={handleLogout}
        className="w-full flex items-center gap-4 px-5 py-3.5 rounded-2xl text-sm font-semibold text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-300 group"
      >

        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 group-hover:bg-red-500/10 transition-all">

          <LogOut className="w-5 h-5 group-hover:translate-x-1 transition-transform" />

        </div>

        <span>
          Cerrar Sesión
        </span>

      </button>

    </div>

  </aside>
);

};

export default SidebarUsuario;