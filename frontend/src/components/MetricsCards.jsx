import React from 'react';

export default function MetricsCards({ metrics }) {
  const cards = [
    {
      title: 'Active Openings',
      value: metrics.active_jobs ?? 0,
      icon: 'briefcase',
      color: 'bg-indigo-50 text-indigo-600',
    },
    {
      title: 'Total Applicants',
      value: metrics.total_candidates ?? 0,
      icon: 'users',
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Avg Screen Score',
      value: metrics.avg_screening_score ? `${metrics.avg_screening_score}%` : '--',
      icon: 'award',
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Interviews Booked',
      value: metrics.scheduled_interviews_count ?? 0,
      icon: 'calendar',
      color: 'bg-violet-50 text-violet-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {cards.map((c, i) => (
        <div key={i} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{c.title}</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{c.value}</p>
          </div>
          <div className={`p-3 rounded-lg ${c.color}`}>
            <span className="font-bold text-sm">#</span>
          </div>
        </div>
      ))}
    </div>
  );
}
