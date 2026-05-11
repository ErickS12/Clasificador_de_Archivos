import React from 'react';
import { NavLink } from "react-router-dom";
import {
  FileText,
  BookOpen,
  LogOut,
  BrainCircuit,
  Cpu,
  Network,
  MessageSquare,
  Eye as ViewIcon
} from 'lucide-react';

const SidebarUsuario = () => {

  const tematicas = [
    { name: 'Inteligencia Artificial', ruta: 'inteligencia-artificial', icon: <BrainCircuit className="w-4 h-4" /> },
    { name: 'Machine Learning', ruta: 'machine-learning', icon: <Cpu className="w-4 h-4" /> },
    { name: 'Redes Neuronales', ruta: 'redes-neuronales', icon: <Network className="w-4 h-4" /> },
    { name: 'Procesamiento de Lenguaje', ruta: 'procesamiento-lenguaje', icon: <MessageSquare className="w-4 h-4" /> },
    { name: 'Visión Computacional', ruta: 'vision-computacional', icon: <ViewIcon className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 min-w-[260px] bg-[#0f172a] text-slate-300 flex flex-col min-h-screen sticky top-0 flex-shrink-0 border-r border-slate-800">

      {/* HEADER */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
        <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-900/40">
          <FileText className="text-white w-6 h-6" />
        </div>
        <div className="text-left">
          <h2 className="text-white font-bold text-sm leading-tight">
            Sistema Clasificador
          </h2>
          <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
            Portal Científico
          </p>
        </div>
      </div>

      {/* MENÚ */}
      <nav className="flex-1 p-4 space-y-6 overflow-y-auto">

        {/* GENERAL */}
        <div className="space-y-1">

          <NavLink
            to="/dashboard"
            end
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all ${
                isActive
                  ? "bg-blue-600 text-white font-bold shadow-lg shadow-blue-900/20"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
              }`
            }
          >
            <FileText className="w-5 h-5" />
            Documentos
          </NavLink>

          <NavLink
            to="/generador-apa"
            className={({ isActive }) =>
              `w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all ${
                isActive
                  ? "bg-blue-600 text-white font-bold shadow-lg shadow-blue-900/20"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
              }`
            }
          >
            <BookOpen className="w-5 h-5" />
            Generador APA
          </NavLink>

        </div>

        {/* TEMÁTICAS */}
        <div>
          <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">
            Temáticas
          </p>

          <div className="space-y-1">
            {tematicas.map((item, index) => (
              <NavLink
                key={index}
                to={`/tema/${item.ruta}`}
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-[13px] transition-all ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                  }`
                }
              >
                <span>{item.icon}</span>
                <span className="truncate">{item.name}</span>
              </NavLink>
            ))}
          </div>
        </div>

      </nav>

      {/* FOOTER */}
      <div className="p-4 border-t border-slate-700/50 bg-[#0f172a]">

        <div className="flex items-center gap-3 px-2 py-3 bg-slate-800/30 rounded-2xl mb-2">
          <div className="w-9 h-9 bg-blue-500 rounded-xl flex items-center justify-center text-white text-xs font-black">
            UD
          </div>
          <div className="overflow-hidden text-left">
            <p className="text-xs font-bold text-white truncate">
              Usuario Demo
            </p>
            <p className="text-[10px] text-slate-500 truncate">
              usuario@demo.com
            </p>
          </div>
        </div>

        <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-red-500/10 rounded-xl text-sm font-bold text-slate-400 hover:text-red-400 transition-all group">
          <LogOut className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          Cerrar Sesión
        </button>

      </div>
    </aside>
  );
};

export default SidebarUsuario;