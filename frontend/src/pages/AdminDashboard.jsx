import React, { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import {
  Plus,
  Users,
  UserCheck,
  ShieldCheck,
  Eye,
  Edit,
  Lock,
  Trash2,
  Search
} from 'lucide-react';

const AdminDashboard = () => {

  const [busqueda, setBusqueda] = useState("");



  const [crearModal, setCrearModal] = useState(false);

  const [nuevoUsuario, setNuevoUsuario] = useState({
    nombre_usuario: "",
    contrasena: "",
    rol: "user"
  });

  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  const [showEditModal, setShowEditModal] = useState(false);

  const [usuarioEditando, setUsuarioEditando] = useState(null);

  const [editForm, setEditForm] = useState({
    nuevo_nombre_usuario: "",
    nueva_contrasena: "",
    nuevo_rol: ""
  });

  const abrirEditar = (usuario) => {

    setUsuarioEditando(usuario);

    setEditForm({
      nuevo_nombre_usuario: usuario.user,
      nueva_contrasena: "",
      nuevo_rol:
        usuario.rol === "Administrador"
          ? "admin"
          : "user"
    });

    setShowEditModal(true);
  };

  const guardarCambiosUsuario = async () => {

    try {

      const token = localStorage.getItem("token");

      const response = await fetch(
        `http://localhost:8000/admin/users/${usuarioEditando.user}?nuevo_nombre_usuario=${editForm.nuevo_nombre_usuario}&nuevo_rol=${editForm.nuevo_rol}${editForm.nueva_contrasena ? `&nueva_contrasena=${editForm.nueva_contrasena}` : ""}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error");
      }

      setUsuarios(prev =>
        prev.map(u =>
          u.user === usuarioEditando.user
            ? {
              ...u,
              user: editForm.nuevo_nombre_usuario,
              rol:
                editForm.nuevo_rol === "admin"
                  ? "Administrador"
                  : "Usuario"
            }
            : u
        )
      );

      setShowEditModal(false);

      alert("Usuario actualizado");

    } catch (err) {
      alert(err.message);
    }
  };

  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Obtener usuarios reales del backend
  useEffect(() => {
    const fetchUsuarios = async () => {
      try {
        const token = localStorage.getItem("token");

        const response = await fetch("http://localhost:8000/admin/users", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });

        const data = await response.json();

        if (!response.ok) {
          if (response.status === 403) {
            window.location.href = "/dashboard";
            return;
          }
          throw new Error(data.detail || "Error al obtener usuarios");
        }

        // Transformar datos del backend
        const usuariosTransformados = Object.entries(data).map(([username, info], index) => ({
          id: index,
          user: username,
          email: "N/A", // aún no manejas email en backend
          rol: info.rol === "admin" ? "Administrador" : "Usuario",
          estado: info.activo ? "Activo" : "Inactivo"
        }));

        setUsuarios(usuariosTransformados);

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUsuarios();
  }, []);

  const eliminarUsuario = async (username) => {

    if (!window.confirm(`¿Eliminar usuario ${username}?`)) {
      return;
    }

    try {

      const token = localStorage.getItem("token");

      const response = await fetch(
        `http://localhost:8000/admin/users/${username}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al eliminar");
      }

      setUsuarios(prev =>
        prev.filter(u => u.user !== username)
      );

      alert("Usuario eliminado");

    } catch (err) {
      alert(err.message);
    }
  };

  const cambiarEstado = async (usuario) => {

    try {

      const token = localStorage.getItem("token");

      const nuevoEstado = usuario.estado !== "Activo";

      const response = await fetch(
        `http://localhost:8000/admin/users/${usuario.user}/estado?activo=${nuevoEstado}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error");
      }

      setUsuarios(prev =>
        prev.map(u =>
          u.user === usuario.user
            ? {
              ...u,
              estado: nuevoEstado ? "Activo" : "Inactivo"
            }
            : u
        )
      );

    } catch (err) {
      alert(err.message);
    }
  };

  const crearUsuario = async () => {
    try {

      const token = localStorage.getItem("token");

      const response = await fetch(
        `http://localhost:8000/admin/users?nombre_usuario=${nuevoUsuario.nombre_usuario}&contrasena=${nuevoUsuario.contrasena}&rol=${nuevoUsuario.rol}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al crear usuario");
      }

      alert("Usuario creado correctamente");

      // 🔄 Recargar usuarios
      window.location.reload();

    } catch (err) {
      alert(err.message);
    }
  };

  const usuariosFiltrados = usuarios.filter((u) =>
    u.user.toLowerCase().includes(busqueda.toLowerCase())
  );

  return (
    <>
      <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 overflow-hidden">

        {/* SIDEBAR */}
        <Sidebar />

        {/* CONTENT */}
        <div className="flex-1 flex flex-col min-w-0">

          <Navbar title="Administración" user="Admin" />

          <main className="p-8 relative">

            {/* Glow Effects */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-200/40 blur-3xl rounded-full"></div>
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-cyan-100/40 blur-3xl rounded-full"></div>

            {/* HEADER */}
            <div className="relative flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-10">

              <div>

                <p className="text-cyan-600 uppercase tracking-[0.25em] text-xs font-bold mb-2">
                  Panel Administrativo
                </p>

                <h1 className="text-4xl font-bold tracking-tight text-slate-800">
                  Administración de Usuarios
                </h1>

                <p className="text-slate-500 mt-3">
                  Gestiona los usuarios y permisos del sistema.
                </p>
              </div>

              <button
                onClick={() => setCrearModal(true)}
                className="bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] transition-all text-white px-6 py-3 rounded-2xl flex items-center gap-3 font-semibold shadow-2xl shadow-cyan-200"
              >

                <Plus className="w-5 h-5" />

                Crear Usuario
              </button>
            </div>

            {/* Loading y Error */}
            {loading && (
              <div className="mb-6 bg-white/80 border border-slate-200 rounded-2xl px-5 py-4 shadow-sm backdrop-blur-xl text-slate-600">
                Cargando usuarios...
              </div>
            )}

            {error && (
              <div className="mb-6 bg-red-50 border border-red-100 text-red-500 rounded-2xl px-5 py-4 shadow-sm">
                {error}
              </div>
            )}

            {/* STATS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">

              {/* TOTAL */}
              <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

                <div className="absolute top-0 right-0 w-40 h-40 bg-blue-100 blur-3xl rounded-full"></div>

                <div className="relative flex items-center justify-between">

                  <div>

                    <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">
                      Total Usuarios
                    </p>

                    <h3 className="text-5xl font-bold mt-3 text-slate-800">
                      {usuarios.length}
                    </h3>
                  </div>

                  <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">

                    <Users className="w-8 h-8" />

                  </div>
                </div>
              </div>

              {/* ACTIVOS */}
              <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

                <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-100 blur-3xl rounded-full"></div>

                <div className="relative flex items-center justify-between">

                  <div>

                    <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">
                      Usuarios Activos
                    </p>

                    <h3 className="text-5xl font-bold mt-3 text-slate-800">
                      {usuarios.filter(u => u.estado === "Activo").length}
                    </h3>
                  </div>

                  <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">

                    <UserCheck className="w-8 h-8" />

                  </div>
                </div>
              </div>

              {/* ADMINS */}
              <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

                <div className="absolute top-0 right-0 w-40 h-40 bg-purple-100 blur-3xl rounded-full"></div>

                <div className="relative flex items-center justify-between">

                  <div>

                    <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">
                      Administradores
                    </p>

                    <h3 className="text-5xl font-bold mt-3 text-slate-800">
                      {usuarios.filter(u => u.rol === "Administrador").length}
                    </h3>
                  </div>

                  <div className="w-16 h-16 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">

                    <ShieldCheck className="w-8 h-8" />

                  </div>
                </div>
              </div>
            </div>

            {/* TABLE */}
            <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[32px] overflow-hidden shadow-sm">

              {/* SEARCH */}
              <div className="p-6 border-b border-slate-100 bg-white/50">

                <div className="relative max-w-md">

                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                  <input
                    type="text"
                    placeholder="Buscar usuarios..."
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    className="w-full bg-white border border-slate-200 text-slate-700 placeholder:text-slate-400 rounded-2xl py-3 pl-11 pr-4 outline-none focus:ring-2 focus:ring-cyan-400 transition-all"
                  />
                </div>
              </div>

              {/* TABLE */}
              <div className="overflow-x-auto">

                <table className="w-full text-sm">

                  <thead className="border-b border-slate-100 bg-slate-50/80">

                    <tr className="text-slate-500 uppercase text-[11px] tracking-widest">

                      <th className="px-8 py-5 text-left">
                        Usuario
                      </th>

                      <th className="px-8 py-5 text-left">
                        Correo
                      </th>

                      <th className="px-8 py-5 text-left">
                        Rol
                      </th>

                      <th className="px-8 py-5 text-left">
                        Estado
                      </th>

                      <th className="px-8 py-5 text-center">
                        Acciones
                      </th>
                    </tr>
                  </thead>

                  <tbody>

                    {usuariosFiltrados.map((u) => (

                      <tr
                        key={u.id}
                        className="border-b border-slate-100 hover:bg-cyan-50/40 transition-all"
                      >

                        {/* USER */}
                        <td className="px-8 py-5">

                          <div className="flex items-center gap-4">

                            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-200">
                              {u.user[0]}
                            </div>

                            <div>

                              <p className="font-semibold text-slate-800">
                                {u.user}
                              </p>

                              <p className="text-xs text-slate-400">
                                ID: {u.id}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* EMAIL */}
                        <td className="px-8 py-5 text-slate-500">
                          {u.email}
                        </td>

                        {/* ROLE */}
                        <td className="px-8 py-5">

                          <span
                            className={`px-3 py-1 rounded-xl text-xs font-semibold border
                        ${u.rol === "Administrador"
                                ? "bg-purple-50 text-purple-600 border-purple-100"
                                : "bg-blue-50 text-blue-600 border-blue-100"
                              }`}
                          >
                            {u.rol}
                          </span>
                        </td>

                        {/* STATUS */}
                        <td className="px-8 py-5">

                          <span className="px-3 py-1 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-600 border border-emerald-100">
                            {u.estado}
                          </span>
                        </td>

                        {/* ACTIONS */}
                        <td className="px-8 py-5">

                          <div className="flex justify-center gap-3">

                            <button
                              onClick={() => {
                                setUsuarioSeleccionado(u);
                                setModalVisible(true);
                              }}
                              className="w-10 h-10 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-600 flex items-center justify-center transition-all"
                            >

                              <Eye className="w-4 h-4" />

                            </button>

                            <button
                              onClick={() => abrirEditar(u)}
                              className="w-10 h-10 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-500 flex items-center justify-center transition-all"
                            >

                              <Edit className="w-4 h-4" />

                            </button>

                            <button
                              onClick={() => cambiarEstado(u)}
                              className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-all"
                            >

                              <Lock className="w-4 h-4" />

                            </button>

                            <button
                              onClick={() => eliminarUsuario(u.user)}
                              className="w-10 h-10 rounded-xl bg-red-50 hover:bg-red-100 text-red-500 flex items-center justify-center transition-all"
                            >

                              <Trash2 className="w-4 h-4" />

                            </button>

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



   
      {crearModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">

          <div className="w-full max-w-md bg-white rounded-[32px] border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">

            {/* Header */}
            <div className="p-8 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-cyan-50">

              <div className="flex items-center gap-4">

                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-200">

                  <Plus className="w-6 h-6 text-white" />

                </div>

                <div>

                  <h2 className="text-2xl font-bold text-slate-800">
                    Crear Usuario
                  </h2>

                  <p className="text-slate-500 text-sm mt-1">
                    Agrega un nuevo usuario al sistema
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 space-y-5">

              <input
                type="text"
                placeholder="Nombre de usuario"
                value={nuevoUsuario.nombre_usuario}
                onChange={(e) =>
                  setNuevoUsuario({
                    ...nuevoUsuario,
                    nombre_usuario: e.target.value
                  })
                }
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-cyan-400 transition-all"
              />

              <input
                type="password"
                placeholder="Contraseña"
                value={nuevoUsuario.contrasena}
                onChange={(e) =>
                  setNuevoUsuario({
                    ...nuevoUsuario,
                    contrasena: e.target.value
                  })
                }
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-cyan-400 transition-all"
              />

              <select
                value={nuevoUsuario.rol}
                onChange={(e) =>
                  setNuevoUsuario({
                    ...nuevoUsuario,
                    rol: e.target.value
                  })
                }
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-cyan-400 transition-all"
              >
                <option value="user">Usuario</option>
                <option value="admin">Administrador</option>
              </select>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-8 pt-0">

              <button
                onClick={() => setCrearModal(false)}
                className="px-5 py-3 rounded-2xl border border-slate-200 hover:bg-slate-100 text-slate-600 transition-all"
              >
                Cancelar
              </button>

              <button
                onClick={crearUsuario}
                className="bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] transition-all text-white px-6 py-3 rounded-2xl shadow-lg shadow-cyan-200 font-semibold"
              >
                Crear
              </button>
            </div>
          </div>
        </div>
      )}

      {modalVisible && usuarioSeleccionado && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">

          <div className="w-full max-w-md bg-white rounded-[32px] border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">

            {/* Header */}
            <div className="p-8 border-b border-slate-100 bg-gradient-to-r from-cyan-50 to-blue-50">

              <div className="flex items-center gap-4">

                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-200">

                  <Eye className="w-6 h-6 text-white" />

                </div>

                <div>

                  <h2 className="text-2xl font-bold text-slate-800">
                    Información del Usuario
                  </h2>

                  <p className="text-slate-500 text-sm mt-1">
                    Información general del usuario
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 space-y-5">

              <div className="bg-slate-50 rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400 font-bold mb-1">
                  Usuario
                </p>

                <p className="font-semibold text-slate-800">
                  {usuarioSeleccionado.user}
                </p>
              </div>

              <div className="bg-slate-50 rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400 font-bold mb-1">
                  Correo
                </p>

                <p className="font-semibold text-slate-800">
                  {usuarioSeleccionado.email}
                </p>
              </div>

              <div className="bg-slate-50 rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400 font-bold mb-1">
                  Rol
                </p>

                <p className="font-semibold text-slate-800">
                  {usuarioSeleccionado.rol}
                </p>
              </div>

              <div className="bg-slate-50 rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400 font-bold mb-1">
                  Estado
                </p>

                <p className="font-semibold text-emerald-600">
                  {usuarioSeleccionado.estado}
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end p-8 pt-0">

              <button
                onClick={() => setModalVisible(false)}
                className="bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] transition-all text-white px-6 py-3 rounded-2xl shadow-lg shadow-cyan-200 font-semibold"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}


      {showEditModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">

          <div className="w-full max-w-md bg-white rounded-[32px] border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">

            {/* Header */}
            <div className="p-8 border-b border-slate-100 bg-gradient-to-r from-amber-50 to-orange-50">

              <div className="flex items-center gap-4">

                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-400 flex items-center justify-center shadow-lg shadow-amber-200">

                  <Edit className="w-6 h-6 text-white" />

                </div>

                <div>

                  <h2 className="text-2xl font-bold text-slate-800">
                    Editar Usuario
                  </h2>

                  <p className="text-slate-500 text-sm mt-1">
                    Modifica la información del usuario
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 space-y-5">

              <div>

                <label className="text-sm font-semibold text-slate-600 mb-2 block">
                  Usuario
                </label>

                <input
                  type="text"
                  value={editForm.nuevo_nombre_usuario}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      nuevo_nombre_usuario: e.target.value
                    })
                  }
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-amber-400 transition-all"
                />
              </div>

              <div>

                <label className="text-sm font-semibold text-slate-600 mb-2 block">
                  Nueva contraseña
                </label>

                <input
                  type="password"
                  placeholder="Opcional"
                  value={editForm.nueva_contrasena}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      nueva_contrasena: e.target.value
                    })
                  }
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-amber-400 transition-all"
                />
              </div>

              <div>

                <label className="text-sm font-semibold text-slate-600 mb-2 block">
                  Rol
                </label>

                <select
                  value={editForm.nuevo_rol}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      nuevo_rol: e.target.value
                    })
                  }
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 outline-none focus:ring-2 focus:ring-amber-400 transition-all"
                >
                  <option value="user">Usuario</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-8 pt-0">

              <button
                onClick={() => setShowEditModal(false)}
                className="px-5 py-3 rounded-2xl border border-slate-200 hover:bg-slate-100 text-slate-600 transition-all"
              >
                Cancelar
              </button>

              <button
                onClick={guardarCambiosUsuario}
                className="bg-gradient-to-r from-amber-500 to-orange-400 hover:scale-[1.02] active:scale-[0.98] transition-all text-white px-6 py-3 rounded-2xl shadow-lg shadow-amber-200 font-semibold"
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}





    </>
  );

};

export default AdminDashboard;