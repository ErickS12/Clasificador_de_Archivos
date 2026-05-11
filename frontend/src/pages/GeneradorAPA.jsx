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
    <div className="flex min-h-screen bg-slate-50">
      
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        
        <Navbar title="Generador APA" user="Usuario" />

        <main className="p-6 md:p-8 w-full max-w-[1400px] mx-auto space-y-6">
          
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-slate-800">
              Generador de Referencias APA
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Genera referencias bibliográficas automáticamente
            </p>
          </div>

          {/* GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* DOCUMENTOS */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5">
              <h2 className="font-bold text-slate-700 mb-4">
                Documentos Seleccionados
              </h2>

              {/* EMPTY STATE */}
              {selectedDocs.length === 0 && (
                <div className="flex flex-col items-center justify-center py-10 text-center text-slate-400">
                  <FileText className="w-10 h-10 mb-3" />
                  <p className="text-sm font-medium">
                    No hay documentos seleccionados
                  </p>
                  <p className="text-xs mt-1">
                    Selecciona documentos para generar referencias
                  </p>
                </div>
              )}

              {/* LISTA */}
              <div className="space-y-3">
                {documentos.map((doc) => {
                  const isSelected = selectedDocs.includes(doc.id);

                  return (
                    <label
                      key={doc.id}
                      className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all
                      ${isSelected
                          ? "bg-blue-50 border-blue-400 shadow-sm"
                          : "bg-white border-slate-200 hover:bg-slate-50"
                        }`}
                    >
                      {/* CHECK */}
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleDoc(doc.id)}
                        className="accent-blue-600 w-4 h-4"
                      />

                      <div>
                        <p className="font-semibold text-sm text-slate-700">
                          {doc.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {doc.author}
                        </p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* HISTORIAL */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5">
              <h2 className="font-bold text-slate-700 mb-4">Historial</h2>

              <div className="space-y-3">
                {historial.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 border rounded-xl flex justify-between items-center hover:bg-slate-50"
                  >
                    <p className="text-sm text-slate-600">{item.label}</p>

                    <div className="flex gap-2">
                      <button className="p-2 rounded-lg hover:bg-blue-50 text-blue-500">
                        <Eye className="w-4 h-4" />
                      </button>

                      <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-600">
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* OPCIONES */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
            
            <h2 className="font-bold text-slate-700">Opciones de Formato</h2>

            <div className="grid md:grid-cols-2 gap-4">
              
              <select className="bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                <option>APA 7</option>
                <option>APA 6</option>
              </select>

              <select className="bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                <option>Español</option>
                <option>Inglés</option>
              </select>

            </div>

            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-blue-200 transition-all active:scale-95">
              <Sparkles className="w-4 h-4" />
              Generar Referencias APA
            </button>

          </div>

        </main>
      </div>
    </div>
  );
};

export default GeneradorAPA;