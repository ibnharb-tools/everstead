import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Mail, Lock, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { everstead } from '../api/everstead';
import { LogoMark } from '../components/Logo';
import { DIORAMA_IMG } from '../lib/assets';

const inputCls =
  'w-full rounded-xl border border-navy-900/10 bg-white pl-11 pr-4 py-3 text-navy-900 placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500';

function OAuthButtons() {
  const tryOAuth = async (provider) => {
    try {
      await everstead.oauth(provider);
    } catch (e) {
      toast(e.message || 'That sign in option is coming soon.');
    }
  };
  return (
    <div className="grid grid-cols-2 gap-3">
      <button
        onClick={() => tryOAuth('google')}
        data-testid="oauth-google"
        className="rounded-xl border border-navy-900/10 bg-white py-2.5 font-semibold text-navy-800 hover:bg-cream transition-colors"
      >
        Continue with Google
      </button>
      <button
        onClick={() => tryOAuth('apple')}
        data-testid="oauth-apple"
        className="rounded-xl border border-navy-900/10 bg-white py-2.5 font-semibold text-navy-800 hover:bg-cream transition-colors"
      >
        Continue with Apple
      </button>
    </div>
  );
}

function AuthPanel({ title, subtitle }) {
  return (
    <div className="hidden lg:flex flex-col justify-between rounded-[2rem] bg-navy-900 p-10 text-cream overflow-hidden relative">
      <div className="flex items-center gap-2.5">
        <LogoMark size={36} />
        <span className="font-heading font-extrabold text-2xl text-cream">Everstead</span>
      </div>
      <div className="relative my-6">
        <img src={DIORAMA_IMG} alt="A friendly home with solar panels and a small wind turbine" className="w-full max-w-sm mx-auto" />
      </div>
      <div>
        <h2 className="font-heading font-extrabold text-3xl text-cream">{title}</h2>
        <p className="mt-2 text-navy-300">{subtitle}</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/dashboard';
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [forgot, setForgot] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      toast.success('Welcome back.');
      navigate(next);
    } catch (err) {
      toast.error(err.message || 'Could not log you in.');
    } finally {
      setBusy(false);
    }
  };

  const sendReset = async () => {
    try {
      const res = await everstead.forgotPassword(email);
      toast.success(res.message || 'Check your email for reset steps.');
      setForgot(false);
    } catch (err) {
      toast.error(err.message || 'Could not send reset email.');
    }
  };

  return (
    <div className="container-px py-12 md:py-20">
      <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
        <AuthPanel title="Welcome back. Let's check on your home." subtitle="Your saved plans are right where you left them." />
        <div className="rounded-[2rem] bg-white border border-navy-900/5 shadow-soft p-8 md:p-10">
          <h1 className="font-heading font-extrabold text-3xl text-navy-900">Log in</h1>
          <p className="mt-2 text-navy-600">Welcome back. Let's check on your home.</p>

          <form onSubmit={submit} className="mt-7 space-y-4" data-testid="login-form">
            <div className="relative">
              <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-navy-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@email.com"
                data-testid="login-email"
                className={inputCls}
              />
            </div>
            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-navy-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                data-testid="login-password"
                className={inputCls}
              />
            </div>

            {forgot ? (
              <div className="rounded-xl bg-cream border border-navy-900/10 p-4">
                <p className="text-sm text-navy-700">Enter your email above, then we will send reset steps.</p>
                <div className="mt-3 flex gap-2">
                  <button type="button" onClick={sendReset} className="text-sm font-semibold text-amber-600">Send reset email</button>
                  <button type="button" onClick={() => setForgot(false)} className="text-sm text-navy-500">Cancel</button>
                </div>
              </div>
            ) : (
              <button type="button" onClick={() => setForgot(true)} className="text-sm font-semibold text-navy-600 hover:text-amber-600">
                Forgot password?
              </button>
            )}

            <button
              type="submit"
              disabled={busy}
              data-testid="login-submit"
              className="w-full inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold text-lg rounded-full py-3.5 shadow-amber transition-all disabled:opacity-60"
            >
              {busy && <Loader2 size={18} className="animate-spin" />} Log in
            </button>
          </form>

          <div className="my-6 flex items-center gap-3 text-navy-400 text-sm">
            <span className="h-px bg-navy-900/10 flex-1" /> or <span className="h-px bg-navy-900/10 flex-1" />
          </div>
          <OAuthButtons />

          <p className="mt-7 text-center text-navy-600">
            New here?{' '}
            <Link to="/signup" data-testid="go-signup" className="font-semibold text-amber-600 hover:text-amber-500">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
