import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, ArrowRight, MapPin, Sun, Wind, Thermometer, Check, Save, ShoppingBag, Loader2, ToggleLeft, ToggleRight } from 'lucide-react';
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

function NumericInput({ value, onChange, placeholder, unit, min = 0, max }) {
  return (
    <div className="relative max-w-xs">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        className="w-full rounded-2xl border border-navy-900/10 bg-white px-4 py-3 pr-16 text-navy-900 placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
      />
      {unit && (
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-navy-500">
          {unit}
        </span>
      )}
    </div>
  );
}

const APPLIANCES = [
  { key: 'ev', label: 'Electric vehicle', kwhPerMonth: 160 },
  { key: 'heat_pump', label: 'Heat pump', kwhPerMonth: 250 },
  { key: 'ac', label: 'Central air conditioning', kwhPerMonth: 200 },
  { key: 'electric_dryer', label: 'Electric dryer', kwhPerMonth: 45 },
  { key: 'electric_water_heater', label: 'Electric water heater', kwhPerMonth: 120 },
  { key: 'pool_pump', label: 'Pool pump', kwhPerMonth: 150 },
  { key: 'chest_freezer', label: 'Chest freezer', kwhPerMonth: 35 },
  { key: 'hot_tub', label: 'Hot tub / spa', kwhPerMonth: 200 },
];

function formatSuggestion(item) {
  const a = item.address || {};
  const road = a.road || a.pedestrian || '';
  const number = a.house_number || '';
  const street = [number, road].filter(Boolean).join(' ');
  const postcode = a.postcode || '';
  const city = a.city || a.town || a.village || a.municipality || '';
  const state = a.state || a.province || '';
  const country = a.country || '';
  return [street, postcode, city, state, country].filter(Boolean).join(', ');
}

export default function RetrofitPage() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [stage, setStage] = useState('start');
  const [assessment, setAssessment] = useState(null);
  const [checkStep, setCheckStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const ranRef = useRef(false);

  // Address autocomplete
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggLoading, setSuggLoading] = useState(false);
  const debounceRef = useRef(null);
  const addressWrapRef = useRef(null);

  const [form, setForm] = useState({
    address: '',
    lat: null,
    lon: null,
    propertyType: 'house',
    floors: 1,
    // Roof size — numeric
    roofSizeValue: '',
    roofSizeUnit: 'sqft',
    // Site features + sub-details
    siteFeatures: [],
    siteFeatureDetails: {
      open_land: { areaAcres: '' },
      stream: { widthM: '' },
      windy: { speedKmh: '' },
    },
    // Energy
    billMode: 'dollar',
    billValue: '',
    heatingType: 'gas',
    goals: [],
    // Appliances
    appliances: [],
    applianceCounts: {},
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k, v) =>
    setForm((f) => ({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] }));
  const setFeatureDetail = (feature, key, val) =>
    setForm((f) => ({
      ...f,
      siteFeatureDetails: {
        ...f.siteFeatureDetails,
        [feature]: { ...f.siteFeatureDetails[feature], [key]: val },
      },
    }));
  const setApplianceCount = (key, count) =>
    setForm((f) => ({ ...f, applianceCounts: { ...f.applianceCounts, [key]: count } }));

  // Fetch address suggestions from Nominatim
  const fetchSuggestions = useCallback((q) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q || q.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSuggLoading(true);
      try {
        const resp = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&addressdetails=1&limit=6`,
          { headers: { 'Accept-Language': 'en' } }
        );
        const data = await resp.json();
        setSuggestions(data);
        setShowSuggestions(data.length > 0);
      } catch {
        setSuggestions([]);
      } finally {
        setSuggLoading(false);
      }
    }, 320);
  }, []);

  const pickSuggestion = (item) => {
    const formatted = formatSuggestion(item);
    setForm((f) => ({ ...f, address: formatted, lat: parseFloat(item.lat), lon: parseFloat(item.lon) }));
    setShowSuggestions(false);
    setSuggestions([]);
  };

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e) => {
      if (addressWrapRef.current && !addressWrapRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const stepIndex = STAGES.indexOf(stage);
  const progress = stage === 'start' ? 0 : ((stepIndex - 0) / 4) * 100;

  // Build the payload to send to the backend
  const buildPayload = () => {
    // Convert roof size to m²
    let roofSizeM2 = null;
    if (form.roofSizeValue) {
      const val = parseFloat(form.roofSizeValue);
      roofSizeM2 = form.roofSizeUnit === 'sqft' ? val * 0.0929 : val;
    }

    // Convert bill to monthly dollar or kWh
    const billVal = parseFloat(form.billValue) || null;

    // Compute total extra kWh/month from appliances
    const extraKwhMonth = form.appliances.reduce((sum, key) => {
      const appl = APPLIANCES.find((a) => a.key === key);
      const count = parseInt(form.applianceCounts[key] || 1);
      return sum + (appl ? appl.kwhPerMonth * count : 0);
    }, 0);

    return {
      address: form.address,
      lat: form.lat,
      lon: form.lon,
      propertyType: form.propertyType,
      floors: form.floors,
      // New: exact roof size
      roofSizeM2,
      // Legacy fallback (adapter still accepts this)
      roofOrLotSize: roofSizeM2
        ? roofSizeM2 < 80 ? 'small' : roofSizeM2 < 180 ? 'medium' : 'large'
        : 'medium',
      siteFeatures: form.siteFeatures,
      siteFeatureDetails: form.siteFeatureDetails,
      // Bill
      monthlyBillDollar: form.billMode === 'dollar' ? billVal : null,
      monthlyBillKwh: form.billMode === 'kwh' ? billVal : null,
      extraKwhMonth: extraKwhMonth || null,
      appliances: form.appliances,
      // Legacy
      monthlyBill: form.billMode === 'dollar' && billVal
        ? billVal < 100 ? 'under_100' : billVal < 200 ? '100_200' : billVal < 300 ? '200_300' : 'over_300'
        : '100_200',
      heatingType: form.heatingType,
      goals: form.goals,
    };
  };

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
        const result = await everstead.assess(buildPayload());
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

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
          <div className="mt-8 relative" ref={addressWrapRef}>
            <MapPin size={20} className="absolute left-4 top-[18px] text-amber-500 z-10" />
            {suggLoading && (
              <Loader2 size={16} className="absolute right-4 top-[20px] text-navy-400 animate-spin z-10" />
            )}
            <input
              value={form.address}
              onChange={(e) => {
                set('address', e.target.value);
                set('lat', null);
                set('lon', null);
                fetchSuggestions(e.target.value);
              }}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              placeholder="123 Main St, your city"
              data-testid="retrofit-address-input"
              autoComplete="off"
              className="w-full rounded-2xl border border-navy-900/10 bg-white pl-12 pr-10 py-4 text-lg text-navy-900 placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
            />
            {showSuggestions && suggestions.length > 0 && (
              <ul className="absolute z-50 left-0 right-0 mt-2 bg-white rounded-2xl border border-navy-900/10 shadow-xl overflow-hidden text-left">
                {suggestions.map((item) => {
                  const formatted = formatSuggestion(item);
                  return (
                    <li key={item.place_id}>
                      <button
                        type="button"
                        className="w-full px-4 py-3 text-sm text-navy-800 hover:bg-amber-500/5 flex items-center gap-2 border-b border-navy-900/5 last:border-0"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          pickSuggestion(item);
                        }}
                      >
                        <MapPin size={14} className="text-amber-500 shrink-0" />
                        <span className="truncate">{formatted}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
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

            <Field label="How big is your roof or property?" hint="Used to estimate solar panel capacity and system sizing.">
              <div className="flex items-center gap-3">
                <NumericInput
                  value={form.roofSizeValue}
                  onChange={(v) => set('roofSizeValue', v)}
                  placeholder={form.roofSizeUnit === 'sqft' ? 'e.g. 1400' : 'e.g. 130'}
                  unit={form.roofSizeUnit === 'sqft' ? 'sq ft' : 'm²'}
                  min={1}
                />
                <button
                  type="button"
                  onClick={() => set('roofSizeUnit', form.roofSizeUnit === 'sqft' ? 'm2' : 'sqft')}
                  className="flex items-center gap-1.5 text-sm font-semibold text-navy-600 hover:text-amber-600 border border-navy-900/10 rounded-xl px-3 py-2.5 bg-white transition-colors"
                >
                  {form.roofSizeUnit === 'sqft'
                    ? <><ToggleLeft size={18} /> Switch to m²</>
                    : <><ToggleRight size={18} /> Switch to sq ft</>}
                </button>
              </div>
              {!form.roofSizeValue && (
                <p className="text-xs text-navy-400 mt-2">Leave blank and we will estimate based on property type.</p>
              )}
            </Field>

            <Field label="Do you have any of these?" hint="Optional. Helps with wind, hydro, and geothermal.">
              <div className="space-y-3">
                {[
                  ['open_land', 'Open land', 'Approximate area (acres)', 'areaAcres', 'acres', 1, 10000],
                  ['stream', 'A stream or moving water', 'Approximate stream width (metres)', 'widthM', 'm', 0.1, 50],
                  ['windy', 'Lots of wind exposure', 'Typical wind speed (km/h)', 'speedKmh', 'km/h', 1, 150],
                ].map(([v, l, subLabel, subKey, subUnit, subMin, subMax]) => (
                  <div key={v} className="space-y-2">
                    <Choice active={form.siteFeatures.includes(v)} onClick={() => toggle('siteFeatures', v)} testid={`site-${v}`}>
                      <span className="flex items-center gap-2">
                        <span className={`w-5 h-5 rounded-md border flex items-center justify-center ${form.siteFeatures.includes(v) ? 'bg-amber-500 border-amber-500' : 'border-navy-900/20'}`}>
                          {form.siteFeatures.includes(v) && <Check size={14} className="text-white" />}
                        </span>
                        {l}
                      </span>
                    </Choice>
                    {form.siteFeatures.includes(v) && (
                      <div className="ml-7 pl-2 border-l-2 border-amber-500/30">
                        <label className="text-sm font-semibold text-navy-700">{subLabel}</label>
                        <div className="mt-1.5">
                          <NumericInput
                            value={form.siteFeatureDetails[v][subKey]}
                            onChange={(val) => setFeatureDetail(v, subKey, val)}
                            placeholder="Optional"
                            unit={subUnit}
                            min={subMin}
                            max={subMax}
                          />
                        </div>
                      </div>
                    )}
                  </div>
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
            {/* Monthly bill */}
            <Field label="Your monthly energy cost or usage" hint="Enter either your average electricity bill or your monthly consumption.">
              <div className="flex gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => set('billMode', 'dollar')}
                  className={`rounded-xl px-4 py-2 text-sm font-semibold transition-all border ${form.billMode === 'dollar' ? 'bg-amber-500 text-white border-amber-500' : 'bg-white text-navy-700 border-navy-900/10 hover:border-navy-900/25'}`}
                >
                  $ Monthly bill
                </button>
                <button
                  type="button"
                  onClick={() => set('billMode', 'kwh')}
                  className={`rounded-xl px-4 py-2 text-sm font-semibold transition-all border ${form.billMode === 'kwh' ? 'bg-amber-500 text-white border-amber-500' : 'bg-white text-navy-700 border-navy-900/10 hover:border-navy-900/25'}`}
                >
                  kWh per month
                </button>
              </div>
              <NumericInput
                value={form.billValue}
                onChange={(v) => set('billValue', v)}
                placeholder={form.billMode === 'dollar' ? 'e.g. 150' : 'e.g. 900'}
                unit={form.billMode === 'dollar' ? '$ / mo' : 'kWh / mo'}
                min={1}
              />
              {form.billMode === 'dollar' && form.billValue && (
                <p className="text-xs text-navy-500 mt-2">
                  ≈ {Math.round((parseFloat(form.billValue) / 0.15))} kWh/month at ~$0.15/kWh
                </p>
              )}
              {form.billMode === 'kwh' && form.billValue && (
                <p className="text-xs text-navy-500 mt-2">
                  ≈ ${Math.round(parseFloat(form.billValue) * 0.15)}/month at ~$0.15/kWh
                </p>
              )}
            </Field>

            {/* Appliances */}
            <Field label="Do you have any high-usage appliances or tech?" hint="Optional. Helps size the system for your actual load.">
              <div className="space-y-2">
                {APPLIANCES.map(({ key, label, kwhPerMonth }) => (
                  <div key={key} className="space-y-2">
                    <Choice active={form.appliances.includes(key)} onClick={() => toggle('appliances', key)}>
                      <span className="flex items-center justify-between gap-2">
                        <span className="flex items-center gap-2">
                          <span className={`w-5 h-5 rounded-md border flex items-center justify-center ${form.appliances.includes(key) ? 'bg-amber-500 border-amber-500' : 'border-navy-900/20'}`}>
                            {form.appliances.includes(key) && <Check size={14} className="text-white" />}
                          </span>
                          {label}
                        </span>
                        <span className="text-xs text-navy-400 font-normal">~{kwhPerMonth} kWh/mo each</span>
                      </span>
                    </Choice>
                    {form.appliances.includes(key) && (
                      <div className="ml-7 pl-2 border-l-2 border-amber-500/30 flex items-center gap-3">
                        <label className="text-sm font-semibold text-navy-700">How many?</label>
                        <div className="flex items-center gap-2">
                          {[1, 2, 3].map((n) => (
                            <button
                              key={n}
                              type="button"
                              onClick={() => setApplianceCount(key, n)}
                              className={`w-9 h-9 rounded-xl border text-sm font-bold transition-all ${(parseInt(form.applianceCounts[key] || 1) === n) ? 'bg-amber-500 border-amber-500 text-white' : 'bg-white border-navy-900/10 text-navy-700'}`}
                            >
                              {n}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {form.appliances.length > 0 && (
                <div className="mt-3 text-sm text-navy-600 bg-amber-500/5 rounded-xl px-4 py-2.5">
                  Estimated extra load from selected appliances:{' '}
                  <strong>
                    {form.appliances.reduce((sum, key) => {
                      const appl = APPLIANCES.find((a) => a.key === key);
                      const count = parseInt(form.applianceCounts[key] || 1);
                      return sum + (appl ? appl.kwhPerMonth * count : 0);
                    }, 0)}{' '}
                    kWh/month
                  </strong>
                </div>
              )}
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
