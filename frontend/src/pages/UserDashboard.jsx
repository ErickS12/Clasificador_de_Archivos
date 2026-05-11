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

        if (!response.ok) {
          throw new Error(data.detail || "Error obteniendo archivos");
        }

        const estructura = data.clasificacion || {};

        const docs = [];

        Object.entries(estructura).forEach(([area, contenido]) => {

          // archivos directos del área
          (contenido.files || []).forEach((archivo) => {
            docs.push({
              id: archivo.id,
              name: archivo.nombre,
              tematica: area,
              subarea: archivo.subarea || null,
              fecha: archivo.fecha
            });
          });

          // subáreas
          Object.entries(contenido).forEach(([key, value]) => {

            if (key === "files") return;
            if (!value?.files) return;

            value.files.forEach((archivo) => {
              docs.push({
                id: archivo.id,
                name: archivo.nombre,
                tematica: area,
                subarea: key,
                fecha: archivo.fecha
              });
            });

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

      // 🔥 YA NO se inventa ID
      setDocumentos(prev => [
        ...prev,
        {
          id: data.id,
          name: file.name,
          tematica: data.area,
          subarea: data.subarea || null,
          fecha: new Date().toISOString()
        }
      ]);

    } catch (err) {

      alert(err.message);

    } finally {

      setSubiendo(false);

    }

  };

  const verDocumento = async (doc) => {
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams();

      params.append("nombre_archivo", doc.name);
      params.append("area", doc.tematica);
      if (doc.subarea) {
        params.append("subarea", doc.subarea);
      }

      const response = await fetch(`http://localhost:8000/download?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || "Error al obtener el documento");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => window.URL.revokeObjectURL(url), 60000);
    } catch (err) {
      alert(err.message);
    }
  };

  //Función Descargar Documento: Similar a verDocumento pero con un endpoint de descarga directa
  const descargarDocumento = async (doc) => {
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams();

      params.append("nombre_archivo", doc.name);
      params.append("area", doc.tematica);
      if (doc.subarea) {
        params.append("subarea", doc.subarea);
      }

      const response = await fetch(`http://localhost:8000/download?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || "Error al descargar el documento");
      }

      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = doc.name;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => window.URL.revokeObjectURL(link.href), 60000);
    } catch (err) {
      alert(err.message);
    }
  };

  //Función Eliminar Documento: Envía una solicitud DELETE al backend para eliminar el documento y luego actualiza el estado local
  const eliminarDocumento = async (doc) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/document?nombre_archivo=${encodeURIComponent(doc.name)}&area=${encodeURIComponent(doc.tematica)}&subarea=${encodeURIComponent(doc.subarea || "")}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Error al eliminar archivo");
      }
      //Quitar el documento eliminado del estado local
      setDocumentos(prev => prev.filter(d => d.id !== doc.id));
      alert("Archivo eliminado correctamente");
    } catch (err) {
      alert(err.message);
    }

  };

  return (
  <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 overflow-hidden">

    <Sidebar />

    <div className="flex-1 flex flex-col min-w-0">

      <Navbar title="Documentos" user="Usuario" />

      <main className="p-6 md:p-8 w-full max-w-[1400px] mx-auto relative">

        {/* Glow Effects */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-100/40 blur-3xl rounded-full pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-100/40 blur-3xl rounded-full pointer-events-none"></div>

        {/* HEADER */}
        <div className="relative mb-8 text-left">

          <p className="text-cyan-600 uppercase tracking-[0.25em] text-xs font-bold mb-2">
            Panel Principal
          </p>

          <h1 className="text-4xl font-bold tracking-tight text-slate-800">
            Gestión de Documentos
          </h1>

          <p className="text-slate-500 mt-3 max-w-2xl">
            Administra, clasifica y visualiza documentos científicos de manera inteligente.
          </p>

        </div>

        {/* TARJETAS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-left">

          {/* TOTAL DOCS */}
          <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[30px] p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

            <div className="absolute top-0 right-0 w-40 h-40 bg-blue-100 blur-3xl rounded-full"></div>

            <div className="relative flex items-center justify-between">

              <div>

                <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">
                  Total Documentos
                </p>

                <h3 className="text-5xl font-bold text-slate-800 mt-3">
                  {documentos.length}
                </h3>

                <p className="text-emerald-500 text-[11px] font-bold mt-2">
                  Clasificados automáticamente
                </p>

              </div>

              <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-sm">

                <FileText className="w-8 h-8" />

              </div>
            </div>
          </div>

          {/* TEMÁTICAS */}
          <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[30px] p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

            <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-100 blur-3xl rounded-full"></div>

            <div className="relative flex items-center justify-between">

              <div>

                <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">
                  Temáticas Científicas
                </p>

                <h3 className="text-5xl font-bold text-slate-800 mt-3">
                  {new Set(documentos.map(d => d.tematica)).size}
                </h3>

                <p className="text-slate-400 text-[11px] font-bold mt-2">
                  Activas
                </p>

              </div>

              <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shadow-sm">

                <Folder className="w-8 h-8" />

              </div>
            </div>
          </div>

          {/* AI */}
          <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[30px] p-6 relative overflow-hidden shadow-sm hover:shadow-xl transition-all">

            <div className="absolute top-0 right-0 w-40 h-40 bg-purple-100 blur-3xl rounded-full"></div>

            <div className="relative flex items-center justify-between">

              <div>

                <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">
                  Último Análisis AI
                </p>

                <h3 className="text-3xl font-bold text-slate-800 mt-3">
                  Hoy
                </h3>

                <p className="text-slate-400 text-[11px] font-bold mt-2">
                  15:30 PM
                </p>

              </div>

              <div className="w-16 h-16 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600 shadow-sm">

                <Clock className="w-8 h-8" />

              </div>
            </div>
          </div>

        </div>

        {/* SUBIDA */}
        <section className="relative bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[32px] mb-8 overflow-hidden shadow-sm">

          <div className="absolute top-0 right-0 w-72 h-72 bg-cyan-100/30 blur-3xl rounded-full"></div>

          <div className="relative p-8 md:p-10 text-center">

            <div className="inline-flex items-center justify-center w-24 h-24 rounded-[30px] bg-gradient-to-br from-blue-600 to-cyan-500 shadow-2xl shadow-cyan-200 mb-6">

              <UploadCloud className="w-12 h-12 text-white" />

            </div>

            <h2 className="text-2xl font-bold text-slate-800 mb-3">
              Subir Documentos Científicos
            </h2>

            <p className="text-slate-500 max-w-xl mx-auto text-sm leading-relaxed">
              Arrastra tus archivos PDF o selecciónalos desde tu equipo para clasificarlos automáticamente mediante inteligencia artificial.
            </p>

            <label className="inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] transition-all text-white px-8 py-3 rounded-2xl text-sm font-bold shadow-2xl shadow-cyan-200 mt-8 cursor-pointer">

              <UploadCloud className="w-5 h-5" />

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

        {/* TABLA */}
        <section className="bg-white/80 backdrop-blur-2xl rounded-[32px] border border-slate-200 overflow-hidden shadow-sm text-left">

          {/* TOP */}
          <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white/50">

            <div>

              <p className="text-cyan-600 uppercase tracking-[0.2em] text-[10px] font-black mb-1">
                Actividad reciente
              </p>

              <h2 className="text-2xl font-bold text-slate-800">
                Documentos Recientes
              </h2>

            </div>

            <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl text-xs font-bold transition-all">
              Ver historial completo
            </button>

          </div>

          {/* TABLE */}
          <div className="overflow-x-auto">

            <table className="w-full text-sm">

              <thead className="bg-slate-50/80 border-b border-slate-100">

                <tr className="text-slate-500 uppercase text-[11px] tracking-[0.15em]">

                  <th className="px-6 py-5 text-left">
                    Documento
                  </th>

                  <th className="px-6 py-5 text-left">
                    Área
                  </th>

                  <th className="px-6 py-5 text-left">
                    Subárea
                  </th>

                  <th className="px-6 py-5 text-left">
                    Fecha
                  </th>

                  <th className="px-6 py-5 text-center">
                    Acciones
                  </th>

                </tr>
              </thead>

              <tbody>

                {loading && (
                  <tr>
                    <td
                      colSpan="5"
                      className="p-8 text-center text-slate-500"
                    >
                      Cargando documentos...
                    </td>
                  </tr>
                )}

                {error && (
                  <tr>
                    <td
                      colSpan="5"
                      className="p-8 text-center text-red-500"
                    >
                      {error}
                    </td>
                  </tr>
                )}

                {documentos.map((doc) => (

                  <tr
                    key={doc.id}
                    className="border-b border-slate-100 hover:bg-cyan-50/40 transition-all group"
                  >

                    {/* DOCUMENTO */}
                    <td className="px-6 py-5">

                      <div className="flex items-center gap-4">

                        <div className="w-11 h-11 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center">

                          <FileText className="w-5 h-5 text-red-500" />

                        </div>

                        <div>

                          <p className="font-semibold text-slate-800 truncate max-w-[250px]">
                            {doc.name}
                          </p>

                        </div>
                      </div>
                    </td>

                    {/* AREA */}
                    <td className="px-6 py-5 text-slate-500 text-sm">
                      {doc.tematica}
                    </td>

                    {/* SUBAREA */}
                    <td className="px-6 py-5">

                      <span className="px-3 py-1 rounded-xl text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-100">
                        {doc.subarea || "-"}
                      </span>

                    </td>

                    {/* FECHA */}
                    <td className="px-6 py-5 text-slate-400 text-xs">

                      {doc.fecha
                        ? new Date(doc.fecha).toLocaleDateString()
                        : "-"}

                    </td>

                    {/* ACTIONS */}
                    <td className="px-6 py-5">

                      <div className="flex justify-center gap-2 opacity-60 group-hover:opacity-100 transition-all">

                        <button
                          type="button"
                          onClick={() => verDocumento(doc)}
                          className="w-10 h-10 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-600 flex items-center justify-center transition-all"
                        >

                          <Eye className="w-4 h-4" />

                        </button>

                        <button
                          type="button"
                          onClick={() => descargarDocumento(doc)}
                          className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-all"
                        >

                          <FileDown className="w-4 h-4" />

                        </button>

                        <button
                          type="button"
                          onClick={() => eliminarDocumento(doc)}
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
        </section>

      </main>
    </div>
  </div>
);

};

export default UserDashboard;