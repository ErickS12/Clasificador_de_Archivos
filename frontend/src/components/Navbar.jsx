import React from 'react';
import {
  LayoutDashboard,
  Bell,
  Search
} from 'lucide-react';

const Navbar = ({ title = "Dashboard" }) => {

  const username = localStorage.getItem("username") || "Usuario";

  return (

    <header className="sticky top-0 z-50 w-full">

      {/* Blur background */}
      <div className="absolute inset-0 bg-white/80 backdrop-blur-2xl border-b border-slate-200"></div>

      <div className="relative h-20 px-4 md:px-8 flex items-center justify-between">

        {/* LEFT */}
        <div className="flex items-center gap-6">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] font-bold">

            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-200">

              <LayoutDashboard className="w-4 h-4 text-white" />

            </div>

            <span className="text-slate-300">/</span>

            <span className="text-slate-700 whitespace-nowrap">
              {title}
            </span>
          </div>


        </div>

        {/* RIGHT */}
        <div className="flex items-center gap-4">


          {/* Divider */}
          <div className="hidden sm:block w-px h-10 bg-slate-200"></div>

          {/* User */}
          <div className="flex items-center gap-3 pl-1">

            {/* Info */}
            <div className="text-right hidden sm:block">

              <p className="text-sm font-bold text-slate-800 uppercase tracking-wide">
                {username}
              </p>

              <p className="text-[11px] text-cyan-600 font-semibold">
                En línea
              </p>
            </div>

            {/* Avatar */}
            <div className="relative">

              <div className="absolute inset-0 bg-cyan-400 blur-xl opacity-30 rounded-full"></div>

              <div className="relative w-11 h-11 rounded-2xl overflow-hidden border-2 border-white shadow-lg ring-1 ring-slate-200">

                <img
                  src={`https://ui-avatars.com/api/?name=${username}&background=2563eb&color=fff`}
                  alt="perfil"
                  className="w-full h-full object-cover"
                />

              </div>

              {/* Online */}
              <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 border-2 border-white rounded-full"></div>

            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;