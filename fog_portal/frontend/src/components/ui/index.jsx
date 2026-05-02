// ── Quality Badge ──────────────────────────────────────────────────────────────
export function QualityBadge({ quality }) {
  const map = {
    Good:       { cls: 'badge badge-success', icon: '✓' },
    Acceptable: { cls: 'badge badge-warning', icon: '~' },
    Poor:       { cls: 'badge badge-danger',  icon: '!' },
  };
  const { cls, icon } = map[quality] || map['Acceptable'];
  return <span className={cls}>{icon} {quality}</span>;
}

// ── Medication Badge ───────────────────────────────────────────────────────────
export function MedBadge({ status }) {
  return (
    <span className={`badge ${status === 'on' ? 'med-on' : 'med-off'}`}>
      {status === 'on' ? '💊 ON' : '⊘ OFF'}
    </span>
  );
}

// ── Trigger Badge ──────────────────────────────────────────────────────────────
export function TriggerBadge({ label }) {
  if (!label) return <span className="badge badge-muted">—</span>;
  const map = {
    StartHesitation: { cls: 'trigger-badge trigger-sh',   icon: '⏸', short: 'Hesitation' },
    Turn:            { cls: 'trigger-badge trigger-turn', icon: '↻', short: 'Turn'        },
    Walking:         { cls: 'trigger-badge trigger-walk', icon: '⚡', short: 'Walking'     },
  };
  const { cls, icon, short } = map[label] || { cls: 'badge badge-muted', icon: '?', short: label };
  return <span className={cls}>{icon} {short}</span>;
}

// ── Confidence Bars ────────────────────────────────────────────────────────────
export function ConfBars({ sh, turn, walk }) {
  const bars = [
    { label: 'SH',   value: sh,   color: 'var(--trigger-sh)'   },
    { label: 'Turn', value: turn, color: 'var(--trigger-turn)' },
    { label: 'Walk', value: walk, color: 'var(--trigger-walk)' },
  ];
  return (
    <div className="conf-bars">
      {bars.map(b => (
        <div className="conf-row" key={b.label}>
          <span style={{ width: 28 }}>{b.label}</span>
          <div className="conf-bar-track">
            <div
              className="conf-bar-fill"
              style={{ width: `${(b.value * 100).toFixed(0)}%`, background: b.color }}
            />
          </div>
          <span className="conf-pct">{(b.value * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}

// ── Low Confidence Flag ────────────────────────────────────────────────────────
export function LowConfFlag({ flag }) {
  if (!flag) return null;
  return (
    <span
      title="Low confidence — interpret with caution"
      style={{ color: 'var(--warning)', fontSize: 14 }}
    >
      ⚠
    </span>
  );
}

// ── Spinner ────────────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }) {
  return (
    <div
      className="spinner"
      style={{ width: size, height: size }}
    />
  );
}

// ── Annotation Buttons ─────────────────────────────────────────────────────────
export function AnnotationButtons({ current, onSelect }) {
  const opts = [
    { key: 'confirmed', label: '✓ Confirmed' },
    { key: 'uncertain', label: '? Uncertain' },
    { key: 'artifact',  label: '✕ Artifact'  },
  ];
  return (
    <div className="annotation-group">
      {opts.map(o => (
        <button
          key={o.key}
          className={`ann-btn ${current === o.key ? `active-${o.key}` : ''}`}
          onClick={() => onSelect(o.key)}
          title={`Mark as ${o.key}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

// ── Stat card ──────────────────────────────────────────────────────────────────
export function MetricCard({ label, value, unit, sub, accent }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={accent ? { color: accent } : {}}>
        {value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

// ── Empty state ────────────────────────────────────────────────────────────────
export function EmptyState({ icon = '📭', title, desc, action }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <div className="empty-title">{title}</div>
      {desc && <div className="empty-desc">{desc}</div>}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  );
}
