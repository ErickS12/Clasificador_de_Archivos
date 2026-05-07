import React, { useEffect, useState } from 'react';
import Sidebar from '../components/SidebarUsuario';
import Navbar from '../components/Navbar';
import { FileText, Folder, Clock, UploadCloud, FileDown, Eye, Trash2 } from 'lucide-react';

const UserDashboard = () => {

  //Estados para documentos reales y manejo de carga/error
  const [documentos, setDocumentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [subiendo, setSubiendo] = useState(false);


  //Concetamos con el backend para obtener los documentos del usuario
  //Concetamos con el backend para obtener los documentos del usuario
  useEffect(() => {

    const obtenerArchivos = async () => {

      try {

        const token = localStorage.getItem("token");

        const response = await fetch(
          "http://localhost:8000/files",
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        const data = await response.json();

        console.log(data);

        if (!response.ok) {
          throw new Error(data.detail || "Error obteniendo archivos");
        }

        // Convertir árbol a array plano
        const docs = [];

        // Compatibilidad con backend y con la respuesta actual del servidor
        const estructura = data.clasificacion || data.archivos || data.areas || {};

        Object.entries(estructura).forEach(([area, contenido]) => {

          // Archivos directos del área
          if (contenido.files) {

            contenido.files.forEach((archivo, index) => {

              docs.push({
                id: `${area}-${index}`,
                name: archivo,
                tematica: area,
                subarea: null
              });

            });

          }

          // Subáreas
          Object.entries(contenido).forEach(([subarea, subcontenido]) => {

            if (subarea === "files") return;

            if (subcontenido.files) {

              subcontenido.files.forEach((archivo, index) => {

                docs.push({
                  id: `${area}-${subarea}-${index}`,
                  name: archivo,
                  tematica: area,
                  subarea: subarea
                });

              });

            }

          });

        });

        setDocumentos(docs);

      } catch (err) {

        setError(err.message);

      } finally {

        setLoading(false);

      }

    };

    obtenerArchivos();

  }, []);

  //Función para manejar la subida de archivos 
  const subirArchivo = async (e) => {

    const file = e.target.files[0];

    if (!file) return;

    try {

      setSubiendo(true);

      const token = localStorage.getItem("token");

      const formData = new FormData();

      formData.append("archivo", file);

      const response = await fetch(
        "http://localhost:8000/upload",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`
          },
          body: formData
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al subir archivo");
      }

      alert("Archivo subido correctamente");

      // Agregar inmediatamente a tabla
      setDocumentos(prev => [
        ...prev,
        {
          id: Date.now(),
          name: file.name,
          tematica: data.area,
          subarea: data.subarea || null
        }
      ]);

    } catch (err) {

      alert(err.message);

    } finally {

      setSubiendo(false);

    }

  };

  

  return (
    <div className="flex min-h-screen bg-slate-50">

      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">

        <Navbar title="Documentos" user="Usuario" />

        <main className="p-6 md:p-8 w-full max-w-[1400px] mx-auto">

          {/* Tarjetas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-left">

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Total Documentos</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">{documentos.length}</h3>
                <p className="text-green-500 text-[10px] font-bold mt-1">Clasificados automáticamente</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
                <FileText className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Temáticas Científicas</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">{new Set(documentos.map(d => d.tematica)).size}</h3>
                <p className="text-slate-400 text-[10px] font-bold mt-1">Activas</p>
              </div>
              <div className="bg-green-50 p-3 rounded-2xl text-green-600">
                <Folder className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Último Análisis AI</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">Hoy</h3>
                <p className="text-slate-400 text-[10px] font-bold mt-1">15:30 PM</p>
              </div>
              <div className="bg-purple-50 p-3 rounded-2xl text-purple-600">
                <Clock className="w-6 h-6" />
              </div>
            </div>

          </div>

          {/* Subida */}
          <section className="bg-white p-8 rounded-3xl border-2 border-dashed border-slate-200 mb-8 transition-all hover:border-blue-400 hover:bg-blue-50/10 group">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Subir Documentos Científicos</h2>

            <div className="flex flex-col items-center justify-center py-6">
              <div className="bg-slate-50 p-4 rounded-full mb-4 group-hover:bg-blue-50 transition-colors">
                <UploadCloud className="w-10 h-10 text-slate-400 group-hover:text-blue-500 transition-colors" />
              </div>

              <p className="text-sm text-slate-600 font-medium">
                Arrastra tus archivos PDF aquí
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                O haz clic para explorar en tu equipo
              </p>

              <label className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-blue-200 mt-6 transition-all active:scale-95 cursor-pointer">

                {subiendo ? "Subiendo..." : "Seleccionar Archivo"}

                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={subirArchivo}
                />

              </label>
            </div>
          </section>

          {/* Tabla */}
          <section className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden text-left">

            <div className="p-5 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-800">Documentos Recientes</h2>
              <button className="text-[11px] bg-slate-50 text-slate-600 px-3 py-1.5 rounded-lg font-bold hover:bg-slate-100">
                Ver historial completo
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">

                <thead className="bg-slate-50/50 text-slate-500 font-bold uppercase text-[10px] tracking-widest border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-4">Documento</th>
                    <th className="px-6 py-4">Área</th>
                    <th className="px-6 py-4">Subárea</th>
                    <th className="px-6 py-4">Fecha</th>
                    <th className="px-6 py-4 text-center">Acciones</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-50">
                  {loading && (
                    <tr>
                      <td colSpan="5" className="p-6 text-center text-slate-500">
                        Cargando documentos...
                      </td>
                    </tr>
                  )}

                  {error && (
                    <tr>
                      <td colSpan="5" className="p-6 text-center text-red-500">
                        {error}
                      </td>
                    </tr>
                  )}


                  {documentos.map((doc) => (
                    <tr key={doc.id} className="hover:bg-blue-50/20 group">

                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="p-2 bg-red-50 rounded-lg">
                          <FileText className="w-4 h-4 text-red-500" />
                        </div>
                        <span className="font-semibold text-slate-700 truncate max-w-[220px]">
                          {doc.name}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-slate-500 text-xs">{doc.tematica}</td>

                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-blue-100 text-blue-600">
                          {doc.subarea || "-"}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-slate-400 text-xs">{doc.fecha || "-"}</td>

                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="p-2 hover:bg-white rounded-lg text-blue-500">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="p-2 hover:bg-white rounded-lg text-slate-500">
                            <FileDown className="w-4 h-4" />
                          </button>
                          <button className="p-2 hover:bg-white rounded-lg text-red-500">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>

                    </tr>
                  ))}
                </tbody>

              </table>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
};

export default UserDashboard;