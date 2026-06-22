import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { User, Mail, Lock, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { LogoMark } from '../components/Logo';
import { DIORAMA_IMG } from '../lib/assets';

const inputCls =
  'w-full rounded-xl border border-navy-900/10 bg-white pl-11 pr-4 py-3 text-navy-900 placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500';

export default function SignupPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/dashboard';
  const { signup } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await signup(name, email, password);
      toast.success('Your account is ready.');
      navigate(next);
    } catch (err) {
      toast.error(err.message || 'Could not create your account.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container-px py-12 md:py-20">
      <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
        <div className="hidden lg:flex flex-col justify-between rounded-[2rem] bg-navy-900 p-10 text-cream relative">
          <div className="flex items-center gap-2.5">
            <LogoMark size={36} />
            <span className="font-heading font-extrabold text-2xl text-cream">Everstead</span>
          </div>
          <img src={DIORAMA_IMG} alt="A friendly home with solar panels and a small wind turbine" className="w-full max-w-sm mx-auto my-6" />
          <div>
            <h2 className="font-heading font-extrabold text-3xl text-cream">Save your plan and come back any time.</h2>
            <p className="mt-2 text-navy-300">One free account holds every home you check.</p>
          </div>
        </div>

        <div className="rounded-[2rem] bg-white border border-navy-900/5 shadow-soft p-8 md:p-10">
          <h1 className="font-heading font-extrabold text-3xl text-navy-900">Create an account</h1>
          <p className="mt-2 text-navy-600">It is free, and it keeps your results safe.</p>

          <form onSubmit={submit} className="mt-7 space-y-4" data-testid="signup-form">
            <div className="relative">
              <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-navy-400" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                data-testid="signup-name"
                className={inputCls}
              />
            </div>
            <div className="relative">
              <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-navy-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@email.com"
                data-testid="signup-email"
                className={inputCls}
              />
            </div>
            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-navy-400" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Pick a password (6+ characters)"
                data-testid="signup-password"
                className={inputCls}
              />
            </div>

            <button
              type="submit"
              disabled={busy}
              data-testid="signup-submit"
              className="w-full inline-flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold text-lg rounded-full py-3.5 shadow-amber transition-all disabled:opacity-60"
            >
              {busy && <Loader2 size={18} className="animate-spin" />} Create account
            </button>
          </form>

          <p className="mt-7 text-center text-navy-600">
            Already have an account?{' '}
            <Link to="/login" data-testid="go-login" className="font-semibold text-amber-600 hover:text-amber-500">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
