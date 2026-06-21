import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowRight, Trash2, Sun, Loader2, Plus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { everstead } from '../api/everstead';
import { fmtMoney, fmtDate } from '../lib/format';
import { DIORAMA_IMG } from '../lib/assets';

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function DashboardPage() {
  const { user, token, logout } = useAuth();
  const [retrofits, setRetrofits] = useState(null);
  const savedPendingRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const data = await everstead.listRetrofits(token);
      setRetrofits(data.retrofits);
    } catch (err) {
      toast.error(err.message || 'Could not load your homes.');
      setRetrofits([]);
    }
  }, [token]);

  useEffect(() => {
    (async () => {
      const pending = sessionStorage.getItem('everstead_pending_plan');
      if (pending && token && !savedPendingRef.current) {
        // consume immediately so a re-run (StrictMode) cannot save twice
        savedPendingRef.current = true;
        sessionStorage.removeItem('everstead_pending_plan');
        try {
          const { assessment, label } = JSON.parse(pending);
          await everstead.saveRetrofit(assessment, label, token);
          toast.success('Your plan is saved.');
        } catch {
          /* ignore, still load list */
        }
      }
      load();
    })();
  }, [token, load]);

  const remove = async (id) => {
    try {
      await everstead.deleteRetrofit(id, token);
      setRetrofits((r) => r.filter((x) => x.id !== id));
      toast.success('Removed.');
    } catch (err) {
      toast.error(err.message || 'Could not remove that home.');
    }
  };

  return (
    <div className="container-px py-12 md:py-16 min-h-[70vh]">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-heading font-extrabold text-3xl md:text-4xl text-navy-900">
            {greeting()}, {user?.name?.split(' ')[0] || 'friend'}.
          </h1>
          <p className="mt-2 text-navy-600">Here are the homes you have saved.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/retrofit"
            data-testid="dashboard-new-assessment"
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-6 py-3 shadow-amber transition-all"
          >
            <Plus size={18} /> New assessment
          </Link>
          <button onClick={logout} data-testid="dashboard-logout" className="text-navy-600 font-semibold hover:text-navy-900">
            Log out
          </button>
        </div>
      </div>

      {retrofits === null ? (
        <div className="flex items-center justify-center py-24 text-navy-500">
          <Loader2 className="animate-spin" /> <span className="ml-2">Loading your homes...</span>
        </div>
      ) : retrofits.length === 0 ? (
        <div className="mt-12 rounded-[2rem] bg-white border border-navy-900/5 shadow-soft p-10 text-center max-w-2xl mx-auto" data-testid="dashboard-empty">
          <img src={DIORAMA_IMG} alt="A friendly home" className="w-56 mx-auto" />
          <h2 className="mt-4 font-heading font-bold text-2xl text-navy-900">You have not saved a home yet.</h2>
          <p className="mt-2 text-navy-600">Let's start your first assessment.</p>
          <Link
            to="/retrofit"
            className="mt-6 inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-7 py-3.5 shadow-amber transition-all"
          >
            Start my assessment <ArrowRight size={18} />
          </Link>
        </div>
      ) : (
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {retrofits.map((r) => (
            <div key={r.id} data-testid={`saved-home-${r.id}`} className="rounded-3xl bg-white border border-navy-900/5 shadow-soft overflow-hidden hover:shadow-lift hover:-translate-y-1 transition-all">
              <div className="h-40 bg-gradient-to-b from-[#fdeed6] to-white flex items-center justify-center">
                <img src={DIORAMA_IMG} alt="Saved home" className="h-36 object-contain" />
              </div>
              <div className="p-6">
                <h3 className="font-heading font-bold text-lg text-navy-900">{r.label}</h3>
                <p className="text-sm text-navy-500 mt-0.5">{r.resolvedAddress}</p>
                <div className="mt-4 flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-azure-600 bg-azure-500/10 rounded-full px-3 py-1">
                    <Sun size={13} /> {r.topRecommendationName}
                  </span>
                  <span className="text-xs text-navy-500">Saved {fmtDate(r.createdAt)}</span>
                </div>
                <p className="mt-4 text-sm text-navy-500">Estimated yearly savings</p>
                <p className="font-heading font-extrabold text-2xl text-leaf-600">
                  {fmtMoney(r.estimatedYearlySavings, r.currency)}
                </p>
                <div className="mt-5 flex items-center justify-between">
                  <Link
                    to={`/plan/${r.id}`}
                    data-testid={`view-plan-${r.id}`}
                    className="inline-flex items-center gap-1.5 font-heading font-bold text-navy-900 bg-cream border border-navy-900/10 rounded-full px-5 py-2.5 hover:border-amber-500 transition-colors"
                  >
                    View my plan <ArrowRight size={16} />
                  </Link>
                  <button
                    onClick={() => remove(r.id)}
                    data-testid={`delete-plan-${r.id}`}
                    className="p-2.5 rounded-full text-navy-400 hover:text-destructive hover:bg-destructive/10 transition-colors"
                    aria-label="Remove home"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
