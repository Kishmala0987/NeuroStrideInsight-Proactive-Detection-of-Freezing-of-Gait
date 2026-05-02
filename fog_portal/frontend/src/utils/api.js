import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min — inference can be slow on CPU
});

// ── Upload ─────────────────────────────────────────────────────────────────────
export const uploadSession = (formData, onProgress) =>
  api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });

// ── Sessions ───────────────────────────────────────────────────────────────────
export const getSession      = (id)        => api.get(`/sessions/${id}`);
export const annotateEpisode = (sessionId, episodeId, annotation) =>
  api.patch(`/sessions/${sessionId}/episodes/${episodeId}/annotate`, { annotation });
export const getReportUrl    = (sessionId) => `/api/sessions/${sessionId}/report`;
export const getCsvUrl       = (sessionId) => `/api/sessions/${sessionId}/export-csv`;

// ── Subjects ───────────────────────────────────────────────────────────────────
export const listSubjects         = ()          => api.get('/subjects/');
export const getSubject           = (id)        => api.get(`/subjects/${id}`);
export const getProgression       = (id)        => api.get(`/subjects/${id}/progression`);
export const getProgressionReport = (id)        => `/api/subjects/${id}/report`;

// ── Statistics ─────────────────────────────────────────────────────────────────
export const getStats = () => api.get('/stats/');

// ── Health ─────────────────────────────────────────────────────────────────────
export const getHealth = () => api.get('/health');

export default api;
