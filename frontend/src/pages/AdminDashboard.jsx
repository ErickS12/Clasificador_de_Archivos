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
    <div className="flex min-h-screen bg-slate-50 min-w-0">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <Navbar title="Administración" user="Admin" />

        <main className="p-8">

          {/* Encabezado */}
          <div className="flex justify-between items-end mb-8 text-left">
            <div>
              <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
                Administración de Usuarios
              </h1>
              <p className="text-slate-500 text-sm mt-1">
                Gestiona los usuarios del sistema
              </p>
            </div>

            <button
              onClick={() => setCrearModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm font-bold shadow-lg shadow-blue-200 transition-all active:scale-95"
            >
              <Plus className="w-4 h-4" />
              Crear Usuario
            </button>
          </div>

          {/* Loading y Error */}
          {loading && <p className="mb-4">Cargando usuarios...</p>}
          {error && <p className="mb-4 text-red-500">{error}</p>}

          {/* Estadísticas dinámicas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-left">
            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase">Total Usuarios</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">
                  {usuarios.length}
                </h3>
              </div>
              <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
                <Users className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase">Usuarios Activos</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">
                  {usuarios.filter(u => u.estado === "Activo").length}
                </h3>
              </div>
              <div className="bg-green-50 p-3 rounded-2xl text-green-600">
                <UserCheck className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-xs font-bold uppercase">Administradores</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">
                  {usuarios.filter(u => u.rol === "Administrador").length}
                </h3>
              </div>
              <div className="bg-purple-50 p-3 rounded-2xl text-purple-600">
                <ShieldCheck className="w-6 h-6" />
              </div>
            </div>
          </div>

          {/* Tabla */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">

            {/* Buscador */}
            <div className="p-4 border-b border-slate-100 bg-slate-50/50">
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar usuarios..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="w-full bg-white border border-slate-200 pl-10 pr-4 py-2 rounded-xl text-xs outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto text-left">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b">
                  <tr>
                    <th className="px-6 py-4">Usuario</th>
                    <th className="px-6 py-4">Correo</th>
                    <th className="px-6 py-4">Rol</th>
                    <th className="px-6 py-4">Estado</th>
                    <th className="px-6 py-4 text-center">Acciones</th>
                  </tr>
                </thead>

                <tbody>
                  {usuariosFiltrados.map((u) => (
                    <tr key={u.id} className="hover:bg-blue-50">
                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-xs">
                          {u.user[0]}
                        </div>
                        <span className="font-semibold text-slate-700">
                          {u.user}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-slate-500">
                        {u.email}
                      </td>

                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${u.rol === 'Administrador'
                          ? 'bg-purple-100 text-purple-600'
                          : 'bg-blue-100 text-blue-600'
                          }`}>
                          {u.rol}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-green-100 text-green-600 rounded text-xs font-bold">
                          {u.estado}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => {
                              setUsuarioSeleccionado(u);
                              setModalVisible(true);
                            }}
                          >
                            <Eye className="w-4 h-4 text-blue-500" />
                          </button>
                          <button onClick={() => abrirEditar(u)}>
                            <Edit className="w-4 h-4 text-amber-500" />
                          </button>
                          <button onClick={() => cambiarEstado(u)}>
                            <Lock className="w-4 h-4 text-gray-400" />
                          </button>
                          <button onClick={() => eliminarUsuario(u.user)}>
                            <Trash2 className="w-4 h-4 text-red-500" />
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

      {crearModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

          <div className="bg-white rounded-3xl p-6 w-[400px] shadow-2xl">

            <h2 className="text-xl font-bold mb-6">
              Crear Usuario
            </h2>

            <div className="space-y-4">

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
                className="w-full border border-slate-300 rounded-xl px-4 py-2"
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
                className="w-full border border-slate-300 rounded-xl px-4 py-2"
              />

              <select
                value={nuevoUsuario.rol}
                onChange={(e) =>
                  setNuevoUsuario({
                    ...nuevoUsuario,
                    rol: e.target.value
                  })
                }
                className="w-full border border-slate-300 rounded-xl px-4 py-2"
              >
                <option value="user">Usuario</option>
                <option value="admin">Administrador</option>
              </select>

            </div>

            <div className="flex justify-end gap-3 mt-6">

              <button
                onClick={() => setCrearModal(false)}
                className="px-4 py-2 rounded-xl border"
              >
                Cancelar
              </button>

              <button
                onClick={crearUsuario}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl"
              >
                Crear
              </button>

            </div>

          </div>

        </div>
      )}

      {modalVisible && usuarioSeleccionado && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

          <div className="bg-white rounded-3xl p-6 w-[400px] shadow-2xl">

            <h2 className="text-xl font-bold mb-4">
              Información del Usuario
            </h2>

            <div className="space-y-3 text-sm">

              <div>
                <span className="font-bold">Usuario:</span>{" "}
                {usuarioSeleccionado.user}
              </div>

              <div>
                <span className="font-bold">Correo:</span>{" "}
                {usuarioSeleccionado.email}
              </div>

              <div>
                <span className="font-bold">Rol:</span>{" "}
                {usuarioSeleccionado.rol}
              </div>

              <div>
                <span className="font-bold">Estado:</span>{" "}
                {usuarioSeleccionado.estado}
              </div>

            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => setModalVisible(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl"
              >
                Cerrar
              </button>
            </div>

          </div>
        </div>
      )}

      {showEditModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

          <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl">

            <h2 className="text-xl font-bold mb-6">
              Editar Usuario
            </h2>

            <div className="space-y-4">

              <div>
                <label className="text-sm font-medium">
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
                  className="w-full border rounded-xl px-4 py-2 mt-1"
                />
              </div>

              <div>
                <label className="text-sm font-medium">
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
                  className="w-full border rounded-xl px-4 py-2 mt-1"
                />
              </div>

              <div>
                <label className="text-sm font-medium">
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
                  className="w-full border rounded-xl px-4 py-2 mt-1"
                >
                  <option value="user">Usuario</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>

            </div>

            <div className="flex justify-end gap-3 mt-8">

              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 rounded-xl border"
              >
                Cancelar
              </button>

              <button
                onClick={guardarCambiosUsuario}
                className="bg-blue-600 text-white px-5 py-2 rounded-xl"
              >
                Guardar
              </button>

            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;