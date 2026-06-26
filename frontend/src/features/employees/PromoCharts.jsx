/* Biểu đồ lộ trình (line) + radar tiêu chí — recharts. Owner: Tân. */
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';

export function SalaryJourneyChart({ promotions }) {
  const data = (promotions || []).map((p) => ({
    date: p.date, wage: p.toWage || 0, label: p.toJob }));
  if (!data.length) return <div className="muted" style={{ fontSize: 12 }}>Chưa có dữ liệu lộ trình.</div>;
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="date" fontSize={11} />
        <YAxis fontSize={11} />
        <Tooltip />
        <Line type="monotone" dataKey="wage" stroke="var(--red-600, #a01b1b)" strokeWidth={2} dot />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CriteriaRadar({ lines }) {
  const data = (lines || []).map((l) => ({
    crit: l.name, current: l.score, target: l.maxScore }));
  if (!data.length) return <div className="muted" style={{ fontSize: 12 }}>Chưa có đợt đánh giá.</div>;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="crit" fontSize={10} />
        <PolarRadiusAxis fontSize={9} />
        <Radar name="Mục tiêu" dataKey="target" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.1} />
        <Radar name="Hiện tại" dataKey="current" stroke="var(--red-600, #a01b1b)" fill="var(--red-600, #a01b1b)" fillOpacity={0.35} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
