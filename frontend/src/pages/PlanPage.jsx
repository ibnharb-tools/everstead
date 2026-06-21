import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { everstead } from '../api/everstead';
import { ResultsView } from '../components/results/ResultsView';

export default function PlanPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await everstead.getRetrofit(id, token);
        setData(res);
      } catch (err) {
        setError(err.message || 'We could not find that saved home.');
      }
    })();
  }, [id, token]);

  return (
    <div className="container-px py-10 md:py-14 min-h-[70vh]">
      <Link to="/dashboard" data-testid="plan-back" className="inline-flex items-center gap-2 text-navy-600 font-semibold hover:text-navy-900">
        <ArrowLeft size={18} /> Back to my homes
      </Link>

      {error ? (
        <div className="mt-10 rounded-3xl bg-white border border-navy-900/5 p-10 text-center">
          <p className="text-navy-700">{error}</p>
        </div>
      ) : !data ? (
        <div className="flex items-center justify-center py-24 text-navy-500">
          <Loader2 className="animate-spin" /> <span className="ml-2">Loading your plan...</span>
        </div>
      ) : (
        <div className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-600">{data.label}</p>
          <div className="mt-4">
            <ResultsView assessment={data.assessment} />
          </div>
        </div>
      )}
    </div>
  );
}
