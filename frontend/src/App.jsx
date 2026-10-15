import React, { useState, useEffect } from 'react';
import MetricsCards from './components/MetricsCards';
import CandidateTable from './components/CandidateTable';
import CandidateDrawer from './components/CandidateDrawer';
import JobModal from './components/JobModal';
import {
  fetchDashboardSummary,
  fetchJobs,
  fetchCandidates,
  uploadResumes
} from './api';

export default function App() {
  const [metrics, setMetrics] = useState({});
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [activeCandidate, setActiveCandidate] = useState(null);
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [auditEvents, setAuditEvents] = useState([]);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      const summary = await fetchDashboardSummary();
      setMetrics(summary);
      setAuditEvents(summary.recent_events || []);

      const jobList = await fetchJobs();
      setJobs(jobList);

      const candList = await fetchCandidates(selectedJobId);
      setCandidates(candList);
    } catch (err) {
      console.error('Error loading data:', err);
    }
  };

  const handleJobFilterChange = async (jobId) => {
    setSelectedJobId(jobId);
    try {
      const candList = await fetchCandidates(jobId);
      setCandidates(candList);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    let targetJob = selectedJobId;
    if (!targetJob && jobs.length > 0) {
      targetJob = jobs[0].id;
    }
    if (!targetJob) {
      alert('Please create a job opening first.');
      setIsJobModalOpen(true);
      return;
    }

    try {
      await uploadResumes(targetJob, files);
      alert('Resumes uploaded and screened successfully!');
      loadAllData();
    } catch (err) {
      alert('Upload error: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md font-bold text-lg">
              AI
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 leading-tight">AI Recruitment Agent Team</h1>
              <p className="text-xs text-slate-500">Autonomous Resume Screening to Interview Scheduling</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>5 Specialized Agents Active</span>
            </div>
            <button
              onClick={() => setIsJobModalOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg shadow-sm transition"
            >
              + Create Opening
            </button>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex-1">
        <MetricsCards metrics={metrics} />

        {/* Filter and Upload Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Filter By Role:</label>
            <select
              value={selectedJobId}
              onChange={(e) => handleJobFilterChange(e.target.value)}
              className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="">All Job Openings</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.candidate_count || 0})
                </option>
              ))}
            </select>
          </div>

          <div>
            <input
              type="file"
              id="react-resume-upload"
              multiple
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={handleFileUpload}
            />
            <button
              onClick={() => document.getElementById('react-resume-upload').click()}
              className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition shadow-sm"
            >
              Upload Resumes (PDF / DOCX)
            </button>
          </div>
        </div>

        {/* Pipeline Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-8">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <h2 className="text-base font-semibold text-slate-900">Candidate Pipeline & Agent Screening</h2>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-200 text-slate-700 rounded-full">
              {candidates.length} candidates
            </span>
          </div>

          <CandidateTable
            candidates={candidates}
            jobs={jobs}
            onInspect={(cand) => setActiveCandidate(cand)}
          />
        </div>

        {/* Audit Trail */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-900">Live Agent Audit Trail</h3>
            <span className="text-xs text-slate-400">Tamper-evident workflow events</span>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
            {auditEvents.map((e) => (
              <div key={e.id} className="text-xs p-2.5 bg-slate-50 border border-slate-100 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-900">[{e.actor_type.toUpperCase()}]</span>{' '}
                  <span className="text-slate-700">{e.event_type}</span>{' '}
                  <span className="text-slate-400">→ {e.new_status}</span>
                </div>
                <span className="text-[10px] text-slate-400">{new Date(e.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Drawer */}
      {activeCandidate && (
        <CandidateDrawer
          candidate={activeCandidate}
          onClose={() => setActiveCandidate(null)}
          onRefresh={loadAllData}
        />
      )}

      {/* Job Modal */}
      <JobModal
        isOpen={isJobModalOpen}
        onClose={() => setIsJobModalOpen(false)}
        onCreated={loadAllData}
      />
    </div>
  );
}
