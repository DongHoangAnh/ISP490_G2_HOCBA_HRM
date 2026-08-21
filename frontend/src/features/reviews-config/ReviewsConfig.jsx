/* Màn Cấu hình đánh giá — 3 tab: Giảng viên / Nhân viên văn phòng / Hướng dẫn.
   Chỉ HR Manager + Admin (Shell: need 'hrm').
   Owner: Việt.
   Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md */
import { useEffect, useState } from 'react';
import {
  fetchReviewConfig, saveReviewCriteria, saveReviewGrading,
} from '../../api/reviews';
import { LoadingState, ErrorState } from '../../components/states';
import Icon from '../../components/Icon';
import CriteriaTab from './CriteriaTab';
import ConfigGuide from './ConfigGuide';

const TABS = [
  { id: 'teacher', label: 'Giảng viên', icon: 'graduation' },
  { id: 'office', label: 'Nhân viên văn phòng', icon: 'users' },
  { id: 'guide', label: 'Hướng dẫn cấu hình', icon: 'book' },
];

const gradingOf = (d) => ({
  gradeA: d.grades.a, gradeB: d.grades.b, gradeC: d.grades.c,
  sessionsTarget: d.params.sessionsTarget,
});

const sumWeight = (rows) => Math.round(
  rows.filter((r) => r.active).reduce((s, r) => s + (Number(r.weight) || 0), 0) * 100) / 100;

export default function ReviewsConfig() {
  const [tab, setTab] = useState(
    () => localStorage.getItem('reviews_config_tab') || 'teacher');
  const [data, setData] = useState(null);
  const [draft, setDraft] = useState({ teacher: [], office: [] });
  const [grading, setGrading] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = () => {
    setLoading(true);
    fetchReviewConfig()
      .then((res) => {
        setData(res);
        setDraft({
          teacher: res.groups.teacher.map((r) => ({ ...r })),
          office: res.groups.office.map((r) => ({ ...r })),
        });
        setGrading(gradingOf(res));
        setErr(null);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);
  useEffect(() => localStorage.setItem('reviews_config_tab', tab), [tab]);

  if (loading && !data) return <LoadingState label="Đang tải cấu hình đánh giá…" />;
  if (err && !data) return <ErrorState message={err} onRetry={load} />;

  const isGuide = tab === 'guide';
  const rows = isGuide ? [] : draft[tab];
  const total = isGuide ? 0 : sumWeight(rows);
  const balanced = Math.abs(total - 100) < 0.01;

  const apply = (res, note) => {
    setData(res);
    setDraft({
      teacher: res.groups.teacher.map((r) => ({ ...r })),
      office: res.groups.office.map((r) => ({ ...r })),
    });
    setGrading(gradingOf(res));
    setMsg({ kind: 'ok', text: note });
  };

  const saveCriteria = () => {
    setSaving(true);
    setMsg(null);
    saveReviewCriteria(tab, rows)
      .then((res) => apply(res, 'Đã lưu bộ câu hỏi đánh giá.'))
      .catch((e) => setMsg({ kind: 'err', text: e.message }))
      .finally(() => setSaving(false));
  };

  const saveGrading = () => {
    setSaving(true);
    setMsg(null);
    saveReviewGrading(grading)
      .then((res) => apply(res, 'Đã lưu ngưỡng xếp loại & tham số.'))
      .catch((e) => setMsg({ kind: 'err', text: e.message }))
      .finally(() => setSaving(false));
  };

  return (
    <div className="content fade-in" style={{ paddingBottom: 88 }}>
      <div className="page-head" style={{ marginBottom: 18 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--ink)' }}>
            Cấu hình đánh giá
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 14 }}>
            Bộ câu hỏi, trọng số, thang điểm và ngưỡng xếp loại của đánh giá định kỳ
          </p>
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: 20 }}>
        {TABS.map((t) => (
          <button key={t.id} className={'tab' + (tab === t.id ? ' active' : '')}
            onClick={() => setTab(t.id)}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name={t.icon} size={16} />
            {t.label}
            {t.id !== 'guide' && Math.abs(sumWeight(draft[t.id]) - 100) >= 0.01 && (
              <span title="Tổng trọng số chưa bằng 100"
                style={{ color: 'var(--red-600)', fontWeight: 800 }}>•</span>
            )}
          </button>
        ))}
      </div>

      {msg && (
        <div className="card" style={{
          padding: '10px 14px', marginBottom: 16, fontSize: 13.5,
          borderLeft: '3px solid ' + (msg.kind === 'ok' ? 'var(--green)' : 'var(--red-600)'),
        }}>
          {msg.text}
        </div>
      )}

      {isGuide ? (
        <ConfigGuide data={data} grading={grading} setGrading={setGrading}
          onSaveGrading={saveGrading} saving={saving}
          groupRows={draft.teacher} />
      ) : (
        <CriteriaTab rows={rows}
          setRows={(next) => setDraft({ ...draft, [tab]: next })}
          autoSources={data.autoSources}
          maxScoreMin={data.maxScoreMin} maxScoreMax={data.maxScoreMax} />
      )}

      {!isGuide && (
        <div style={{
          position: 'sticky', bottom: 0, marginTop: 18, padding: '12px 16px',
          background: '#fff', borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <Icon name={balanced ? 'checkCircle' : 'alertTriangle'} size={18} />
          <div style={{ fontSize: 13.5, fontWeight: 600,
            color: balanced ? 'var(--green)' : 'var(--red-600)' }}>
            Tổng trọng số: {total} / 100
            {!balanced && (
              <span style={{ fontWeight: 500 }}>
                {' '}— {total > 100 ? `thừa ${Math.round((total - 100) * 100) / 100}`
                  : `còn thiếu ${Math.round((100 - total) * 100) / 100}`}
              </span>
            )}
          </div>
          <div style={{ flex: 1 }} />
          <button className="btn btn-ghost" onClick={load} disabled={saving}>
            <Icon name="rotateCcw" size={15} className="mr-s" /> Huỷ thay đổi
          </button>
          <button className="btn btn-primary" onClick={saveCriteria}
            disabled={saving || !balanced}
            title={balanced ? '' : 'Tổng trọng số phải bằng 100 mới lưu được'}>
            <Icon name="checkCircle" size={16} className="mr-s" />
            {saving ? 'Đang lưu…' : 'Lưu bộ câu hỏi'}
          </button>
        </div>
      )}
    </div>
  );
}
