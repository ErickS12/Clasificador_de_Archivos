import React from 'react';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import { Plus, Users, UserCheck, ShieldCheck, Eye, Edit, Lock, Trash2, Search } from 'lucide-react';

const AdminDashboard = () => {
  // Simulación de datos (Estado inicial)
  const usuarios = [
    { id: 1, user: 'jperez', email: 'jperez@universidad.edu', rol: 'Usuario', estado: 'Activo', fecha: '2024-01-15', acceso: '2024-03-20 14:30' },
    { id: 2, user: 'mgarcia', email: 'mgarcia@universidad.edu', rol: 'Usuario', estado: 'Activo', fecha: '2024-02-01', acceso: '2024-03-19 10:15' },
    { id: 3, user: 'admin', email: 'admin@sistema.com', rol: 'Administrador', estado: 'Activo', fecha: '2023-12-01', acceso: '2024-03-21 09:00' },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50  min-w-0">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Navbar title="Administración" user="Admin" />

        <main className="p-8">
          {/* Encabezado de sección */}
          <div className="flex justify-between items-end mb-8 text-left">
            <div>
              <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Administración de Usuarios</h1>
              <p className="text-slate-500 text-sm mt-1">Gestiona los usuarios del sistema</p>
            </div>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold shadow-lg shadow-blue-200 transition-all active:scale-95">
              <Plus className="w-4 h-4" /> Crear Usuario
            </button>
          </div>

          {/* Tarjetas de Estadísticas [Paso 1] */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-left">
            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">Total Usuarios</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">4</h3>
                <p className="text-green-500 text-[10px] font-bold mt-1">+2 este mes</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-2xl text-blue-600"><Users className="w-6 h-6" /></div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">Usuarios Activos</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">3</h3>
                <p className="text-slate-400 text-[10px] font-bold mt-1">En línea</p>
              </div>
              <div className="bg-green-50 p-3 rounded-2xl text-green-600"><UserCheck className="w-6 h-6" /></div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">Administradores</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">1</h3>
                <p className="text-purple-500 text-[10px] font-bold mt-1">Con privilegios</p>
              </div>
              <div className="bg-purple-50 p-3 rounded-2xl text-purple-600"><ShieldCheck className="w-6 h-6" /></div>
            </div>
          </div>

          {/* Tabla de Usuarios [Paso 2] */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            {/* Buscador interno de la tabla */}
            <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                    <input type="text" placeholder="Buscar usuarios..." className="w-full bg-white border border-slate-200 pl-10 pr-4 py-2 rounded-xl text-xs outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
            </div>

            <div className="overflow-x-auto text-left">
              <table className="w-full text-sm">
                <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase text-[10px] tracking-widest border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-4">Usuario</th>
                    <th className="px-6 py-4">Correo</th>
                    <th className="px-6 py-4">Rol</th>
                    <th className="px-6 py-4">Estado</th>
                    <th className="px-6 py-4 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {usuarios.map((u) => (
                    <tr key={u.id} className="hover:bg-blue-50/30 transition-colors group">
                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-[10px] uppercase">{u.user[0]}</div>
                        <span className="font-semibold text-slate-700">{u.user}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-500 font-medium">{u.email}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase ${u.rol === 'Administrador' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}`}>
                          {u.rol}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 bg-green-100 text-green-600 rounded-lg text-[10px] font-black uppercase">
                          {u.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                          <button title="Ver" className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-blue-500 transition-all"><Eye className="w-4 h-4" /></button>
                          <button title="Editar" className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-amber-500 transition-all"><Edit className="w-4 h-4" /></button>
                          <button title="Bloquear" className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-slate-400 transition-all"><Lock className="w-4 h-4" /></button>
                          <button title="Eliminar" className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-red-500 transition-all"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;