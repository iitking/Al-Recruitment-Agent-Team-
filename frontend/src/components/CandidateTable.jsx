import React from 'react';

export default function CandidateTable({ candidates, jobs, onInspect }) {
  const getStatusBadge = (status) => {
    const map = {
      Applied: 'bg-slate-100 text-slate-700',
      RecruiterReview: 'bg-amber-100 text-amber-800',
      ApprovedForInterview: 'bg-emerald-100 text-emerald-800',
      AwaitingAvailability: 'bg-emerald-100 text-emerald-800',
      Scheduled: 'bg-indigo-100 text-indigo-800',
      InterviewCompleted: 'bg-purple-100 text-purple-800',
      NeedsManualReview: 'bg-rose-100 text-rose-800',
      Rejected: 'bg-rose-100 text-rose-800',
    };
    return (
      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${map[status] || 'bg-slate-100 text-slate-700'}`}>
        {status}
      </span>
    );
  };

  const getRecBadge = (rec) => {
    if (rec === 'Strong Match') return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    if (rec === 'Potential Match') return 'bg-blue-50 text-blue-700 border border-blue-200';
    if (rec === 'Needs Clarification') return 'bg-amber-50 text-amber-700 border border-amber-200';
    return 'bg-slate-50 text-slate-700 border border-slate-200';
  };

  if (!candidates || candidates.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        No candidate applications found. Upload resumes to initiate screening.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm text-slate-600">
        <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
          <tr>
            <th className="px-6 py-3.5">Candidate</th>
            <th className="px-6 py-3.5">Target Role</th>
            <th className="px-6 py-3.5">Match Score</th>
            <th className="px-6 py-3.5">Agent Recommendation</th>
            <th className="px-6 py-3.5">Workflow Status</th>
            <th className="px-6 py-3.5 text-right">Review Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {candidates.map((c) => {
            const jobTitle = jobs.find((j) => j.id === c.job_id)?.title || 'Role';
            return (
              <tr key={c.id} className="hover:bg-slate-50/75 transition">
                <td className="px-6 py-4">
                  <div className="font-semibold text-slate-900">{c.name || 'Candidate'}</div>
                  <div className="text-xs text-slate-400">{c.email || 'No email parsed'}</div>
                </td>
                <td className="px-6 py-4 text-slate-700">{jobTitle}</td>
                <td className="px-6 py-4 font-bold text-slate-900">
                  {c.latest_score !== null && c.latest_score !== undefined ? `${c.latest_score}%` : 'Pending'}
                </td>
                <td className="px-6 py-4">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${getRecBadge(c.latest_recommendation)}`}>
                    {c.latest_recommendation || 'Processing'}
                  </span>
                </td>
                <td className="px-6 py-4">{getStatusBadge(c.status)}</td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => onInspect(c)}
                    className="text-xs bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 font-medium px-3 py-1.5 rounded-lg border border-slate-200 transition"
                  >
                    Inspect & Review
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
