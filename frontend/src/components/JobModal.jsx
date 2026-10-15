import React, { useState } from 'react';
import { createJob } from '../api';

export default function JobModal({ isOpen, onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [description, setDescription] = useState('');
  const [reqSkills, setReqSkills] = useState('');
  const [prefSkills, setPrefSkills] = useState('');
  const [minExp, setMinExp] = useState(2);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createJob({
        title,
        department,
        description,
        required_skills: reqSkills.split(',').map((s) => s.trim()).filter(Boolean),
        preferred_skills: prefSkills.split(',').map((s) => s.trim()).filter(Boolean),
        min_experience_years: parseInt(minExp, 10),
      });
      onCreated();
      onClose();
    } catch (err) {
      alert('Error creating job: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl p-6 text-slate-800">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-200">
          <h3 className="text-base font-bold text-slate-900">Create New Job Opening</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Job Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Machine Learning Engineer"
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Department</label>
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="e.g. AI Systems / Infrastructure"
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Job Description *</label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe core responsibilities..."
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Required Skills (comma separated)</label>
              <input
                type="text"
                value={reqSkills}
                onChange={(e) => setReqSkills(e.target.value)}
                placeholder="Python, FastAPI, SQL"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Preferred Skills</label>
              <input
                type="text"
                value={prefSkills}
                onChange={(e) => setPrefSkills(e.target.value)}
                placeholder="Docker, Kubernetes, Redis"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Min Experience (Years)</label>
            <input
              type="number"
              min="0"
              value={minExp}
              onChange={(e) => setMinExp(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition"
            >
              {loading ? 'Creating...' : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
