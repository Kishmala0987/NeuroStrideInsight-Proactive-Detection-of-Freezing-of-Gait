import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { uploadSession } from '../utils/api';
import { Spinner } from '../components/ui';

// ── File drop zone component ───────────────────────────────────────────────────
function FileZone({ label, hint, accept, file, onFile }) {
  const onDrop = useCallback(files => { if (files[0]) onFile(files[0]); }, [onFile]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept, multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? 'drag-active' : ''} ${file ? 'file-ready' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-icon">{file ? '✅' : '📂'}</div>
      <div className="dropzone-text">{label}</div>
      <div className="dropzone-hint">{hint}</div>
      {file && <div className="dropzone-filename">📄 {file.name}</div>}
    </div>
  );
}

// ── Pipeline step display ──────────────────────────────────────────────────────
const STEPS = [
  { icon: '🔍', label: 'Validating CSV',         desc: 'Checking signal quality and required columns' },
  { icon: '🧠', label: 'FOG Detection',           desc: 'CNN+BiLSTM+FiLM model — sliding window inference' },
  { icon: '🏷',  label: 'Trigger Classification', desc: 'Classifying episode triggers: Hesitation / Turn / Walking' },
  { icon: '📈', label: 'Deriving Metrics',        desc: 'Computing FOG burden, episode summary, and statistics' },
  { icon: '💾', label: 'Saving Results',          desc: 'Persisting to database' },
];

function PipelineProgress({ step }) {
  return (
    <div className="pipeline-steps fade-in">
      {STEPS.map((s, i) => (
        <div
          key={i}
          className={`pipeline-step ${i === step ? 'active' : i < step ? 'done' : ''}`}
        >
          <div className="step-icon">
            {i < step ? '✓' : i === step ? <Spinner size={16} /> : s.icon}
          </div>
          <div>
            <div className="step-label">{s.label}</div>
            <div className="step-desc">{s.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main Upload Page ───────────────────────────────────────────────────────────
export default function UploadPage() {
  const navigate = useNavigate();

  const [csvFile,         setCsvFile]         = useState(null);
  const [medicationStatus, setMedicationStatus] = useState('');
  const [clinicalNote,    setClinicalNote]    = useState('');

  const [pipelineStep,    setPipelineStep]    = useState(-1);  // -1 = idle
  const [error,           setError]           = useState(null);
  const [success,         setSuccess]         = useState(null);
  const [uploading,       setUploading]       = useState(false);

  const canSubmit = csvFile && medicationStatus;

  const handleSubmit = async () => {
    setError(null);
    setSuccess(null);
    setUploading(true);
    setPipelineStep(0);

    const fd = new FormData();
    fd.append('csv_file', csvFile);
    fd.append('medication_status', medicationStatus);
    if (clinicalNote) fd.append('clinical_note', clinicalNote);

    const stepInterval = setInterval(() => {
      setPipelineStep(prev => (prev < STEPS.length - 2 ? prev + 1 : prev));
    }, 1200);

    try {
      const res = await uploadSession(fd);
      clearInterval(stepInterval);
      setPipelineStep(STEPS.length);
      setSuccess(`✓ Analysis complete! Subject ${res.data.subject_id}, Visit ${res.data.visit_number}`);
      await new Promise(r => setTimeout(r, 1000));
      navigate(`/subjects/${res.data.subject_id}`, {
        state: { fresh: true, summary: res.data }
      });
    } catch (err) {
      clearInterval(stepInterval);
      setPipelineStep(-1);
      setError(err.response?.data?.detail || 'Upload failed. Please check your files and try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-content fade-in">
      <div className="page-header">
        <h1>New Session Upload</h1>
        <p>Upload an IMU recording to run the full FOG detection and analysis pipeline</p>
      </div>

      <div style={{ maxWidth: 600, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Recording CSV upload */}
        <div className="card">
          <div className="card-title">Recording File</div>
          <FileZone
            label="Drop accelerometer CSV here"
            hint="File must be named as Series ID (e.g. 011322847a.csv) · AccV, AccML, AccAP required"
            accept={{ 'text/csv': ['.csv'] }}
            file={csvFile}
            onFile={setCsvFile}
          />
        </div>

        {/* Session info */}
        <div className="card">
          <div className="card-title">Session Details</div>

          <div className="form-group">
            <label className="form-label">Medication Status <span style={{ color: 'var(--danger)' }}>*</span></label>
            <select
              className="form-input"
              value={medicationStatus}
              onChange={e => setMedicationStatus(e.target.value)}
              required
            >
              <option value="">Select medication status</option>
              <option value="on">ON medication</option>
              <option value="off">OFF medication</option>
            </select>
            <div className="form-hint">Whether the patient was ON or OFF medication during this recording</div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Clinical Note <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
            <textarea
              className="form-input"
              placeholder="Any observations about this recording session..."
              value={clinicalNote}
              onChange={e => setClinicalNote(e.target.value)}
            />
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="alert alert-danger">
            <span>⚠</span>
            <div>{error}</div>
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            <span>✓</span>
            <div>{success}</div>
          </div>
        )}

        {/* Pipeline progress */}
        {(uploading || pipelineStep >= 0) && (
          <div className="card">
            <div className="card-title">Pipeline Progress</div>
            <PipelineProgress step={pipelineStep} />
          </div>
        )}

        {/* Submit button */}
        <button
          className="btn btn-primary btn-lg"
          onClick={handleSubmit}
          disabled={!canSubmit}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {uploading ? <><Spinner size={16} /> Running Pipeline…</> : '▶ Run Analysis'}
        </button>
      </div>
    </div>
  );
}
