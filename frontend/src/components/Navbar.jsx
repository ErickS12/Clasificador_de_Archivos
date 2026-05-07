import React from 'react';
import { LayoutDashboard } from 'lucide-react';

const Navbar = ({ title = "Dashboard" }) => {

  // 🔥 Usuario real
  const username = localStorage.getItem("username") || "Usuario";

  return (
    <header className="w-full h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-8 sticky top-0 z-50">

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[11px] uppercase font-bold tracking-widest text-slate-400">

        <LayoutDashboard className="w-4 h-4" />

        <span>/</span>

        <span className="text-slate-600 whitespace-nowrap">
          {title}
        </span>

      </div>

      {/* Right side */}
      <div className="flex items-center gap-4 md:gap-6">

        {/* Usuario */}
        <div className="flex items-center gap-3">

          <div className="text-right hidden sm:block">
            <p className="text-sm font-bold text-slate-700 uppercase">
              {username}
            </p>

            <p className="text-[11px] text-slate-400">
              En línea
            </p>
          </div>

          {/* Avatar */}
          <div className="w-9 h-9 bg-blue-600 rounded-full border-2 border-white shadow-sm ring-1 ring-slate-200 overflow-hidden">

            <img
              src={`https://ui-avatars.com/api/?name=${username}&bg=2563eb&color=fff`}
              alt="perfil"
              className="w-full h-full object-cover"
            />

          </div>

        </div>

      </div>

    </header>
  );
};

export default Navbar;