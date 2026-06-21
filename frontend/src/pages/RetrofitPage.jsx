import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, ArrowRight, MapPin, Sun, Wind, Thermometer, Check, Save, ShoppingBag, Loader2 } from 'lucide-react';
import { everstead } from '../api/everstead';
import { useAuth } from '../context/AuthContext';
import { ResultsView } from '../components/results/ResultsView';

const STAGES = ['start', 'property', 'energy', 'checking', 'results'];

function Choice({ active, onClick, testid, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testid}
      className={`rounded-2xl border px-4 py-3 font-semibold text-left transition-all ${
        active
          ? 'border-amber-500 bg-amber-500/10 text-navy-900 ring-2 ring-amber-500/20'
          : 'border-navy-900/10 bg-white text-navy-700 hover:border-navy-900/25'
      }`}
    >
      {children}
    </button>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="font-heading font-bold text-navy-900">{label}</label>
      {hint && <p className="text-sm text-navy-500 mt-0.5">{hint}</p>}
      <div className="mt-3">{children}</div>
    </div>
  );
}

export default function RetrofitPage() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [stage, setStage] = useState('start');
  const [assessment, setAssessment] = useState(null);
  const [checkStep, setCheckStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const ranRef = useRef(false);

  const [form, setForm] = useState({
    address: '',
    propertyType: 'house',
    floors: 1,
    roofOrLotSize: 'medium',
    siteFeatures: [],
    monthlyBill: '100_200',
    heatingType: 'gas',
    goals: [],
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k, v) =>
    setForm((f) => ({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] }));

  const stepIndex = STAGES.indexOf(stage);
  const progress = stage === 'start' ? 0 : ((stepIndex - 0) / 4) * 100;

  // Run the assessment when we reach the checking stage
  useEffect(() => {
    if (stage !== 'checking') {
      ranRef.current = false;
      return;
    }
    if (ranRef.current) return;
    ranRef.current = true;
    setCheckStep(0);
    const t1 = setTimeout(() => setCheckStep(1), 700);
    const t2 = setTimeout(() => setCheckStep(2), 1400);
    const t3 = setTimeout(() => setCheckStep(3), 2100);
    (async () => {
      try {
        const result = await everstead.assess(form);
        setAssessment(result);
        setTimeout(() => setStage('results'), 600);
      } catch (err) {
        toast.error(err.message || 'We could not finish your assessment.');
        setStage('energy');
      }
    })();
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [stage, form]);

  const handleSave = async () => {
    const label = form.address ? form.address.split(',')[0] : 'My home';
    if (!user) {
      sessionStorage.setItem('everstead_pending_plan', JSON.stringify({ assessment, label }));
      toast('Create a free account to save your plan.');
      navigate('/signup?next=/dashboard');
      return;
    }
    setSaving(true);
    try {
      await everstead.saveRetrofit(assessment, label, token);
      toast.success('Your plan is saved.');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.message || 'Could not save your plan.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container-px py-10 md:py-14 min-h-[70vh]">
      {/* Progress bar */}
      {stage !== 'start' && (
        <div className="max-w-3xl mx-auto mb-10">
          <div className="flex items-center justify-between text-sm font-semibold text-navy-600 mb-2">
            <span>Your home</span>
            <span>Energy use</span>
            <span>Checking</span>
            <span>Your plan</span>
          </div>
          <div className="h-2 rounded-full bg-navy-900/10 overflow-hidden">
            <div className="h-full bg-amber-500 transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* START */}
      {stage === 'start' && (
        <div className="max-w-2xl mx-auto text-center pt-6">
          <span className="inline-flex items-center gap-2 bg-amber-500/10 text-amber-600 font-semibold rounded-full px-4 py-1.5 text-sm">
            <span className="w-2 h-2 rounded-full bg-amber-500" /> Retrofit my home
          </span>
          <h1 className="mt-5 font-heading font-extrabold text-4xl md:text-5xl text-navy-900">
            Enter your home address to begin.
          </h1>
          <p className="mt-4 text-lg text-navy-600">
            It takes about five minutes. No account needed to see your first results.
          </p>
          <div className="mt-8 relative">
            <MapPin size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-amber-500" />
            <input
              value={form.address}
              onChange={(e) => set('address', e.target.value)}
              placeholder="123 Main St, your city"
              data-testid="retrofit-address-input"
              className="w-full rounded-2xl border border-navy-900/10 bg-white pl-12 pr-4 py-4 text-lg text-navy-900 placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
            />
          </div>
          <button
            onClick={() => form.address.trim() && setStage('property')}
            disabled={!form.address.trim()}
            data-testid="retrofit-start-btn"
            className="mt-6 inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold text-lg rounded-full px-8 py-4 shadow-amber transition-all disabled:opacity-50"
          >
            Start my assessment <ArrowRight size={20} />
          </button>
        </div>
      )}

      {/* STEP 1: PROPERTY */}
      {stage === 'property' && (
        <div className="max-w-3xl mx-auto" data-testid="retrofit-step-property">
          <h2 className="font-heading font-extrabold text-3xl text-navy-900">Tell us about your property.</h2>
          <p className="mt-2 text-navy-600">A few basics so we know what we are working with.</p>

          <div className="mt-8 space-y-8">
            <Field label="What type of property is it?">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  ['house', 'House'],
                  ['townhouse', 'Townhouse'],
                  ['farm', 'Farm'],
                  ['cabin', 'Cabin'],
                  ['other', 'Other'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.propertyType === v} onClick={() => set('propertyType', v)} testid={`property-type-${v}`}>
                    {l}
                  </Choice>
                ))}
              </div>
            </Field>

            <Field label="How many floors?">
              <div className="grid grid-cols-4 gap-3 max-w-xs">
                {[1, 2, 3, 4].map((n) => (
                  <Choice key={n} active={form.floors === n} onClick={() => set('floors', n)} testid={`floors-${n}`}>
                    {n === 4 ? '4+' : n}
                  </Choice>
                ))}
              </div>
            </Field>

            <Field label="Roughly how big is your roof or property?">
              <div className="grid grid-cols-3 gap-3 max-w-md">
                {[
                  ['small', 'Small'],
                  ['medium', 'Medium'],
                  ['large', 'Large'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.roofOrLotSize === v} onClick={() => set('roofOrLotSize', v)} testid={`size-${v}`}>
                    {l}
                  </Choice>
                ))}
              </div>
            </Field>

            <Field label="Do you have any of these?" hint="Optional. Helps with wind, hydro, and geothermal.">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  ['open_land', 'Open land'],
                  ['stream', 'A stream or moving water'],
                  ['windy', 'Lots of wind exposure'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.siteFeatures.includes(v)} onClick={() => toggle('siteFeatures', v)} testid={`site-${v}`}>
                    <span className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-md border flex items-center justify-center ${form.siteFeatures.includes(v) ? 'bg-amber-500 border-amber-500' : 'border-navy-900/20'}`}>
                        {form.siteFeatures.includes(v) && <Check size={14} className="text-white" />}
                      </span>
                      {l}
                    </span>
                  </Choice>
                ))}
              </div>
            </Field>
          </div>

          <div className="mt-10 flex items-center justify-between">
            <button onClick={() => setStage('start')} data-testid="property-back" className="inline-flex items-center gap-2 font-semibold text-navy-600 hover:text-navy-900">
              <ArrowLeft size={18} /> Back
            </button>
            <button onClick={() => setStage('energy')} data-testid="property-next" className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-7 py-3 shadow-amber transition-all">
              Next <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: ENERGY */}
      {stage === 'energy' && (
        <div className="max-w-3xl mx-auto" data-testid="retrofit-step-energy">
          <h2 className="font-heading font-extrabold text-3xl text-navy-900">Your energy use.</h2>
          <p className="mt-2 text-navy-600">Rough answers are fine. We just need a starting point.</p>

          <div className="mt-8 space-y-8">
            <Field label="About how much is your monthly electricity bill?">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  ['under_100', 'Under $100'],
                  ['100_200', '$100 to $200'],
                  ['200_300', '$200 to $300'],
                  ['over_300', 'Over $300'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.monthlyBill === v} onClick={() => set('monthlyBill', v)} testid={`bill-${v}`}>
                    {l}
                  </Choice>
                ))}
              </div>
            </Field>

            <Field label="How do you heat your home now?">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  ['gas', 'Gas'],
                  ['electric', 'Electric'],
                  ['oil', 'Oil'],
                  ['heat_pump', 'Heat pump'],
                  ['not_sure', 'Not sure'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.heatingType === v} onClick={() => set('heatingType', v)} testid={`heat-${v}`}>
                    {l}
                  </Choice>
                ))}
              </div>
            </Field>

            <Field label="Any goals?">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  ['lower_bill', 'Lower my bill'],
                  ['backup_power', 'Backup power for outages'],
                  ['go_green', 'Go green'],
                  ['all', 'All of the above'],
                ].map(([v, l]) => (
                  <Choice key={v} active={form.goals.includes(v)} onClick={() => toggle('goals', v)} testid={`goal-${v}`}>
                    <span className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-md border flex items-center justify-center ${form.goals.includes(v) ? 'bg-amber-500 border-amber-500' : 'border-navy-900/20'}`}>
                        {form.goals.includes(v) && <Check size={14} className="text-white" />}
                      </span>
                      {l}
                    </span>
                  </Choice>
                ))}
              </div>
            </Field>
          </div>

          <div className="mt-10 flex items-center justify-between">
            <button onClick={() => setStage('property')} data-testid="energy-back" className="inline-flex items-center gap-2 font-semibold text-navy-600 hover:text-navy-900">
              <ArrowLeft size={18} /> Back
            </button>
            <button onClick={() => setStage('checking')} data-testid="energy-next" className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-7 py-3 shadow-amber transition-all">
              See my plan <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: CHECKING */}
      {stage === 'checking' && (
        <div className="max-w-xl mx-auto text-center py-10" data-testid="retrofit-checking">
          <h2 className="font-heading font-extrabold text-3xl text-navy-900">We are checking your address.</h2>
          <p className="mt-3 text-navy-600">Looking at the sun, wind, and ground at your spot. One moment.</p>
          <div className="mt-10 space-y-4 text-left">
            {[
              { icon: Sun, color: '#3DA5E0', label: 'Sunlight through the year' },
              { icon: Wind, color: '#6FBEEB', label: 'Wind speed nearby' },
              { icon: Thermometer, color: '#329257', label: 'Ground warmth underground' },
            ].map((d, i) => {
              const done = checkStep > i;
              return (
                <div
                  key={d.label}
                  className={`flex items-center gap-4 rounded-2xl border p-4 transition-all duration-500 ${
                    done ? 'border-leaf-500/30 bg-leaf-500/5' : 'border-navy-900/10 bg-white'
                  }`}
                >
                  <span className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: `${d.color}1a` }}>
                    <d.icon size={22} style={{ color: d.color }} />
                  </span>
                  <span className="font-semibold text-navy-800 flex-1">{d.label}</span>
                  {done ? (
                    <span className="w-7 h-7 rounded-full bg-leaf-500 flex items-center justify-center">
                      <Check size={16} className="text-white" />
                    </span>
                  ) : (
                    <Loader2 size={20} className="animate-spin text-navy-300" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RESULTS */}
      {stage === 'results' && assessment && (
        <div className="max-w-6xl mx-auto" data-testid="retrofit-results">
          <ResultsView
            assessment={assessment}
            actions={
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  data-testid="save-results-btn"
                  className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-6 py-3 shadow-amber transition-all disabled:opacity-60"
                >
                  {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />} Save my results
                </button>
                <button
                  onClick={() => toast('The marketplace is coming soon.')}
                  data-testid="explore-marketplace-btn"
                  className="inline-flex items-center gap-2 bg-white text-navy-900 border-2 border-navy-900/10 hover:border-navy-900/30 font-heading font-bold rounded-full px-6 py-3 transition-colors"
                >
                  <ShoppingBag size={18} /> Explore the marketplace
                </button>
              </div>
            }
          />

          {!user && (
            <div className="mt-12 rounded-[2rem] bg-navy-900 text-cream p-8 md:p-10 text-center">
              <h3 className="font-heading font-extrabold text-2xl md:text-3xl">Want to keep this plan?</h3>
              <p className="mt-2 text-navy-300">Create a free account so you can come back to it any time.</p>
              <button
                onClick={handleSave}
                data-testid="results-create-account"
                className="mt-6 inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold rounded-full px-7 py-3.5 shadow-amber transition-all"
              >
                Save my results <ArrowRight size={18} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
