import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listSubjects } from '../utils/api';
import { Spinner, EmptyState } from '../components/ui';

export default function SubjectsPage() {
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [search,   setSearch]   = useState('');

  useEffect(() => {
    listSubjects()
      .then(r => setSubjects(r.data))
      .finally(() => setLoading(false));
  }, []);

  const filtered = subjects.filter(s =>
    s.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-content fade-in">
      <div className="page-header-row page-header">
        <div>
          <h1>Patients</h1>
          <p>{subjects.length} subject{subjects.length !== 1 ? 's' : ''} in database</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div className="search-wrap">
            <span className="search-icon">🔍</span>
            <input
              className="search-input"
              placeholder="Search subject ID…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/upload')}>
            ⬆ New Upload
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 40 }}>
          <Spinner /> <span style={{ color: 'var(--text-secondary)' }}>Loading patients…</span>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="👤"
          title={search ? 'No matching patients' : 'No patients yet'}
          desc={search ? 'Try a different search term' : 'Upload a CSV file to add the first patient'}
          action={!search && (
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>
              ⬆ Upload First Recording
            </button>
          )}
        />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject ID</th>
                <th>Age</th>
                <th>Sex</th>
                <th>Total Visits</th>
                <th>Latest Visit</th>
                <th>Latest FOG Burden</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/subjects/${s.id}`)}>
                  <td style={{ fontFamily: 'var(--font-data)', color: 'var(--accent-light)', fontWeight: 600 }}>
                    {s.id}
                  </td>
                  <td>{s.age ?? '—'}</td>
                  <td>{s.sex ?? '—'}</td>
                  <td>
                    <span className="badge badge-accent">{s.total_visits} visit{s.total_visits !== 1 ? 's' : ''}</span>
                  </td>
                  <td className="col-text" style={{ color: 'var(--text-secondary)' }}>
                    {s.latest_visit_date
                      ? new Date(s.latest_visit_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
                      : '—'
                    }
                  </td>
                  <td>
                    {s.latest_fog_burden != null ? (
                      <span style={{
                        fontFamily: 'var(--font-data)',
                        color: s.latest_fog_burden > 30 ? 'var(--danger)'
                             : s.latest_fog_burden > 15 ? 'var(--warning)'
                             : 'var(--success)',
                        fontWeight: 600,
                      }}>
                        {s.latest_fog_burden.toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => navigate(`/subjects/${s.id}`)}
                    >
                      View →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
