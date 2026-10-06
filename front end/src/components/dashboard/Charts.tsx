import { useId } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, BarChart3, TrendingUp } from "lucide-react";
import type { AnalyticsData } from "@/types/trustgraph";

export function DistributionChart({ data }: { data: AnalyticsData["distribution"] }) {
  const max = Math.max(...data.map(item => item.count), 1);
  return <div className="chart-box" data-testid="risk-distribution-chart">
    <div className="chart-legend">{data.map(item => <span key={item.label}><i style={{ background: item.color }} />{item.label}<strong>{item.count}</strong></span>)}</div>
    <div className="distribution-bars">{data.map(item => <div className="distribution-bar-group" key={item.label}>
      <div className={`distribution-bar ${item.count === 0 ? "distribution-bar-empty" : ""}`} style={{ height: `${item.count / max * 100}%`, background: item.color }} aria-label={`${item.label}: ${item.count}`}><span>{item.count}</span></div><small>{item.label}</small>
    </div>)}</div>
  </div>;
}

export function TimelineChart({ points, compact = false }: { points: AnalyticsData["timeseries"]; compact?: boolean }) {
  const gradient = useId().replaceAll(":", "");
  const max = Math.max(...points.map(item => item.total), 1);
  const width = 600, height = compact ? 120 : 190, padding = 8;
  const position = (index: number) => points.length === 1 ? width / 2 : padding + index / Math.max(points.length - 1, 1) * (width - padding * 2);
  const y = (value: number) => height - padding - value / max * (height - padding * 2);
  const line = points.map((point, index) => `${position(index)},${y(point.total)}`).join(" ");
  return <div className={`chart-box timeline-box ${compact ? "timeline-compact" : ""}`} data-testid="detections-over-time-chart">
    <div className="chart-legend"><span><i className="legend-line" />Cumulative detections</span><span className="chart-metric"><TrendingUp size={13} />{points.at(-1)?.total ?? 0} latest</span></div>
    <svg className="timeline-plot" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label={`Cumulative detections over time, ${points.at(-1)?.total ?? 0} in the selected period`}>
      <defs><linearGradient id={gradient} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2F66F0" stopOpacity=".34" /><stop offset="100%" stopColor="#2F66F0" stopOpacity="0" /></linearGradient></defs>
      {points.length > 1 && <><polygon points={`${position(0)},${height} ${line} ${position(points.length - 1)},${height}`} fill={`url(#${gradient})`} /><polyline points={line} fill="none" stroke="#7FA8FF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></>}
      {points.map((point, index) => <circle key={point.label} cx={position(index)} cy={y(point.total)} r="4" fill="#060B1A" stroke="#7FA8FF" strokeWidth="2" />)}
    </svg>
    <div className="chart-axis">{points.map(point => <span key={point.label}>{point.label}</span>)}</div>
  </div>;
}

export function ChartHeading({ eyebrow, title, link, to = "/app/analytics" }: { eyebrow: string; title: string; link?: string; to?: string }) {
  return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h2 data-testid={`section-title-${title.toLowerCase().replaceAll(" ", "-")}`}>{title}</h2></div>{link && <Link to={to} className="section-link"><ArrowUpRight size={14} />{link}</Link>}</div>;
}

const channelNames = { whatsapp: "WhatsApp", gmail: "Gmail", messenger: "Messenger", instagram: "Instagram", linkedin: "LinkedIn", telegram: "Telegram", discord: "Discord", slack: "Slack", generic: "Other sites", test: "Test page", other: "Other" };
export function ChannelBars({ data }: { data: AnalyticsData["channels"] }) {
  const max = Math.max(...data.map(item => item.count), 1);
  return <div className="channel-bars" data-testid="channel-breakdown-chart">{data.map(item => <div className="channel-row" key={item.channel}><span>{channelNames[item.channel]}</span><div><i style={{ width: `${item.count / max * 100}%` }} /></div><strong>{item.count}</strong></div>)}</div>;
}
export function ChartIcon() { return <BarChart3 size={17} />; }
