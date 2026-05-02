import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
import {
  getSession, annotateEpisode, getReportUrl, getCsvUrl
} from '../utils/api';
import {
  QualityBadge, MedBadge, TriggerBadge, ConfBars,
  LowConfFlag, AnnotationButtons, MetricCard, Spinner, EmptyState
} from '../components/ui';

// ── FOG Timeline Plot ──────────────────────────────────────────────────────────
function FogTimeline({ windows, episodes }) {
  if (!windows?.length) return null;

  const x      = windows.map(w => w.start_time_s);
  const y      = windows.map(w => w.fog_probability);

  // Episode highlight shapes
  const shapes = episodes.map(ep => ({
    type: 'rect',
    xref: 'x', yref: 'paper',
    x0: ep.start_time_s, x1: ep.end_time_s,
    y0: 0, y1: 1,
    fillcolor: triggerColor(ep.trigger_label),
    opacity: 0.15,
    line: { width: 0 },
  }));

  // Episode vertical markers with labels
  const annotations = episodes.map(ep => ({
    x: (ep.start_time_s + ep.end_time_s) / 2,
    y: 1.05, xref: 'x', yref: 'paper',
    text: `#${ep.episode_index}`,
    showarrow: false,
    font: { size: 10, color: '#8BA5C4', family: 'DM Mono' },
  }));

  return (
    <Plot
      data={[
        {
          x, y,
          type: 'scatter',
          mode: 'lines',
          name: 'FOG Probability',
          line: { color: '#4A9AE8', width: 1.5, shape: 'spline' },
          fill: 'tozeroy',
          fillcolor: 'rgba(45,125,210,0.08)',
          hovertemplate: '<b>%{x:.2f}s</b><br>Prob: %{y:.3f}<extra></extra>',
        },
        {
          x, y: windows.map(() => 0.42),
          type: 'scatter', mode: 'lines',
          name: 'Threshold (0.42)',
          line: { color: '#F59E0B', width: 1, dash: 'dot' },
          hoverinfo: 'none',
        },
      ]}
      layout={{
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        font:  { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: {
          title: { text: 'Time (seconds)', font: { size: 11 } },
          gridcolor: '#1E3454', zerolinecolor: '#1E3454',
          color: '#4A6580',
        },
        yaxis: {
          title: { text: 'FOG Probability', font: { size: 11 } },
          range: [0, 1.1],
          gridcolor: '#1E3454', zerolinecolor: '#1E3454',
          color: '#4A6580',
        },
        shapes,
        annotations,
        legend: {
          orientation: 'h',
          x: 0, y: -0.15,
          font: { size: 11 },
          bgcolor: 'transparent',
        },
        margin: { t: 20, b: 60, l: 55, r: 20 },
        hovermode: 'x unified',
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 260 }}
      useResizeHandler
    />
  );
}

function triggerColor(label) {
  return {
    StartHesitation: 'rgba(229,62,62,0.6)',
    Turn:            'rgba(45,125,210,0.6)',
    Walking:         'rgba(16,185,129,0.6)',
  }[label] || 'rgba(139,165,196,0.3)';
}

// ── Trigger Breakdown Chart ────────────────────────────────────────────────────
function TriggerChart({ episodes }) {
  const counts = { StartHesitation: 0, Turn: 0, Walking: 0 };
  episodes.forEach(ep => { if (ep.trigger_label) counts[ep.trigger_label]++; });
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;

  return (
    <Plot
      data={[{
        type: 'bar',
        orientation: 'h',
        x: [counts.StartHesitation, counts.Turn, counts.Walking],
        y: ['Start Hesitation', 'Turn', 'Walking'],
        text: [
          `${counts.StartHesitation} (${((counts.StartHesitation/total)*100).toFixed(0)}%)`,
          `${counts.Turn} (${((counts.Turn/total)*100).toFixed(0)}%)`,
          `${counts.Walking} (${((counts.Walking/total)*100).toFixed(0)}%)`,
        ],
        textposition: 'outside',
        textfont: { family: 'DM Mono', size: 11, color: '#8BA5C4' },
        marker: {
          color: ['#E53E3E', '#2D7DD2', '#10B981'],
          opacity: 0.85,
        },
        hovertemplate: '<b>%{y}</b>: %{x} episodes<extra></extra>',
      }]}
      layout={{
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        font:  { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: {
          title: { text: 'Episode Count', font: { size: 11 } },
          gridcolor: '#1E3454', zerolinecolor: '#1E3454', color: '#4A6580',
        },
        yaxis: { color: '#8BA5C4', gridcolor: '#1E3454' },
        margin: { t: 10, b: 40, l: 120, r: 80 },
        bargap: 0.4,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 180 }}
      useResizeHandler
    />
  );
}

// ── Episodes Table ─────────────────────────────────────────────────────────────
function EpisodesTable({ episodes, onAnnotate }) {
  if (!episodes?.length) {
    return (
      <EmptyState
        icon="✅"
        title="No FOG Episodes Detected"
        desc="The model found no freezing of gait events in this recording."
      />
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Start (s)</th>
            <th>End (s)</th>
            <th>Duration (s)</th>
            <th>Trigger</th>
            <th>Confidence</th>
            <th>Flag</th>
            <th>Annotation</th>
          </tr>
        </thead>
        <tbody>
          {episodes.map(ep => (
            <tr key={ep.id}>
              <td style={{ color: 'var(--text-muted)' }}>{ep.episode_index}</td>
              <td>{ep.start_time_s.toFixed(2)}</td>
              <td>{ep.end_time_s.toFixed(2)}</td>
              <td style={{ color: 'var(--accent-light)' }}>{ep.duration_s.toFixed(2)}</td>
              <td><TriggerBadge label={ep.trigger_label} /></td>
              <td>
                <ConfBars
                  sh={ep.conf_start_hesitation}
                  turn={ep.conf_turn}
                  walk={ep.conf_walking}
                />
              </td>
              <td><LowConfFlag flag={ep.low_confidence_flag} /></td>
              <td>
                <AnnotationButtons
                  current={ep.annotation}
                  onSelect={ann => onAnnotate(ep.id, ann)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Dashboard Page ────────────────────────────────────────────────────────
export default function SessionPage() {
  const { sessionId } = useParams();
  const location      = useLocation();
  const navigate      = useNavigate();

  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const isFresh = location.state?.fresh;

  useEffect(() => {
    setLoading(true);
    getSession(sessionId)
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load session data.'))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleAnnotate = async (episodeId, annotation) => {
    try {
      await annotateEpisode(sessionId, episodeId, annotation);
      setData(prev => ({
        ...prev,
        episodes: prev.episodes.map(ep =>
          ep.id === episodeId ? { ...ep, annotation } : ep
        ),
      }));
    } catch { /* silent */ }
  };

  if (loading) return (
    <div className="page-content" style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 60 }}>
      <Spinner size={24} /> <span style={{ color: 'var(--text-secondary)' }}>Loading session…</span>
    </div>
  );

  if (error) return (
    <div className="page-content">
      <div className="alert alert-danger">{error}</div>
    </div>
  );

  const { session, subject, windows, episodes } = data;

  return (
    <div className="page-content fade-in">

      {/* Header */}
      <div className="page-header-row page-header">
        <div>
          <h1>
            Session Analysis
            <span style={{ fontFamily: 'var(--font-data)', fontSize: 15, color: 'var(--text-muted)', marginLeft: 12 }}>
              {session.subject_id}
            </span>
          </h1>
          <p>
            Visit {session.visit_number} &nbsp;·&nbsp;
            {new Date(session.upload_timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
            &nbsp;·&nbsp; <MedBadge status={session.medication_status} />
            &nbsp;·&nbsp; <QualityBadge quality={session.quality_badge} />
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate(`/subjects/${session.subject_id}`)}
          >
            👤 Patient Profile
          </button>
          <a href={getCsvUrl(sessionId)} className="btn btn-secondary btn-sm" download>
            ⬇ Export CSV
          </a>
          <a href={getReportUrl(sessionId)} className="btn btn-primary btn-sm" download>
            📄 Download Report
          </a>
        </div>
      </div>

      {isFresh && (
        <div className="alert alert-success" style={{ marginBottom: 24 }}>
          <span>✓</span>
          <div>Analysis complete. {episodes.length} FOG episode{episodes.length !== 1 ? 's' : ''} detected.</div>
        </div>
      )}

      {/* Metric cards */}
      <div className="metric-grid" style={{ marginBottom: 24 }}>
        <MetricCard label="FOG Episodes"    value={session.total_fog_episodes} />
        <MetricCard label="FOG Duration"    value={session.total_fog_duration_s?.toFixed(1)} unit="s" />
        <MetricCard label="FOG Burden"      value={session.fog_burden_pct?.toFixed(1)} unit="%" accent={session.fog_burden_pct > 30 ? 'var(--danger)' : session.fog_burden_pct > 15 ? 'var(--warning)' : 'var(--success)'} />
        <MetricCard label="Avg Duration"    value={session.avg_episode_duration_s?.toFixed(1)} unit="s" />
        <MetricCard label="Max Duration"    value={session.max_episode_duration_s?.toFixed(1)} unit="s" />
        <MetricCard label="Recording"       value={session.recording_duration_s?.toFixed(0)} unit="s" />
      </div>

      {/* Timeline */}
      <div className="chart-container" style={{ marginBottom: 24 }}>
        <div className="section-title">FOG Probability Timeline</div>
        <FogTimeline windows={windows} episodes={episodes} />
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
          Colored bands indicate detected FOG episodes. Red = Start Hesitation · Blue = Turn · Green = Walking
        </div>
      </div>

      {/* Trigger breakdown + patient info */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20, marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Trigger Breakdown</div>
          {episodes.length > 0
            ? <TriggerChart episodes={episodes} />
            : <EmptyState icon="📊" title="No episodes to chart" />
          }
        </div>

        <div className="card">
          <div className="card-title">Patient Info</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { label: 'Subject ID',       value: subject.id },
              { label: 'Age',              value: subject.age ?? '—' },
              { label: 'Sex',              value: subject.sex ?? '—' },
              { label: 'Years Since Dx',   value: subject.years_since_dx ?? '—' },
              { label: 'UPDRS III (On)',   value: subject.updrs_on ?? '—' },
              { label: 'UPDRS III (Off)',  value: subject.updrs_off ?? '—' },
              { label: 'NFOGQ Score',      value: subject.nfogq_score ?? '—' },
              { label: 'Total Visits',     value: subject.total_visits },
            ].map(r => (
              <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'var(--text-muted)' }}>{r.label}</span>
                <span style={{ fontFamily: 'var(--font-data)', color: 'var(--text-primary)' }}>{r.value}</span>
              </div>
            ))}
          </div>
          {session.clinical_note && (
            <>
              <div style={{ height: 1, background: 'var(--border)', margin: '14px 0' }} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>CLINICAL NOTE</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                {session.clinical_note}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Episodes table */}
      <div className="card">
        <div className="card-title">
          Detected Episodes
          {episodes.some(ep => ep.low_confidence_flag) && (
            <span className="badge badge-warning" style={{ marginLeft: 10, fontWeight: 400 }}>
              ⚠ Some episodes have low trigger confidence
            </span>
          )}
        </div>
        <EpisodesTable episodes={episodes} onAnnotate={handleAnnotate} />
      </div>
    </div>
  );
}
