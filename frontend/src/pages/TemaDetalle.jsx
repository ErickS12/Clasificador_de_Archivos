import React, { useEffect, useRef, useState } from "react";
import Sidebar from "../components/SidebarUsuario";
import Navbar from "../components/Navbar";
import { useParams } from "react-router-dom";
import {
  Upload,
  FileText,
  Eye,
  Download,
  Edit,
  Trash2,
  Folder,
  Sparkles,
  BarChart3
} from "lucide-react";

const TemaDetalle = () => {

  const { nombre } = useParams();
  const [documentos, setDocumentos] = useState([]);
  const [subtemas, setSubtemas] = useState([]);
  const [temaReal, setTemaReal] = useState("");
  const inputFileRef = useRef(null);

  useEffect(() => {
    obtenerTema();
  }, [nombre]);

  const obtenerTema = async () => {
    try {
      const token = localStorage.getItem("token");

      const response = await fetch("http://localhost:8000/files", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      const clasificacion = data.clasificacion;

      const temaKey = Object.keys(clasificacion).find(
        (k) => k.toLowerCase() === nombre.toLowerCase()
      );

      if (!temaKey) {
        console.log("Tema no encontrado");
        return;
      }
      setTemaReal(temaKey);
      const tema = clasificacion[temaKey];

      let docs = tema.files || [];

      const subs = [];

      Object.keys(tema).forEach((key) => {

        if (key !== "files") {

          subs.push({
            name: key,
            docs: tema[key].files?.length || 0,
          });

          const docsSub = (tema[key].files || []).map((d) => ({
            ...d,
            sub: key,
          }));

          docs = [...docs, ...docsSub];
        }
      });

      setSubtemas(subs);
      setDocumentos(docs);

    } catch (error) {
      console.error(error);
    }
  };

  //funciones
  // SUBIR ARCHIVO
  const subirArchivo = async (e) => {

    const file = e.target.files[0];
    if (!file) return;

    try {

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

      obtenerTema();

    } catch (err) {

      alert(err.message);

    }

  };

  // VER DOCUMENTO
  const verDocumento = async (doc) => {

    try {

      const token = localStorage.getItem("token");

      const params = new URLSearchParams();

      params.append("nombre_archivo", doc.nombre);
      params.append("area", temaReal);

      if (doc.sub) {
        params.append("subarea", doc.sub);
      }

      const response = await fetch(
        `http://localhost:8000/download?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {

        const errorData = await response.json().catch(() => null);

        throw new Error(
          errorData?.detail || "Error al obtener documento"
        );
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      window.open(url, "_blank");

      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 60000);

    } catch (err) {

      alert(err.message);

    }

  };

  // DESCARGAR DOCUMENTO
  const descargarDocumento = async (doc) => {

    try {

      const token = localStorage.getItem("token");

      const params = new URLSearchParams();

      params.append("nombre_archivo", doc.nombre);
      params.append("area", temaReal);

      if (doc.sub) {
        params.append("subarea", doc.sub);
      }

      const response = await fetch(
        `http://localhost:8000/download?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {

        const errorData = await response.json().catch(() => null);

        throw new Error(
          errorData?.detail || "Error al descargar documento"
        );
      }

      const blob = await response.blob();

      const link = document.createElement("a");

      link.href = window.URL.createObjectURL(blob);

      link.download = doc.nombre;

      document.body.appendChild(link);

      link.click();

      link.remove();

      setTimeout(() => {
        window.URL.revokeObjectURL(link.href);
      }, 60000);

    } catch (err) {

      alert(err.message);

    }

  };

  // ELIMINAR DOCUMENTO
  const eliminarDocumento = async (doc) => {

    try {

      const token = localStorage.getItem("token");

      const response = await fetch(
        `http://localhost:8000/document?nombre_archivo=${encodeURIComponent(doc.nombre)}&area=${encodeURIComponent(temaReal)}&subarea=${encodeURIComponent(doc.sub || "")}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error eliminando documento");
      }

      setDocumentos(prev =>
        prev.filter(d => d.id !== doc.id)
      );

      alert("Documento eliminado");

    } catch (err) {

      alert(err.message);

    }

  };

  return (

    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 overflow-hidden">

      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">

        <Navbar title={nombre} user="Usuario" />

        <main className="relative p-6 md:p-8 w-full max-w-[1600px] mx-auto space-y-8">

          {/* Glow Effects */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-100/40 blur-3xl rounded-full"></div>
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-100/40 blur-3xl rounded-full"></div>

          {/* HEADER */}
          <div className="relative flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">

            {/* LEFT */}
            <div>

              <p className="text-cyan-600 uppercase tracking-[0.25em] text-xs font-black mb-3">
                Biblioteca Científica
              </p>

              <h1 className="text-4xl font-bold text-slate-800 capitalize tracking-tight">
                {nombre}
              </h1>

              <p className="text-slate-500 mt-3 text-sm">
                Gestiona documentos, subtemáticas y referencias científicas.
              </p>

            </div>

            {/* ACTIONS */}
            <div className="flex flex-wrap gap-4">

              <>
                <button
                  onClick={() => inputFileRef.current.click()}
                  className="group px-6 py-3.5 rounded-2xl bg-white border border-slate-200 hover:border-cyan-300 hover:shadow-xl hover:shadow-cyan-100 text-sm font-semibold flex items-center gap-3 transition-all"
                >

                  <div className="w-10 h-10 rounded-xl bg-slate-100 group-hover:bg-cyan-50 flex items-center justify-center transition-all">

                    <Upload className="w-5 h-5 text-slate-600 group-hover:text-cyan-600" />

                  </div>

                  <span className="text-slate-700">
                    Subir Documento
                  </span>

                </button>

                <input
                  ref={inputFileRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={subirArchivo}
                />
              </>

              <button className="group px-6 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] text-white text-sm font-bold flex items-center gap-3 shadow-2xl shadow-cyan-200 transition-all">

                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">

                  <Sparkles className="w-5 h-5" />

                </div>

                Generar APA

              </button>

            </div>
          </div>

          {/* SUBTEMAS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">

            {subtemas.map((s, i) => (

              <div
                key={i}
                className="group relative bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 hover:border-cyan-300 hover:shadow-2xl hover:shadow-cyan-100 transition-all cursor-pointer overflow-hidden"
              >

                {/* Glow */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-100 opacity-0 group-hover:opacity-100 blur-3xl rounded-full transition-all"></div>

                <div className="relative flex items-start justify-between">

                  <div>

                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-200 mb-4">

                      <Folder className="w-6 h-6 text-white" />

                    </div>

                    <h3 className="font-bold text-slate-800 text-base leading-tight">
                      {s.name}
                    </h3>

                    <p className="text-sm text-slate-400 mt-2">
                      {s.docs} documentos
                    </p>

                  </div>

                </div>

              </div>

            ))}

          </div>

          {/* TABLE */}
          <div className="bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-[32px] overflow-hidden shadow-sm">

            {/* HEADER */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white/50">

              <div>

                <h2 className="text-2xl font-bold text-slate-800">
                  Documentos
                </h2>

                <p className="text-sm text-slate-400 mt-1">
                  Archivos relacionados con la temática
                </p>

              </div>

            </div>

            {/* TABLE */}
            <div className="overflow-x-auto">

              <table className="w-full text-sm text-left">

                <thead className="bg-slate-50/80 text-slate-500 uppercase text-[11px] tracking-[0.2em] border-b border-slate-100">

                  <tr>

                    <th className="px-6 py-5"></th>

                    <th className="px-6 py-5">
                      Documento
                    </th>

                    <th className="px-6 py-5">
                      Subtemática
                    </th>

                    <th className="px-6 py-5">
                      Fecha
                    </th>

                    <th className="px-6 py-5">
                      Tamaño
                    </th>

                    <th className="px-6 py-5 text-center">
                      Acciones
                    </th>

                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">

                  {documentos.map((doc) => (

                    <tr
                      key={doc.id}
                      className="hover:bg-cyan-50/40 transition-all group"
                    >

                      {/* CHECK */}
                      <td className="px-6 py-5">

                        <input
                          type="checkbox"
                          className="accent-cyan-500 w-4 h-4"
                        />

                      </td>

                      {/* DOCUMENT */}
                      <td className="px-6 py-5">

                        <div className="flex items-center gap-4">

                          <div className="w-12 h-12 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center">

                            <FileText className="w-5 h-5 text-red-500" />

                          </div>

                          <div>

                            <p className="font-semibold text-slate-800 truncate max-w-[250px]">
                              {doc.nombre}
                            </p>

                            <p className="text-xs text-slate-400 mt-1">
                              Documento PDF
                            </p>

                          </div>

                        </div>

                      </td>

                      {/* SUB */}
                      <td className="px-6 py-5">

                        <span className="px-3 py-1.5 rounded-xl text-[11px] font-bold uppercase bg-blue-50 text-blue-600 border border-blue-100">
                          {doc.sub || "Sin subtema"}
                        </span>

                      </td>

                      {/* DATE */}
                      <td className="px-6 py-5 text-slate-500 text-sm">

                        {
                          doc.fecha
                            ? new Date(doc.fecha).toLocaleDateString("es-MX", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            })
                            : "-"
                        }

                      </td>

                      {/* SIZE */}
                      <td className="px-6 py-5 text-slate-400 text-sm">
                        {doc.size}
                      </td>

                      {/* ACTIONS */}
                      <td className="px-6 py-5">

                        <div className="flex justify-center gap-2 opacity-70 group-hover:opacity-100 transition-all">

                          <button
                            onClick={() => verDocumento(doc)}
                            className="w-10 h-10 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-600 flex items-center justify-center transition-all"
                          >

                            <Eye className="w-4 h-4" />

                          </button>

                          <button
                            onClick={() => descargarDocumento(doc)}
                            className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-all"
                          >

                            <Download className="w-4 h-4" />

                          </button>

                          <button
                            className="w-10 h-10 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-500 flex items-center justify-center transition-all"
                          >

                            <Edit className="w-4 h-4" />

                          </button>

                          <button
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
          </div>

          {/* STATS */}
          <div className="grid md:grid-cols-3 gap-6">

            {/* DOCS */}
            <div className="relative bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 overflow-hidden shadow-sm hover:shadow-xl transition-all">

              <div className="absolute top-0 right-0 w-40 h-40 bg-blue-100 blur-3xl rounded-full"></div>

              <div className="relative flex items-center justify-between">

                <div>

                  <p className="text-slate-500 text-[11px] uppercase tracking-[0.2em] font-black">
                    Total Documentos
                  </p>

                  <h3 className="text-5xl font-bold text-slate-800 mt-3">
                    {documentos.length}
                  </h3>

                  <p className="text-emerald-500 text-xs font-bold mt-3">
                    +12 este mes
                  </p>

                </div>

                <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">

                  <FileText className="w-8 h-8" />

                </div>

              </div>
            </div>

            {/* SUBTEMAS */}
            <div className="relative bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 overflow-hidden shadow-sm hover:shadow-xl transition-all">

              <div className="absolute top-0 right-0 w-40 h-40 bg-purple-100 blur-3xl rounded-full"></div>

              <div className="relative flex items-center justify-between">

                <div>

                  <p className="text-slate-500 text-[11px] uppercase tracking-[0.2em] font-black">
                    Subtemáticas
                  </p>

                  <h3 className="text-5xl font-bold text-slate-800 mt-3">
                    {subtemas.length}
                  </h3>

                  <p className="text-slate-400 text-xs font-bold mt-3">
                    Activas
                  </p>

                </div>

                <div className="w-16 h-16 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">

                  <Folder className="w-8 h-8" />

                </div>

              </div>
            </div>

            {/* ACTIVITY */}
            <div className="relative bg-white/80 backdrop-blur-2xl border border-slate-200 rounded-3xl p-6 overflow-hidden shadow-sm hover:shadow-xl transition-all">

              <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-100 blur-3xl rounded-full"></div>

              <div className="relative flex items-center justify-between">

                <div>

                  <p className="text-slate-500 text-[11px] uppercase tracking-[0.2em] font-black">
                    Actividad
                  </p>

                  <h3 className="text-3xl font-bold text-slate-800 mt-3">
                    Hoy
                  </h3>

                  <p className="text-slate-400 text-xs font-bold mt-3">
                    Última actualización
                  </p>

                </div>

                <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">

                  <BarChart3 className="w-8 h-8" />

                </div>

              </div>
            </div>

          </div>

        </main>
      </div>
    </div>
  );


};

export default TemaDetalle;