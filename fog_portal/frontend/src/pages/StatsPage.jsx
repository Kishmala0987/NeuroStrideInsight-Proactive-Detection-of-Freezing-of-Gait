import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getStats } from '../utils/api';
import { Spinner, EmptyState, MetricCard } from '../components/ui';

// ── FOG Burden Distribution Histogram ─────────────────────────────────────────
function BurdenHistogram({ data }) {
  return (
    <Plot
      data={[{
        x: data,
        type: 'histogram',
        nbinsx: 20,
        marker: {
          color: 'rgba(45,125,210,0.7)',
          line: { color: '#2D7DD2', width: 1 },
        },
        hovertemplate: 'Burden: %{x:.1f}%<br>Sessions: %{y}<extra></extra>',
      }]}
      layout={{
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: {
          title: { text: 'FOG Burden (%)', font: { size: 11 } },
          color: '#4A6580', gridcolor: '#1E3454',
        },
        yaxis: {
          title: { text: 'Number of Sessions', font: { size: 11 } },
          color: '#4A6580', gridcolor: '#1E3454',
        },
        margin: { t: 10, b: 50, l: 55, r: 20 },
        bargap: 0.05,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 260 }}
      useResizeHandler
    />
  );
}

// ── Trigger Distribution Pie ───────────────────────────────────────────────────
function TriggerPie({ counts }) {
  const labels = ['Start Hesitation', 'Turn', 'Walking'];
  const values = [counts.StartHesitation, counts.Turn, counts.Walking];
  const colors = ['#E53E3E', '#2D7DD2', '#10B981'];

  return (
    <Plot
      data={[{
        type: 'pie',
        labels, values,
        marker: { colors, line: { color: '#0D1B2E', width: 2 } },
        textfont: { family: 'DM Mono', size: 11, color: '#EDF2F7' },
        hovertemplate: '<b>%{label}</b><br>%{value} episodes (%{percent})<extra></extra>',
        hole: 0.45,
      }]}
      layout={{
        paper_bgcolor: 'transparent',
        showlegend: true,
        legend: {
          orientation: 'v', x: 1, y: 0.5,
          font: { family: 'Sora', size: 11, color: '#8BA5C4' },
          bgcolor: 'transparent',
        },
        margin: { t: 10, b: 10, l: 10, r: 10 },
        annotations: [{
          text: `${values.reduce((a,b) => a+b, 0)}<br><span style="font-size:10px">total</span>`,
          x: 0.5, y: 0.5, xref: 'paper', yref: 'paper',
          showarrow: false,
          font: { family: 'DM Mono', size: 16, color: '#EDF2F7' },
        }],
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 260 }}
      useResizeHandler
    />
  );
}

// ── Medication Comparison Bar ──────────────────────────────────────────────────
function MedComparisonChart({ onBurden, offBurden, onCount, offCount }) {
  return (
    <Plot
      data={[
        {
          x: ['ON Medication', 'OFF Medication'],
          y: [onBurden ?? 0, offBurden ?? 0],
          type: 'bar',
          marker: { color: ['#10B981', '#EF4444'], opacity: 0.85 },
          text: [
            onBurden != null ? `${onBurden.toFixed(1)}%` : 'N/A',
            offBurden != null ? `${offBurden.toFixed(1)}%` : 'N/A',
          ],
          textposition: 'outside',
          textfont: { family: 'DM Mono', size: 13, color: '#EDF2F7' },
          hovertemplate: '<b>%{x}</b><br>Avg FOG Burden: %{y:.1f}%<extra></extra>',
          width: 0.4,
        }
      ]}
      layout={{
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { family: 'Sora', color: '#8BA5C4', size: 11 },
        xaxis: { color: '#4A6580', gridcolor: '#1E3454' },
        yaxis: {
          title: { text: 'Avg FOG Burden (%)', font: { size: 11 } },
          color: '#4A6580', gridcolor: '#1E3454',
          rangemode: 'tozero',
        },
        margin: { t: 30, b: 40, l: 55, r: 20 },
        annotations: [
          { x: 'ON Medication',  y: -0.12, xref: 'x', yref: 'paper', text: `n=${onCount}`,  showarrow: false, font: { size: 10, color: '#4A6580' } },
          { x: 'OFF Medication', y: -0.12, xref: 'x', yref: 'paper', text: `n=${offCount}`, showarrow: false, font: { size: 10, color: '#4A6580' } },
        ],
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: 260 }}
      useResizeHandler
    />
  );
}

// ── Main Stats Page ────────────────────────────────────────────────────────────
export default function StatsPage() {
  const [stats,   setStats]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(r => setStats(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="page-content" style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 60 }}>
      <Spinner size={24} /> <span style={{ color: 'var(--text-secondary)' }}>Loading statistics…</span>
    </div>
  );

  if (!stats || stats.total_subjects === 0) return (
    <div className="page-content">
      <div className="page-header"><h1>Population Statistics</h1></div>
      <EmptyState
        icon="📊"
        title="No data yet"
        desc="Upload patient sessions to see population-level statistics"
      />
    </div>
  );

  const totalTriggers = Object.values(stats.trigger_counts || {}).reduce((a, b) => a + b, 0);

  return (
    <div className="page-content fade-in">
      <div className="page-header">
        <h1>Population Statistics</h1>
        <p>Aggregate analytics across all patients and sessions in the database</p>
      </div>

      {/* Summary metrics */}
      <div className="metric-grid" style={{ marginBottom: 24 }}>
        <MetricCard label="Total Subjects"    value={stats.total_subjects} />
        <MetricCard label="Total Sessions"    value={stats.total_sessions} />
        <MetricCard label="Total Episodes"    value={stats.total_episodes} />
        <MetricCard label="Avg FOG Burden"    value={stats.avg_fog_burden_pct?.toFixed(1)} unit="%" />
        <MetricCard label="Avg Episodes/Session" value={stats.avg_episode_count?.toFixed(1)} />
        <MetricCard label="Sessions ON Med"   value={stats.sessions_by_medication?.on ?? 0} />
        <MetricCard label="Sessions OFF Med"  value={stats.sessions_by_medication?.off ?? 0} />
      </div>

      {/* Charts row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div className="chart-container">
          <div className="section-title">FOG Burden Distribution</div>
          <BurdenHistogram data={stats.fog_burden_distribution || []} />
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
            Distribution of FOG burden % across all recorded sessions
          </div>
        </div>

        <div className="chart-container">
          <div className="section-title">Trigger Type Distribution</div>
          {totalTriggers > 0
            ? <TriggerPie counts={stats.trigger_counts} />
            : <EmptyState icon="🏷" title="No trigger data" />
          }
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="chart-container" style={{ marginBottom: 20 }}>
        <div className="section-title">Medication Effect on FOG Burden</div>
        <MedComparisonChart
          onBurden={stats.med_on_avg_burden}
          offBurden={stats.med_off_avg_burden}
          onCount={stats.sessions_by_medication?.on ?? 0}
          offCount={stats.sessions_by_medication?.off ?? 0}
        />
        {stats.med_on_avg_burden != null && stats.med_off_avg_burden != null && (
          <div className="alert alert-info" style={{ marginTop: 14 }}>
            <span>ℹ</span>
            <div style={{ fontSize: 13 }}>
              Across all sessions, patients OFF medication show on average{' '}
              <strong>{(stats.med_off_avg_burden - stats.med_on_avg_burden).toFixed(1)}%</strong>{' '}
              {stats.med_off_avg_burden > stats.med_on_avg_burden ? 'higher' : 'lower'} FOG burden than when ON medication.
            </div>
          </div>
        )}
      </div>

      {/* Trigger counts table */}
      <div className="card">
        <div className="card-title">Trigger Type Summary</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Trigger Type</th>
              <th>Episode Count</th>
              <th>% of Total</th>
              <th>Distribution</th>
            </tr>
          </thead>
          <tbody>
            {[
              { key: 'StartHesitation', label: 'Start Hesitation', color: 'var(--trigger-sh)' },
              { key: 'Turn',            label: 'Turn',             color: 'var(--trigger-turn)' },
              { key: 'Walking',         label: 'Walking',          color: 'var(--trigger-walk)' },
            ].map(t => {
              const count = stats.trigger_counts?.[t.key] ?? 0;
              const pct   = totalTriggers > 0 ? ((count / totalTriggers) * 100).toFixed(1) : '0.0';
              return (
                <tr key={t.key}>
                  <td className="col-text" style={{ color: t.color, fontWeight: 600 }}>{t.label}</td>
                  <td>{count}</td>
                  <td style={{ color: t.color }}>{pct}%</td>
                  <td>
                    <div style={{ width: 200, height: 8, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{
                        width: `${pct}%`, height: '100%',
                        background: t.color, borderRadius: 4,
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
