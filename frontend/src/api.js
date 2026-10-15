/**
 * Frontend API client for AI Recruitment Agent Team backend
 */

const API_BASE = '/api';

export async function fetchDashboardSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchJobs() {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function createJob(jobData) {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(jobData),
  });
  if (!res.ok) throw new Error('Failed to create job opening');
  return res.json();
}

export async function fetchCandidates(jobId = '') {
  const url = jobId ? `${API_BASE}/candidates?job_id=${jobId}` : `${API_BASE}/candidates`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json();
}

export async function fetchCandidateReport(candidateId) {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/report`);
  if (!res.ok) throw new Error('Failed to fetch screening report');
  return res.json();
}

export async function uploadResumes(jobId, files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  const res = await fetch(`${API_BASE}/jobs/${jobId}/resumes`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload resumes');
  return res.json();
}

export async function submitRecruiterReview(candidateId, reviewData) {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reviewData),
  });
  if (!res.ok) throw new Error('Failed to submit review');
  return res.json();
}

export async function draftCommunication(candidateId, templateType = 'interview_invitation') {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/communications/draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_type: templateType }),
  });
  if (!res.ok) throw new Error('Failed to draft email');
  return res.json();
}

export async function sendCommunication(candidateId, emailData) {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/communications/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(emailData),
  });
  if (!res.ok) throw new Error('Failed to send email');
  return res.json();
}

export async function suggestInterviewSlots(candidateId, interviewerEmail = 'recruiter@company.com') {
  const res = await fetch(`${API_BASE}/interviews/suggest-slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ candidate_id: candidateId, interviewer_email: interviewerEmail }),
  });
  if (!res.ok) throw new Error('Failed to suggest slots');
  return res.json();
}

export async function bookInterview(bookingData) {
  const res = await fetch(`${API_BASE}/interviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookingData),
  });
  if (!res.ok) throw new Error('Failed to book interview');
  return res.json();
}
