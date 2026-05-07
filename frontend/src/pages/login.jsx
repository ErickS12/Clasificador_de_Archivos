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
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <div className="bg-white p-8 rounded-3xl shadow-2xl w-full max-w-sm border border-slate-50">

        {/* Encabezado con Icono */}
        <div className="flex flex-col items-center mb-6">
          <div className="bg-blue-600 p-2.5 rounded-xl mb-3 shadow-lg shadow-blue-100">
            <FileText className="text-white w-7 h-7" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 text-center tracking-tight">
            Sistema Clasificador Científico
          </h1>
          <p className="text-slate-400 text-[11px] mt-1 uppercase font-semibold tracking-wider">
            {isLogin ? 'Gestión de Documentos' : 'Registro de Investigador'}
          </p>
        </div>

        {error && (
          <p className="bg-red-50 text-red-500 p-2 rounded-lg mb-4 text-[11px] text-center font-medium border border-red-100">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Campos dinámicos de Registro */}
          {!isLogin && (
            <>
              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-1 ml-1 uppercase">Nombre Completo</label>
                <div className="relative">
                  <CreditCard className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                  <input
                    type="text" required placeholder="Juan Pérez"
                    className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl outline-none bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all"
                    onChange={(e) => setFormData({ ...formData, nombreCompleto: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-1 ml-1 uppercase">Correo Electrónico</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                  <input
                    type="email" required placeholder="correo@ejemplo.com"
                    className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl outline-none bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all"
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
              </div>
            </>
          )}

          {/* Campos de Usuario y Password */}
          <div>
            <label className="block text-[10px] font-bold text-slate-600 mb-1 ml-1 uppercase">Usuario</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
              <input
                type="text" required placeholder="Tu usuario"
                className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl outline-none bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all"
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-600 mb-1 ml-1 uppercase">Contraseña</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
              <input
                type="password" required placeholder="••••••••"
                className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl outline-none bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all"
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-[10px] font-bold text-slate-600 mb-1 ml-1 uppercase">Confirmar Contraseña</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                <input
                  type="password" required placeholder="••••••••"
                  className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl outline-none bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all"
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                />
              </div>
            </div>
          )}

          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-xl transition-all shadow-md shadow-blue-100 text-sm mt-4">
            {isLogin ? 'Entrar al Sistema' : 'Crear Cuenta'}
          </button>
        </form>

        <div className="mt-8 pt-4 border-t border-slate-100 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-xs text-slate-500 hover:text-blue-600 transition-colors font-medium"
          >
            {isLogin ? (
              <span>¿Eres nuevo? <strong className="text-blue-600">Regístrate aquí</strong></span>
            ) : (
              <span>¿Ya tienes cuenta? <strong className="text-blue-600">Inicia sesión</strong></span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login; // ¡NO OLVIDES ESTA LÍNEA!