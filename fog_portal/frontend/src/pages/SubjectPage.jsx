import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { getSubject, getProgression, getProgressionReport } from '../utils/api';
import { MedBadge, TriggerBadge, QualityBadge, Spinner, EmptyState } from '../components/ui';

// ── FOG Burden Progression Chart ───────────────────────────────────────────────
function ProgressionChart({ visits }) {
  const onVisits  = visits.filter(v => v.medication_status === 'on');
  const offVisits = visits.filter(v => v.medication_status === 'off');

  const traces = [];

  if (onVisits.length) {
    traces.push({
      x: onVisits.map(v => `Visit ${v.visit_number}`),
      y: onVisits.map(v => v.fog_burden_pct),
      type: 'scatter', mode: 'lines+markers',
      name: 'Medication ON',
      line:   { color: '#10B981', width: 2.5 },
      marker: { color: '#10B981', size: 9, symbol: 'circle' },
      hovertemplate: 'Visit %{x}<br>FOG Burden: <b>%{y:.1f}%</b><br>Med: ON<extra></extra>',
    });
  }

  if (offVisits.length) {
    traces.push({
      x: offVisits.map(v => `Visit ${v.visit_number}`),
      y: offVisits.map(v => v.fog_burden_pct),
      type: 'scatter', mode: 'lines+markers',
      name: 'Medication OFF',
      line:   { color: '#EF4444', width: 2.5, dash: 'dash' },
      marker: { color: '#EF4444', size: 9, symbol: 'diamond' },
      hovertemplate: 'Visit %{x}<br>FOG Burden: <b>%{y:.1f}%</b><br>Med: OFF<extra></extra>',
    });
  }

  // All visits combined line
  traces.unshift({
    x: visits.map(v => `Visit ${v.visit_number}`),
    y: visits.map(v => v.fog_burden_pct),
    type: 'scatter', mode: 'lines',
    name: 'All Visits',
    line: { color: 'rgba(45,125,210,0.25)', width: 1.5 },
    showlegend: false,
    hoverinfo: 'none',
  });

  return (
    <Plot
      data={traces}
      layout={{
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: { color: '#4A6580', gridcolor: '#1E3454', zerolinecolor: '#1E3454' },
        yaxis: {
          title: { text: 'FOG Burden (%)', font: { size: 11 } },
          color: '#4A6580', gridcolor: '#1E3454', zerolinecolor: '#1E3454',
          rangemode: 'tozero',
        },
        legend: { orientation: 'h', x: 0, y: -0.2, bgcolor: 'transparent' },
        margin: { t: 10, b: 50, l: 55, r: 20 },
        hovermode: 'closest',
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 260 }}
      useResizeHandler
    />
  );
}

// ── Trigger Distribution Stacked Bar ───────────────────────────────────────────
function TriggerProgressionChart({ visits }) {
  const labels = ['StartHesitation', 'Turn', 'Walking'];
  const colors = ['#E53E3E', '#2D7DD2', '#10B981'];
  const names  = ['Start Hesitation', 'Turn', 'Walking'];

  const xLabels = visits.map(v => `Visit ${v.visit_number}`);

  const traces = labels.map((lbl, i) => ({
    x: xLabels,
    y: visits.map(v => v.trigger_counts?.[lbl] || 0),
    type: 'bar',
    name: names[i],
    marker: { color: colors[i], opacity: 0.85 },
    hovertemplate: `${names[i]}: <b>%{y}</b> episodes<extra></extra>`,
  }));

  return (
    <Plot
      data={traces}
      layout={{
        barmode: 'stack',
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: { color: '#4A6580', gridcolor: '#1E3454' },
        yaxis: {
          title: { text: 'Episode Count', font: { size: 11 } },
          color: '#4A6580', gridcolor: '#1E3454',
        },
        legend: { orientation: 'h', x: 0, y: -0.2, bgcolor: 'transparent' },
        margin: { t: 10, b: 50, l: 55, r: 20 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 240 }}
      useResizeHandler
    />
  );
}

// ── Main Subject Profile Page ──────────────────────────────────────────────────
export default function SubjectPage() {
  const { subjectId } = useParams();
  const navigate      = useNavigate();

  const [profile,      setProfile]      = useState(null);
  const [progression,  setProgression]  = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [activeTab,    setActiveTab]    = useState('overview');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getSubject(subjectId),
      getProgression(subjectId).catch(() => null),
    ]).then(([p, prog]) => {
      setProfile(p.data);
      if (prog) setProgression(prog.data);
    }).finally(() => setLoading(false));
  }, [subjectId]);

  if (loading) return (
    <div className="page-content" style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 60 }}>
      <Spinner size={24} /> <span style={{ color: 'var(--text-secondary)' }}>Loading patient…</span>
    </div>
  );

  if (!profile) return (
    <div className="page-content">
      <div className="alert alert-danger">Patient not found.</div>
    </div>
  );

  const { subject, sessions } = profile;
  const hasProgression = progression && progression.visits?.length >= 2;

  return (
    <div className="page-content fade-in">

      {/* Header */}
      <div className="page-header-row page-header">
        <div>
          <h1>
            Patient Profile
            <span style={{ fontFamily: 'var(--font-data)', fontSize: 15, color: 'var(--text-muted)', marginLeft: 12 }}>
              {subjectId}
            </span>
          </h1>
          <p>{subject.total_visits} visit{subject.total_visits !== 1 ? 's' : ''} recorded</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate('/upload')}
          >
            ⬆ New Upload
          </button>
          {hasProgression && (
            <a href={getProgressionReport(subjectId)} className="btn btn-primary btn-sm" download>
              📄 Progression Report
            </a>
          )}
        </div>
      </div>

      {/* Demographics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Age',             value: subject.age ?? '—', unit: subject.age ? 'yrs' : '' },
          { label: 'Sex',             value: subject.sex ?? '—' },
          { label: 'Years Since Dx',  value: subject.years_since_dx ?? '—' },
          { label: 'NFOGQ Score',     value: subject.nfogq_score ?? '—' },
          { label: 'UPDRS III (ON)',  value: subject.updrs_on ?? '—' },
          { label: 'UPDRS III (OFF)', value: subject.updrs_off ?? '—' },
        ].map(m => (
          <div className="metric-card" key={m.label}>
            <div className="metric-label">{m.label}</div>
            <div className="metric-value" style={{ fontSize: 22 }}>
              {m.value}{m.unit && <span className="metric-unit">{m.unit}</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`}   onClick={() => setActiveTab('overview')}>   Visit History </button>
        {hasProgression && (
          <button className={`tab ${activeTab === 'progression' ? 'active' : ''}`} onClick={() => setActiveTab('progression')}> Progression </button>
        )}
      </div>

      {/* ── Visit History Tab ── */}
      {activeTab === 'overview' && (
        <div className="fade-in">
          {sessions.length === 0 ? (
            <div className="card">
              <EmptyState icon="📭" title="No sessions yet" />
            </div>
          ) : (
            (() => {
              // Group sessions by visit
              const visitGroups = {};
              sessions.forEach(s => {
                if (!visitGroups[s.visit_number]) {
                  visitGroups[s.visit_number] = [];
                }
                visitGroups[s.visit_number].push(s);
              });

              return Object.keys(visitGroups)
                .sort((a, b) => Number(a) - Number(b))
                .map(visitNum => (
                  <div key={visitNum} className="card" style={{ marginBottom: 20 }}>
                    <div className="card-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>Visit {visitNum}</span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 400 }}>
                        {visitGroups[visitNum].length} session{visitGroups[visitNum].length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <table className="data-table" style={{ margin: 0 }}>
                      <thead>
                        <tr>
                          <th>Medication</th>
                          <th>Date</th>
                          <th>Episodes</th>
                          <th>FOG Duration (s)</th>
                          <th>FOG Burden</th>
                          <th>Avg Duration (s)</th>
                          <th>Dominant Trigger</th>
                          <th>Quality</th>
                          <th>Note</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visitGroups[visitNum].map(s => (
                          <tr key={s.id}>
                            <td><MedBadge status={s.medication_status} /></td>
                            <td className="col-text" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                              {new Date(s.upload_timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                            </td>
                            <td>{s.total_fog_episodes}</td>
                            <td>{s.total_fog_duration_s?.toFixed(1)}</td>
                            <td style={{ color: s.fog_burden_pct > 30 ? 'var(--danger)' : s.fog_burden_pct > 15 ? 'var(--warning)' : 'var(--success)' }}>
                              {s.fog_burden_pct?.toFixed(1)}%
                            </td>
                            <td>{s.avg_episode_duration_s?.toFixed(1)}</td>
                            <td><TriggerBadge label={s.dominant_trigger} /></td>
                            <td><QualityBadge quality={s.quality_badge} /></td>
                            <td className="col-text" style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontStyle: 'italic', fontSize: 11 }}>
                              {s.clinical_note || '—'}
                            </td>
                            <td>
                              <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => navigate(`/sessions/${s.id}`)}
                              >
                                View →
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ));
            })()
          )}
        </div>
      )}

      {/* ── Progression Tab ── */}
      {activeTab === 'progression' && hasProgression && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="fade-in">

          {/* Medication delta card */}
          {progression.med_delta && (
            <div className="card" style={{ borderColor: 'var(--border-focus)', background: 'var(--accent-glow)' }}>
              <div className="card-title">Medication Effect Summary</div>
              <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>AVG BURDEN · ON</div>
                  <div style={{ fontFamily: 'var(--font-data)', fontSize: 28, color: 'var(--success)' }}>
                    {progression.med_delta.on_avg_burden}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>AVG BURDEN · OFF</div>
                  <div style={{ fontFamily: 'var(--font-data)', fontSize: 28, color: 'var(--danger)' }}>
                    {progression.med_delta.off_avg_burden}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>DELTA (OFF − ON)</div>
                  <div style={{ fontFamily: 'var(--font-data)', fontSize: 28, color: 'var(--warning)' }}>
                    {progression.med_delta.delta > 0 ? '+' : ''}{progression.med_delta.delta}%
                  </div>
                </div>
                <div style={{ flex: 1, fontSize: 13, color: 'var(--text-secondary)', alignSelf: 'center' }}>
                  {progression.med_delta.delta > 0
                    ? `FOG burden is ${progression.med_delta.delta.toFixed(1)}% higher when OFF medication.`
                    : `FOG burden is similar across medication states.`}
                </div>
              </div>
            </div>
          )}

          {/* FOG burden line chart */}
          <div className="chart-container">
            <div className="section-title">FOG Burden Over Visits</div>
            <ProgressionChart visits={progression.visits} />
          </div>

          {/* Trigger distribution chart */}
          <div className="chart-container">
            <div className="section-title">Trigger Distribution Over Visits</div>
            <TriggerProgressionChart visits={progression.visits} />
          </div>

          {/* Visit comparison table */}
          <div className="card">
            <div className="card-title">Visit-by-Visit Comparison</div>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Visit</th>
                    <th>Date</th>
                    <th>Medication</th>
                    <th>Episodes</th>
                    <th>FOG Burden</th>
                    <th>Avg Duration (s)</th>
                    <th>Start Hesitation</th>
                    <th>Turn</th>
                    <th>Walking</th>
                    <th>Dominant</th>
                  </tr>
                </thead>
                <tbody>
                  {progression.visits.map(v => (
                    <tr key={v.visit_number}>
                      <td style={{ color: 'var(--accent-light)', fontWeight: 600 }}>V{v.visit_number}</td>
                      <td className="col-text">
                        {new Date(v.upload_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      <td><MedBadge status={v.medication_status} /></td>
                      <td>{v.total_fog_episodes}</td>
                      <td style={{ color: v.fog_burden_pct > 30 ? 'var(--danger)' : v.fog_burden_pct > 15 ? 'var(--warning)' : 'var(--success)' }}>
                        {v.fog_burden_pct?.toFixed(1)}%
                      </td>
                      <td>{v.avg_episode_duration_s?.toFixed(1)}</td>
                      <td style={{ color: 'var(--trigger-sh)' }}>{v.trigger_counts?.StartHesitation ?? 0}</td>
                      <td style={{ color: 'var(--trigger-turn)' }}>{v.trigger_counts?.Turn ?? 0}</td>
                      <td style={{ color: 'var(--trigger-walk)' }}>{v.trigger_counts?.Walking ?? 0}</td>
                      <td><TriggerBadge label={v.dominant_trigger} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
