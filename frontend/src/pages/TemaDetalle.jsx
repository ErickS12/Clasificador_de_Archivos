import React from "react";
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

  const documentos = [
    { id: 1, nombre: "Introduction to Deep Learning.pdf", sub: "Deep Learning", fecha: "2024-03-15", size: "2.4 MB" },
    { id: 2, nombre: "Advanced Neural Networks.pdf", sub: "Deep Learning", fecha: "2024-03-14", size: "3.1 MB" },
    { id: 3, nombre: "Image Recognition Techniques.pdf", sub: "Computer Vision", fecha: "2024-03-13", size: "1.8 MB" },
  ];

  const subtemas = [
    { name: "Deep Learning", docs: 45 },
    { name: "Computer Vision", docs: 32 },
    { name: "Reinforcement Learning", docs: 28 },
    { name: "Supervised Learning", docs: 51 },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50">
      
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        
        <Navbar title={nombre} user="Usuario" />

        <main className="p-6 md:p-8 w-full max-w-[1400px] mx-auto space-y-6">
          
          {/* HEADER */}
          <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
            
            <div>
              <h1 className="text-2xl font-bold text-slate-800 capitalize">
                {nombre}
              </h1>
              <p className="text-slate-500 text-sm">
                Documentos y subtemáticas relacionadas
              </p>
            </div>

            <div className="flex gap-3 flex-wrap">
              
              <button className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-sm font-medium flex items-center gap-2 transition-all">
                <Upload className="w-4 h-4" />
                Subir Documento
              </button>

              <button className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold flex items-center gap-2 shadow-lg shadow-blue-200 transition-all active:scale-95">
                <Sparkles className="w-4 h-4" />
                Generar APA
              </button>

            </div>
          </div>

          {/* SUBTEMAS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {subtemas.map((s, i) => (
              <div
                key={i}
                className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-blue-50 p-2 rounded-lg text-blue-600 group-hover:bg-blue-100 transition">
                    <Folder className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-slate-700 text-sm">
                    {s.name}
                  </h3>
                </div>

                <p className="text-xs text-slate-400">
                  {s.docs} documentos
                </p>
              </div>
            ))}
          </div>

          {/* TABLA */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            
            <div className="p-5 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-800">
                Documentos de la temática
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-widest border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-4"></th>
                    <th className="px-6 py-4">Nombre</th>
                    <th className="px-6 py-4">Subtemática</th>
                    <th className="px-6 py-4">Fecha</th>
                    <th className="px-6 py-4">Tamaño</th>
                    <th className="px-6 py-4 text-center">Acciones</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {documentos.map((doc) => (
                    <tr key={doc.id} className="hover:bg-blue-50/30 transition-colors group">
                      
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          className="accent-blue-600 w-4 h-4"
                        />
                      </td>

                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="p-2 bg-red-50 rounded-lg">
                          <FileText className="w-4 h-4 text-red-500" />
                        </div>
                        <span className="font-semibold text-slate-700 truncate max-w-[220px]">
                          {doc.nombre}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <span className="bg-blue-100 text-blue-600 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase">
                          {doc.sub}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {doc.fecha}
                      </td>

                      <td className="px-6 py-4 text-slate-400 text-xs">
                        {doc.size}
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                          
                          <button className="p-2 hover:bg-white hover:shadow-sm rounded-lg text-blue-500 transition-all">
                            <Eye className="w-4 h-4" />
                          </button>

                          <button className="p-2 hover:bg-white hover:shadow-sm rounded-lg text-slate-500 transition-all">
                            <Download className="w-4 h-4" />
                          </button>

                          <button className="p-2 hover:bg-white hover:shadow-sm rounded-lg text-amber-500 transition-all">
                            <Edit className="w-4 h-4" />
                          </button>

                          <button className="p-2 hover:bg-white hover:shadow-sm rounded-lg text-red-500 transition-all">
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
            
            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  Total Documentos
                </p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">
                  {documentos.length}
                </h3>
                <p className="text-green-500 text-[10px] font-bold mt-1">
                  +12 este mes
                </p>
              </div>
              <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
                <FileText className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  Subtemáticas
                </p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">
                  {subtemas.length}
                </h3>
                <p className="text-slate-400 text-[10px] font-bold mt-1">
                  Activas
                </p>
              </div>
              <div className="bg-purple-50 p-3 rounded-2xl text-purple-600">
                <Folder className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  Actividad
                </p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">
                  Hoy
                </h3>
                <p className="text-slate-400 text-[10px] font-bold mt-1">
                  Última actualización
                </p>
              </div>
              <div className="bg-green-50 p-3 rounded-2xl text-green-600">
                <BarChart3 className="w-6 h-6" />
              </div>
            </div>

          </div>

        </main>
      </div>
    </div>
  );
};

export default TemaDetalle;