import React, { useState } from 'react';
import { User, Lock, Mail, CreditCard, FileText } from 'lucide-react';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    nombreCompleto: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');

  //conexion backend

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      // Validación registro
      if (!isLogin && formData.password !== formData.confirmPassword) {
        setError('Las contraseñas no coinciden');
        return;
      }

      // URL dinámica
      const url = isLogin
        ? `http://localhost:8000/login?nombre_usuario=${formData.username}&contrasena=${formData.password}`
        : `http://localhost:8000/register?nombre_usuario=${formData.username}&contrasena=${formData.password}`;

      const response = await fetch(url, {
        method: 'POST'
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error en la solicitud');
      }

      // 🔐 LOGIN
      if (isLogin) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('rol', data.rol);

        console.log('Login exitoso:', data);

        // 🔥 Redirección por rol
        if (data.rol === 'admin') {
          window.location.href = '/admin';
        } else {
          window.location.href = '/dashboard';
        }
      } else {
        // 🆕 REGISTRO
        console.log('Registro exitoso:', data);

        // cambiar a login automáticamente
        setIsLogin(true);
      }

    } catch (err) {
      setError(err.message);
    }
  };


  return (
    <div
      className={`min-h-screen flex items-center justify-center p-6 transition-all duration-700 overflow-hidden relative
    ${isLogin
          ? "bg-gradient-to-br from-[#0f172a] via-[#111827] to-[#1e3a8a]"
          : "bg-gradient-to-br from-[#1e1b4b] via-[#111827] to-[#581c87]"
        }`}
    >

      {/* Glow Effects */}
      <div
        className={`absolute top-[-120px] right-[-120px] w-80 h-80 rounded-full blur-3xl opacity-30
      ${isLogin ? "bg-blue-500" : "bg-purple-500"}`}
      />

      <div
        className={`absolute bottom-[-120px] left-[-120px] w-80 h-80 rounded-full blur-3xl opacity-30
      ${isLogin ? "bg-cyan-400" : "bg-pink-500"}`}
      />

      {/* CARD */}
      <div
        className={`relative w-full transition-all duration-500 rounded-[32px] backdrop-blur-2xl border shadow-2xl overflow-hidden
      ${isLogin
            ? "max-w-md bg-white/10 border-white/10"
            : "max-w-5xl bg-white/10 border-white/10"
          }`}
      >

        {/* LOGIN */}
        {isLogin ? (
          <div className="p-10">

            {/* Header */}
            <div className="flex flex-col items-center mb-8">

              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-xl shadow-blue-500/30 mb-4">
                <FileText className="text-white w-8 h-8" />
              </div>

              <h1 className="text-3xl font-bold text-white">
                Bienvenido
              </h1>

              <p className="text-slate-300 mt-2 text-sm text-center">
                Inicia sesión para acceder al sistema
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-2xl px-4 py-3 text-sm mb-5 text-center backdrop-blur-md">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Usuario */}
              <div>
                <label className="text-sm font-medium text-slate-200 mb-2 block">
                  Usuario
                </label>

                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                  <input
                    type="text"
                    required
                    placeholder="Tu usuario"
                    className="w-full bg-white/5 border border-white/10 text-white placeholder:text-slate-400 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all"
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        username: e.target.value,
                      })
                    }
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="text-sm font-medium text-slate-200 mb-2 block">
                  Contraseña
                </label>

                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    className="w-full bg-white/5 border border-white/10 text-white placeholder:text-slate-400 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all"
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        password: e.target.value,
                      })
                    }
                  />
                </div>
              </div>

              {/* Button */}
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-400 hover:scale-[1.01] active:scale-[0.99] transition-all text-white font-semibold py-3 rounded-2xl shadow-xl shadow-blue-500/30"
              >
                Entrar al Sistema
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 text-center">
              <button
                onClick={() => setIsLogin(false)}
                className="text-sm text-slate-300 hover:text-cyan-300 transition-colors"
              >
                ¿No tienes cuenta?{" "}
                <span className="font-semibold text-cyan-300">
                  Regístrate
                </span>
              </button>
            </div>
          </div>
        ) : (

          /* REGISTER */
          <div className="grid lg:grid-cols-2 min-h-[650px]">

            {/* LEFT */}
            <div className="hidden lg:flex flex-col justify-center p-12 text-white bg-gradient-to-br from-indigo-700 to-purple-700 relative overflow-hidden">

              <div className="absolute top-0 right-0 w-72 h-72 bg-white/10 rounded-full blur-3xl"></div>

              <div className="relative z-10">

                <div className="w-20 h-20 rounded-3xl bg-white/10 backdrop-blur-md flex items-center justify-center mb-8 border border-white/10">
                  <FileText className="w-10 h-10 text-white" />
                </div>

                <h1 className="text-5xl font-bold leading-tight">
                  Crea tu cuenta
                </h1>

                <p className="mt-6 text-white/80 text-lg leading-relaxed">
                  Accede a la plataforma de clasificación y gestión de documentos científicos.
                </p>
              </div>
            </div>

            {/* RIGHT */}
            <div className="bg-white p-8 lg:p-12 flex flex-col justify-center">

              <div className="mb-8">
                <h2 className="text-3xl font-bold text-slate-800">
                  Registro
                </h2>

                <p className="text-slate-500 mt-2">
                  Completa la información para comenzar
                </p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 text-red-500 rounded-2xl px-4 py-3 text-sm mb-5 text-center">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">

                {/* GRID */}
                <div className="grid md:grid-cols-2 gap-5">

                  {/* Nombre */}
                  <div>
                    <label className="text-sm font-medium text-slate-600 mb-2 block">
                      Nombre Completo
                    </label>

                    <div className="relative">
                      <CreditCard className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                      <input
                        type="text"
                        required
                        placeholder="Juan Pérez"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            nombreCompleto: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="text-sm font-medium text-slate-600 mb-2 block">
                      Correo Electrónico
                    </label>

                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                      <input
                        type="email"
                        required
                        placeholder="correo@ejemplo.com"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            email: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>

                  {/* Usuario */}
                  <div>
                    <label className="text-sm font-medium text-slate-600 mb-2 block">
                      Usuario
                    </label>

                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                      <input
                        type="text"
                        required
                        placeholder="Tu usuario"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            username: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="text-sm font-medium text-slate-600 mb-2 block">
                      Contraseña
                    </label>

                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                      <input
                        type="password"
                        required
                        placeholder="••••••••"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            password: e.target.value,
                          })
                        }
                      />
                    </div>
                  </div>
                </div>

                {/* Confirm */}
                <div>
                  <label className="text-sm font-medium text-slate-600 mb-2 block">
                    Confirmar Contraseña
                  </label>

                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

                    <input
                      type="password"
                      required
                      placeholder="••••••••"
                      className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-11 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          confirmPassword: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                {/* Button */}
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:scale-[1.01] active:scale-[0.99] transition-all text-white font-semibold py-3 rounded-2xl shadow-xl shadow-purple-500/20 mt-2"
                >
                  Crear Cuenta
                </button>
              </form>

              {/* Footer */}
              <div className="mt-8 text-center">
                <button
                  onClick={() => setIsLogin(true)}
                  className="text-sm text-slate-500 hover:text-purple-600 transition-colors"
                >
                  ¿Ya tienes cuenta?{" "}
                  <span className="font-semibold text-purple-600">
                    Inicia sesión
                  </span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Login; // ¡NO OLVIDES ESTA LÍNEA!