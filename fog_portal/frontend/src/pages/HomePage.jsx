import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '60px 40px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Hero Section */}
      <div style={{ marginBottom: 60, textAlign: 'center' }}>
        <h1 style={{
          fontSize: 48,
          fontWeight: 700,
          color: 'var(--text-primary)',
          marginBottom: 16,
          lineHeight: 1.2,
        }}>
          FOG Detection & Analysis Portal
        </h1>
        <p style={{
          fontSize: 18,
          color: 'var(--text-secondary)',
          marginBottom: 32,
          maxWidth: 700,
          margin: '0 auto 32px',
        }}>
          Clinical decision support for Freezing of Gait analysis in Parkinson's disease patients
        </p>
        <button
          onClick={() => navigate('/upload')}
          style={{
            padding: '14px 32px',
            fontSize: 15,
            fontWeight: 600,
            background: 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => e.target.style.background = 'var(--accent-light)'}
          onMouseLeave={(e) => e.target.style.background = 'var(--accent)'}
        >
          Analyze Recording
        </button>
      </div>

      {/* Info Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 24,
        marginBottom: 60,
      }}>
        {/* What is FOG */}
        <div className="card">
          <div style={{
            fontSize: 24,
            marginBottom: 12,
          }}>
            ❄️
          </div>
          <div className="card-title">What is FOG?</div>
          <p style={{
            fontSize: 14,
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
          }}>
            Freezing of Gait (FOG) is a sudden, brief, involuntary inability to move, despite the intention to walk. It's a common symptom in Parkinson's disease, severely impacting quality of life and increasing fall risk.
          </p>
        </div>

        {/* Why It Matters */}
        <div className="card">
          <div style={{
            fontSize: 24,
            marginBottom: 12,
          }}>
            📊
          </div>
          <div className="card-title">Clinical Significance</div>
          <p style={{
            fontSize: 14,
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
          }}>
            Early detection and characterization of FOG patterns enables clinicians to personalize interventions. Understanding trigger types—start hesitation, turning, or walking—guides targeted rehabilitation strategies.
          </p>
        </div>

        {/* How It Works */}
        <div className="card">
          <div style={{
            fontSize: 24,
            marginBottom: 12,
          }}>
            🧠
          </div>
          <div className="card-title">How This Portal Works</div>
          <p style={{
            fontSize: 14,
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
          }}>
            Upload accelerometer data from patient recordings. Our AI models detect FOG episodes, classify their triggers, and compute clinical metrics. Results are presented with progression tracking and medication effect analysis.
          </p>
        </div>
      </div>

      {/* Workflow Section */}
      <div className="card" style={{ marginBottom: 40 }}>
        <div className="card-title">Analysis Workflow</div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 20,
        }}>
          {[
            { num: 1, title: 'Upload CSV', desc: 'Accelerometer data' },
            { num: 2, title: 'Select Status', desc: 'ON/OFF medication' },
            { num: 3, title: 'AI Analysis', desc: 'Detection & triggers' },
            { num: 4, title: 'View Results', desc: 'Progress & metrics' },
          ].map((step) => (
            <div key={step.num} style={{
              textAlign: 'center',
              padding: '20px',
              background: 'var(--bg-elevated)',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
            }}>
              <div style={{
                width: 40,
                height: 40,
                margin: '0 auto 12px',
                background: 'var(--accent)',
                color: '#fff',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                fontWeight: 700,
              }}>
                {step.num}
              </div>
              <div style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 4,
              }}>
                {step.title}
              </div>
              <div style={{
                fontSize: 12,
                color: 'var(--text-secondary)',
              }}>
                {step.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trigger Types */}
      <div className="card">
        <div className="card-title">FOG Trigger Types</div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 20,
        }}>
          {[
            {
              label: 'Start Hesitation',
              desc: 'Difficulty initiating walking from standing',
              color: 'var(--trigger-sh)',
            },
            {
              label: 'Turn',
              desc: 'FOG during turning maneuvers',
              color: 'var(--trigger-turn)',
            },
            {
              label: 'Walking',
              desc: 'Freezing during continuous walking',
              color: 'var(--trigger-walk)',
            },
          ].map((trigger) => (
            <div key={trigger.label} style={{
              padding: '16px',
              borderLeft: `4px solid ${trigger.color}`,
              background: 'var(--bg-elevated)',
              borderRadius: 'var(--radius)',
            }}>
              <div style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 8,
              }}>
                {trigger.label}
              </div>
              <div style={{
                fontSize: 13,
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
              }}>
                {trigger.desc}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
