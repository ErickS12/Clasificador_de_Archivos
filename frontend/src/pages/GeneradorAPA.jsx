import React, { useState } from 'react';
import Sidebar from '../components/SidebarUsuario';
import Navbar from '../components/Navbar';
import { FileText, Eye, Download, Sparkles } from 'lucide-react';

const GeneradorAPA = () => {

  const [selectedDocs, setSelectedDocs] = useState([]);

  const documentos = [
    { id: 1, name: "Deep Learning Applications.pdf", author: "Goodfellow, Bengio" },
    { id: 2, name: "Neural Networks Theory.pdf", author: "Yoshua Bengio" },
  ];

  const historial = [
    { id: 1, label: "5 documentos - 2024-03-15" },
    { id: 2, label: "3 documentos - 2024-03-14" },
  ];

  const toggleDoc = (id) => {
    setSelectedDocs((prev) =>
      prev.includes(id)
        ? prev.filter((d) => d !== id)
        : [...prev, id]
    );
  };
  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">

      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">

        <Navbar title="Generador APA" user="Usuario" />

        <main className="p-6 md:p-8 w-full max-w-[1400px] mx-auto space-y-8">

          {/* HEADER */}
          <div className="relative overflow-hidden rounded-[32px] border border-slate-200 bg-white/80 backdrop-blur-2xl p-8 shadow-sm">

            <div className="absolute top-0 right-0 w-72 h-72 bg-blue-100/50 blur-3xl rounded-full"></div>

            <div className="relative">

              <p className="text-cyan-600 uppercase tracking-[0.25em] text-xs font-bold mb-2">
                Generador Inteligente
              </p>

              <h1 className="text-4xl font-bold tracking-tight text-slate-800">
                Generador de Referencias APA
              </h1>

              <p className="text-slate-500 text-sm mt-3 max-w-2xl">
                Genera referencias bibliográficas automáticamente a partir
                de tus documentos científicos seleccionados.
              </p>

            </div>
          </div>

          {/* GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* DOCUMENTOS */}
            <div className="lg:col-span-2 bg-white/80 backdrop-blur-2xl rounded-[32px] border border-slate-200 p-6 shadow-sm">

              <div className="flex items-center justify-between mb-6">

                <div>

                  <p className="text-cyan-600 uppercase tracking-[0.2em] text-[10px] font-bold mb-1">
                    Biblioteca
                  </p>

                  <h2 className="font-bold text-2xl text-slate-800">
                    Documentos Seleccionados
                  </h2>

                </div>

                <div className="bg-blue-50 border border-blue-100 px-4 py-2 rounded-2xl">

                  <p className="text-xs font-bold text-blue-600">
                    {selectedDocs.length} seleccionados
                  </p>

                </div>

              </div>

              {/* EMPTY */}
              {selectedDocs.length === 0 && (
                <div className="flex flex-col items-center justify-center py-14 text-center border border-dashed border-slate-200 rounded-3xl bg-slate-50/70">

                  <div className="w-20 h-20 rounded-3xl bg-blue-50 flex items-center justify-center mb-5 text-blue-500">

                    <FileText className="w-10 h-10" />

                  </div>

                  <p className="text-sm font-semibold text-slate-700">
                    No hay documentos seleccionados
                  </p>

                  <p className="text-xs mt-2 text-slate-400">
                    Selecciona documentos para generar referencias APA
                  </p>

                </div>
              )}

              {/* LISTA */}
              <div className="space-y-4">

                {documentos.map((doc) => {

                  const isSelected = selectedDocs.includes(doc.id);

                  return (
                    <label
                      key={doc.id}
                      className={`group flex items-center gap-4 p-5 rounded-3xl border cursor-pointer transition-all duration-200
                    ${isSelected
                          ? "bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300 shadow-md shadow-cyan-100"
                          : "bg-white border-slate-200 hover:border-cyan-300 hover:shadow-lg"
                        }`}
                    >

                      {/* CHECK */}
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleDoc(doc.id)}
                        className="accent-blue-600 w-4 h-4"
                      />

                      {/* ICON */}
                      <div
                        className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all
                      ${isSelected
                            ? "bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-lg shadow-cyan-200"
                            : "bg-slate-100 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600"
                          }`}
                      >

                        <FileText className="w-5 h-5" />

                      </div>

                      {/* INFO */}
                      <div className="flex-1 min-w-0">

                        <p className="font-semibold text-sm text-slate-800 truncate">
                          {doc.name}
                        </p>

                        <p className="text-xs text-slate-500 mt-1 truncate">
                          {doc.author}
                        </p>

                      </div>

                    </label>
                  );
                })}
              </div>
            </div>

            {/* HISTORIAL */}
            <div className="bg-white/80 backdrop-blur-2xl rounded-[32px] border border-slate-200 p-6 shadow-sm relative overflow-hidden">

              <div className="absolute top-0 right-0 w-56 h-56 bg-purple-100/40 blur-3xl rounded-full"></div>

              <div className="relative">

                <p className="text-purple-600 uppercase tracking-[0.2em] text-[10px] font-bold mb-1">
                  Actividad
                </p>

                <h2 className="font-bold text-2xl text-slate-800 mb-6">
                  Historial
                </h2>

                <div className="space-y-4">

                  {historial.map((item) => (

                    <div
                      key={item.id}
                      className="group p-4 rounded-3xl border border-slate-200 bg-white hover:shadow-lg transition-all"
                    >

                      <div className="flex justify-between items-center gap-3">

                        <div className="min-w-0">

                          <p className="text-sm font-semibold text-slate-700 truncate">
                            {item.label}
                          </p>

                          <p className="text-[11px] text-slate-400 mt-1">
                            Referencia generada
                          </p>

                        </div>

                        <div className="flex gap-2">

                          <button className="w-10 h-10 rounded-2xl bg-blue-50 hover:bg-blue-100 text-blue-500 flex items-center justify-center transition-all">

                            <Eye className="w-4 h-4" />

                          </button>

                          <button className="w-10 h-10 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-all">

                            <Download className="w-4 h-4" />

                          </button>

                        </div>

                      </div>

                    </div>
                  ))}

                </div>

              </div>
            </div>

          </div>

          {/* OPCIONES */}
          <div className="bg-white/80 backdrop-blur-2xl rounded-[32px] border border-slate-200 p-8 shadow-sm relative overflow-hidden">

            <div className="absolute bottom-0 left-0 w-72 h-72 bg-cyan-100/40 blur-3xl rounded-full"></div>

            <div className="relative">

              <div className="mb-6">

                <p className="text-cyan-600 uppercase tracking-[0.2em] text-[10px] font-bold mb-1">
                  Configuración
                </p>

                <h2 className="font-bold text-2xl text-slate-800">
                  Opciones de Formato
                </h2>

              </div>

              <div className="grid md:grid-cols-2 gap-5 mb-8">

                <div>

                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 block">
                    Versión APA
                  </label>

                  <select className="w-full bg-slate-50 border border-slate-200 px-4 py-3 rounded-2xl text-sm focus:ring-2 focus:ring-cyan-400 outline-none transition-all">

                    <option>APA 7</option>
                    <option>APA 6</option>

                  </select>

                </div>

                <div>

                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 block">
                    Idioma
                  </label>

                  <select className="w-full bg-slate-50 border border-slate-200 px-4 py-3 rounded-2xl text-sm focus:ring-2 focus:ring-cyan-400 outline-none transition-all">

                    <option>Español</option>
                    <option>Inglés</option>

                  </select>

                </div>

              </div>

              <button className="w-full bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.01] active:scale-[0.99] transition-all text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-3 shadow-xl shadow-cyan-200">

                <Sparkles className="w-5 h-5" />

                Generar Referencias APA

              </button>

            </div>
          </div>

        </main>
      </div>
    </div>
  );
};

export default GeneradorAPA;