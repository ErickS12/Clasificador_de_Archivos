import React from 'react';
import { Search, Bell, LayoutDashboard } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10">
      {/* Ruta actual (Breadcrumbs) */}
      <div className="flex items-center gap-2 text-[11px] uppercase font-bold tracking-widest text-slate-400">
        <LayoutDashboard className="w-3.5 h-3.5" />
        <span>/</span>
        <span className="text-slate-600">Administración</span>
      </div>

      {/* Buscador y Perfil */}
      <div className="flex items-center gap-6">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Buscar..." 
            className="bg-slate-50 border border-slate-200 pl-10 pr-4 py-2 rounded-xl text-xs outline-none focus:ring-2 focus:ring-blue-500 w-64 transition-all"
          />
        </div>
        <div className="relative cursor-pointer">
            <Bell className="w-5 h-5 text-slate-400" />
            <span className="absolute -top-1 -right-1 bg-red-500 w-2 h-2 rounded-full border-2 border-white"></span>
        </div>
        <div className="w-8 h-8 bg-blue-600 rounded-full border-2 border-white shadow-sm ring-1 ring-slate-200 overflow-hidden">
            <img src="https://ui-avatars.com/api/?name=Admin&bg=2563eb&color=fff" alt="perfil" />
        </div>
      </div>
    </header>
  );
};

export default Navbar;