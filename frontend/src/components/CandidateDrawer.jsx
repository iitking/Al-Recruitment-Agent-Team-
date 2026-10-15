import React, { useState, useEffect } from 'react';
import {
  fetchCandidateReport,
  submitRecruiterReview,
  draftCommunication,
  sendCommunication,
  suggestInterviewSlots,
  bookInterview
} from '../api';

export default function CandidateDrawer({ candidate, onClose, onRefresh }) {
  const [report, setReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(true);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  useEffect(() => {
    if (candidate) {
      loadReport();
      loadDraft();
    }
  }, [candidate]);

  const loadReport = async () => {
    setLoadingReport(true);
    try {
      const data = await fetchCandidateReport(candidate.id);
      setReport(data);
    } catch (e) {
      console.warn('Report not generated yet', e);
    } finally {
      setLoadingReport(false);
    }
  };

  const loadDraft = async () => {
    try {
      const data = await draftCommunication(candidate.id, 'interview_invitation');
      setEmailSubject(data.subject);
      setEmailBody(data.body);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReview = async (decision) => {
    try {
      await submitRecruiterReview(candidate.id, {
        decision,
        recruiter_name: 'Lead Recruiter',
        notes: `Reviewed in recruiter drawer: ${decision}`,
      });
      setStatusMsg(`Decision '${decision}' recorded!`);
      onRefresh();
    } catch (err) {
      alert('Review submission failed: ' + err.message);
    }
  };

  const handleSendEmail = async () => {
    try {
      await sendCommunication(candidate.id, {
        subject: emailSubject,
        body: emailBody,
      });
      setStatusMsg('Email dispatched by communication agent!');
      onRefresh();
    } catch (err) {
      alert('Email failed: ' + err.message);
    }
  };

  const handleFindSlots = async () => {
    setLoadingSlots(true);
    try {
      const res = await suggestInterviewSlots(candidate.id);
      setSlots(res.suggested_slots || []);
    } catch (err) {
      alert('Slots error: ' + err.message);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleBookSlot = async (slot) => {
    try {
      const booking = await bookInterview({
        candidate_id: candidate.id,
        interviewer_email: slot.interviewer_email,
        start_time: slot.start_time,
        end_time: slot.end_time,
        title: 'Technical Screen Interview',
      });
      alert(`Interview Booked Successfully!\nMeeting Link: ${booking.meeting_link}`);
      onRefresh();
      onClose();
    } catch (err) {
      alert('Booking error: ' + err.message);
    }
  };

  if (!candidate) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h3 className="text-lg font-bold text-slate-900">{candidate.name || 'Candidate'}</h3>
            <p className="text-xs text-slate-500">ID: {candidate.id} | Email: {candidate.email || 'N/A'}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-sm font-bold p-2">✕</button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {statusMsg && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-3 py-2 rounded-lg">
              {statusMsg}
            </div>
          )}

          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">Current Status</span>
              <p className="text-sm font-bold text-slate-900 mt-1">{candidate.status}</p>
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">Match Score</span>
              <p className="text-xl font-bold text-indigo-600 mt-1">
                {report ? `${report.match_score}%` : (candidate.latest_score ? `${candidate.latest_score}%` : '--')}
              </p>
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase">Agent Recommendation</span>
              <p className="text-sm font-semibold text-slate-800 mt-1">
                {report ? report.recommendation : (candidate.latest_recommendation || 'Processing')}
              </p>
            </div>
          </div>

          {/* Evidence Analysis */}
          {report && (
            <div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">Evidence-Based Screening Analysis</h4>
              <p className="text-xs text-slate-500 mb-3">{report.recommendation_rationale}</p>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-600">Matched Requirements & Provenance:</p>
                {report.matched_requirements && report.matched_requirements.length > 0 ? (
                  report.matched_requirements.map((m, idx) => (
                    <div key={idx} className="p-2.5 bg-emerald-50/50 border border-emerald-200 rounded-lg text-xs">
                      <p className="font-semibold text-emerald-950">✓ {m.requirement}</p>
                      <p className="text-slate-600 mt-1 italic pl-3">“{m.evidence}”</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400">No explicit requirements verified.</p>
                )}
              </div>

              {report.missing_or_unclear_requirements && report.missing_or_unclear_requirements.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-slate-600 mb-2">Missing or Unclear in Resume:</p>
                  <div className="flex flex-wrap gap-2">
                    {report.missing_or_unclear_requirements.map((miss, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 text-xs rounded-full font-medium">
                        {miss}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recruiter Decision Bar */}
          <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100">
            <h4 className="text-xs font-bold text-indigo-950 uppercase tracking-wider mb-1">Recruiter Decision</h4>
            <p className="text-xs text-slate-600 mb-3">Consequential decisions require human oversight.</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => handleReview('approved')} className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition">
                Approve for Interview
              </button>
              <button onClick={() => handleReview('clarification_requested')} className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition">
                Request Clarification
              </button>
              <button onClick={() => handleReview('on_hold')} className="bg-slate-600 hover:bg-slate-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition">
                Put On Hold
              </button>
              <button onClick={() => handleReview('rejected')} className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition">
                Reject Candidate
              </button>
            </div>
          </div>

          {/* Email Draft Panel */}
          <div className="border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Candidate Email Draft</h4>
              <button onClick={loadDraft} className="text-xs text-indigo-600 hover:text-indigo-800">Regenerate</button>
            </div>
            <div className="space-y-2">
              <input
                type="text"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
                placeholder="Subject"
                className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <textarea
                rows={4}
                value={emailBody}
                onChange={(e) => setEmailBody(e.target.value)}
                placeholder="Body"
                className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
              />
              <button
                onClick={handleSendEmail}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium px-3.5 py-2 rounded-lg transition"
              >
                Dispatch Email via Agent
              </button>
            </div>
          </div>

          {/* Interview Scheduling Panel */}
          <div className="border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Schedule Interview (Calendar Agent)</h4>
              <button onClick={handleFindSlots} className="text-xs text-indigo-600 hover:text-indigo-800">
                {loadingSlots ? 'Scanning...' : 'Find Available Slots'}
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {slots.map((s, idx) => {
                const dt = new Date(s.start_time);
                return (
                  <div key={idx} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs flex flex-col justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{dt.toLocaleDateString()}</p>
                      <p className="text-slate-500">{dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC</p>
                    </div>
                    <button
                      onClick={() => handleBookSlot(s)}
                      className="mt-2 bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded text-[11px] font-medium transition"
                    >
                      Book Slot
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
