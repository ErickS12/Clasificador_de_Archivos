import React from 'react';
import { Search, Bell, LayoutDashboard } from 'lucide-react';

const Navbar = ({ title = "Dashboard", user = "Usuario" }) => {
  return (
    <header className="w-full h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-8 sticky top-0 z-50">
      
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[11px] uppercase font-bold tracking-widest text-slate-400">
        <LayoutDashboard className="w-4 h-4" />
        <span>/</span>
        <span className="text-slate-600 whitespace-nowrap">{title}</span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4 md:gap-6">
        
        {/* Search */}
        <div className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Buscar..." 
            className="bg-slate-50 border border-slate-200 pl-10 pr-4 py-2 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500 w-48 md:w-64 transition-all"
          />
        </div>

        {/* Notifications */}
        <div className="relative cursor-pointer">
          <Bell className="w-5 h-5 text-slate-500" />
          <span className="absolute -top-1 -right-1 bg-red-500 w-2 h-2 rounded-full border-2 border-white"></span>
        </div>

        {/* Avatar */}
        <div className="w-9 h-9 bg-blue-600 rounded-full border-2 border-white shadow-sm ring-1 ring-slate-200 overflow-hidden">
          <img 
            src={`https://ui-avatars.com/api/?name=${user}&bg=2563eb&color=fff`} 
            alt="perfil" 
            className="w-full h-full object-cover"
          />
        </div>

      </div>
    </header>
  );
};

export default Navbar;