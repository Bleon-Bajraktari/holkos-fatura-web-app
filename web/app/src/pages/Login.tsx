import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import PasswordInput from '../components/PasswordInput';

export default function Login() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [logoError, setLogoError] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const userRef = useRef<HTMLInputElement>(null);
  const passRef = useRef<HTMLInputElement>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';
  const autofillHandled = useRef(false);
  const lastTypingRef = useRef(0);

  useEffect(() => {
    if (autofillHandled.current || loading) return;
    const tryAutofillLogin = () => {
      if (Date.now() - lastTypingRef.current < 800) return;
      const userEl = document.getElementById('username') as HTMLInputElement | null;
      const passEl = document.getElementById('password') as HTMLInputElement | null;
      const u = userEl?.value?.trim();
      const p = passEl?.value ?? '';
      if (u && p && !autofillHandled.current) {
        autofillHandled.current = true;
        setError('');
        setLoading(true);
        login(u, p)
          .then(() => navigate(from, { replace: true }))
          .catch((err: unknown) => {
            const msg = err && typeof err === 'object' && 'response' in err
              ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
              : null;
            setError(msg || 'Emri i përdoruesit ose fjalëkalimi është i gabuar.');
            autofillHandled.current = false;
          })
          .finally(() => setLoading(false));
      }
    };
    // Poll për 15 sek (iOS Safari: autofill ndodh kur përdoruesi prek fushën dhe zgjedh)
    const iv = setInterval(tryAutofillLogin, 300);
    const stop = setTimeout(() => clearInterval(iv), 15000);
    const onVisibility = () => { if (document.visibilityState === 'visible') tryAutofillLogin(); };
    const onFocus = () => { tryAutofillLogin(); };
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('focus', onFocus);
    const onTyping = () => { lastTypingRef.current = Date.now(); };
    const userEl = document.getElementById('username');
    const passEl = document.getElementById('password');
    userEl?.addEventListener('input', onTyping);
    userEl?.addEventListener('keydown', onTyping);
    passEl?.addEventListener('input', onTyping);
    passEl?.addEventListener('keydown', onTyping);
    return () => {
      clearInterval(iv);
      clearTimeout(stop);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('focus', onFocus);
      userEl?.removeEventListener('input', onTyping);
      userEl?.removeEventListener('keydown', onTyping);
      passEl?.removeEventListener('input', onTyping);
      passEl?.removeEventListener('keydown', onTyping);
    };
  }, [loading, login, navigate, from]);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const userEl = userRef.current ?? document.getElementById('username') as HTMLInputElement | null;
    const passEl = passRef.current ?? document.getElementById('password') as HTMLInputElement | null;
    const u = (userEl?.value ?? '').toString().trim();
    const p = (passEl?.value ?? '').toString();
    if (!u || !p) return;
    setError('');
    setLoading(true);
    try {
      await login(u, p);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null;
      setError(msg || 'Emri i përdoruesit ose fjalëkalimi është i gabuar.');
    } finally {
      setLoading(false);
    }
  };

  const logoUrl = '/icon-192.png';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/40 px-4 py-8 sm:py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-[420px]"
      >
        <div className="bg-white/90 backdrop-blur-sm rounded-[2rem] shadow-xl shadow-slate-200/50 border border-slate-100 pt-0 px-6 pb-6 sm:pt-0 sm:px-8 sm:pb-8">
          <div className="flex flex-col items-center text-center -mt-0 mb-0">
            <div className="w-64 h-64 sm:w-80 sm:h-80 flex items-center justify-center overflow-hidden">
              {logoError ? (
                <span className="text-9xl sm:text-[10rem] font-black text-blue-600">H</span>
              ) : (
                <img
                  src={logoUrl}
                  alt="Holkos Fatura"
                  className="max-w-full max-h-full w-auto h-auto object-contain"
                  onError={() => setLogoError(true)}
                />
              )}
            </div>
          </div>

          <form id="login-form" onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-slate-700 mb-2">
                Emri i përdoruesit
              </label>
              <input
                ref={userRef}
                id="username"
                name="username"
                type="text"
                defaultValue=""
                autoComplete="username"
                className="w-full px-4 py-3.5 rounded-2xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 focus:bg-white outline-none transition-all text-base min-h-[48px]"
                placeholder="Username"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-slate-700 mb-2">
                Fjalëkalimi
              </label>
              <PasswordInput
                ref={passRef}
                id="password"
                name="password"
                defaultValue=""
                autoComplete="current-password"
                inputClassName="w-full px-4 py-3.5 rounded-2xl border border-slate-200 bg-slate-50/50 text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 focus:bg-white outline-none transition-all text-base min-h-[48px]"
                placeholder="Password"
                required
                disabled={loading}
              />
            </div>
            {error && (
              <p className="text-rose-600 text-sm font-medium bg-rose-50 px-4 py-2 rounded-xl">
                {error}
              </p>
            )}
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 rounded-2xl font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 transition-all disabled:opacity-70 disabled:cursor-not-allowed text-base"
            >
              {loading ? 'Duke hyrë...' : 'Hyr'}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
