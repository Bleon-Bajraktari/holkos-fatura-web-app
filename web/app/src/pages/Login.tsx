import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Moon, Sun, ArrowRight } from 'lucide-react';
import PasswordInput from '../components/PasswordInput';
import api, { API_BASE } from '../services/api';

export default function Login() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [logoError, setLogoError] = useState(false);
  const [darkLogoFailed, setDarkLogoFailed] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const userRef = useRef<HTMLInputElement>(null);
  const passRef = useRef<HTMLInputElement>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';
  const autofillHandled = useRef(false);
  const userHasTyped = useRef(false);

  useEffect(() => {
    api.get('/health').catch(() => {});
  }, []);

  // Reset darkLogoFailed kur ndryshon tema
  useEffect(() => {
    setDarkLogoFailed(false);
    setLogoError(false);
  }, [isDark]);

  useEffect(() => {
    if (autofillHandled.current || loading) return;
    const tryAutofillLogin = () => {
      if (userHasTyped.current) return;
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
            const isTimeout = err && typeof err === 'object' && 'code' in err && (err as { code?: string }).code === 'ECONNABORTED';
            const isNetwork = err && typeof err === 'object' && 'message' in err && typeof (err as { message?: string }).message === 'string' && ((err as { message?: string }).message?.includes('Network') || (err as { message?: string }).message?.includes('timeout'));
            setError(isTimeout || isNetwork
              ? 'Serveri po ngrohet. Ju lutemi prisni 30–60 sekonda dhe provoni përsëri.'
              : (err && typeof err === 'object' && 'response' in err ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : null) || 'Emri i përdoruesit ose fjalëkalimi është i gabuar.');
            if (isTimeout || isNetwork) autofillHandled.current = false;
          })
          .finally(() => setLoading(false));
      }
    };
    const iv = setInterval(tryAutofillLogin, 400);
    const stop = setTimeout(() => clearInterval(iv), 12000);
    const onVisibility = () => { if (document.visibilityState === 'visible') tryAutofillLogin(); };
    document.addEventListener('visibilitychange', onVisibility);
    const onTyping = () => { userHasTyped.current = true; };
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
      const isTimeout = err && typeof err === 'object' && 'code' in err && (err as { code?: string }).code === 'ECONNABORTED';
      const isNetwork = err && typeof err === 'object' && 'message' in err && typeof (err as { message?: string }).message === 'string' && ((err as { message?: string }).message?.includes('Network') || (err as { message?: string }).message?.includes('timeout'));
      if (isTimeout || isNetwork) {
        setError('Serveri po ngrohet. Ju lutemi prisni 30–60 sekonda dhe provoni përsëri.');
      } else {
        const msg = err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
        setError(msg || 'Emri i përdoruesit ose fjalëkalimi është i gabuar.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Backend root pa /api suffix (p.sh. https://holkos-fatura-api.onrender.com)
  const backendBase = API_BASE.startsWith('http')
    ? API_BASE.replace(/\/api\/?$/, '')
    : '';
  // Dark theme: provo logo-dark.png; nëse 404 → logo.png si fallback
  const logoUrl = isDark && !darkLogoFailed
    ? `${backendBase}/logo-dark.png`
    : `${backendBase}/logo.png`;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 relative overflow-hidden bg-background">
      {/* Animated mesh orbs */}
      <div className="orb-1 absolute w-[500px] h-[500px] rounded-full bg-violet-500/20 dark:bg-violet-600/15 blur-[120px] pointer-events-none" />
      <div className="orb-2 absolute w-[400px] h-[400px] rounded-full bg-indigo-500/15 dark:bg-indigo-600/10 blur-[100px] pointer-events-none" />
      <div className="orb-3 absolute w-[350px] h-[350px] rounded-full bg-emerald-500/10 dark:bg-emerald-600/8 blur-[80px] pointer-events-none" />

      {/* Theme toggle */}
      <button
        type="button"
        onClick={toggleTheme}
        className="absolute top-4 right-4 p-2.5 rounded-xl text-muted-foreground hover:bg-card/80 hover:text-foreground transition-all backdrop-blur-sm border border-border/50"
        title={isDark ? 'Dritë' : 'Errësirë'}
      >
        {isDark ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-[400px] relative z-10"
      >
        {/* Glass card */}
        <div className="glass rounded-3xl border border-border/60 shadow-2xl shadow-violet-500/10 px-7 pb-7 pt-5 sm:px-8 sm:pb-8">
          {/* Logo */}
          <div className="flex flex-col items-center text-center mb-2">
            <div className="flex items-center justify-center mb-2">
              {logoError ? (
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
                  <span className="text-4xl font-black text-white">H</span>
                </div>
              ) : (
                <div className="w-44 h-44 sm:w-52 sm:h-52 flex items-center justify-center overflow-hidden rounded-2xl bg-white shadow-md">
                  <img
                    key={logoUrl}
                    src={logoUrl}
                    alt="Holkos Fatura"
                    className="max-w-full max-h-full w-auto h-auto object-contain"
                    onError={() => {
                      if (isDark && !darkLogoFailed) {
                        setDarkLogoFailed(true);
                      } else {
                        setLogoError(true);
                      }
                    }}
                    onLoad={() => setLogoError(false)}
                  />
                </div>
              )}
            </div>
          </div>

          <form id="login-form" onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="input-label">
                Emri i përdoruesit
              </label>
              <input
                ref={userRef}
                id="username"
                name="username"
                type="text"
                defaultValue=""
                autoComplete="username"
                className="input-base"
                placeholder="username"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="input-label">
                Fjalëkalimi
              </label>
              <PasswordInput
                ref={passRef}
                id="password"
                name="password"
                defaultValue=""
                autoComplete="current-password"
                inputClassName="input-base"
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-rose-600 dark:text-rose-400 text-sm font-medium bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 px-4 py-2.5 rounded-xl"
              >
                {error}
              </motion.p>
            )}

            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="btn-primary w-full py-3.5 text-base font-black flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Duke hyrë...
                </>
              ) : (
                <>
                  Hyr
                  <ArrowRight size={18} />
                </>
              )}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
