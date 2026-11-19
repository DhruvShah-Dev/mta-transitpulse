import React, { useState } from "react";
import { chartConfigEntries, DataComponent, DataTable, EvidenceChart, MetricCard, useDataApp, useDashboardTabs } from "../../data-app-public.jsx";

const tabs = [
  { id: "overview", label: "Overview" }, { id: "lines", label: "Line performance" },
  { id: "diagnostics", label: "Diagnostics" }, { id: "priorities", label: "Priorities" },
];
const pct = (value) => `${Number(value).toFixed(2)}%`;
const mins = (value) => `${Number(value).toFixed(1)}M`;
function Route({ line }) {
  const group = /^[1234567]$/.test(line) ? "number" : ["B", "D", "F", "M"].includes(line) ? "orange" : ["N", "Q", "R", "W", "NW"].includes(line) ? "yellow" : ["A", "C", "E"].includes(line) ? "blue" : "neutral";
  return <span className={`tp-route tp-route--${group}`}>{line}</span>;
}
function Panel({ id, queryId, title, rows, spec, height = 290, note }) {
  const chart = spec.yDomain ? chartConfigEntries({ id, title, rows, spec })[0] : { id, title, rows, spec };
  return <div className="tp-panel"><EvidenceChart {...chart} queryId={queryId} sourceRows={rows} height={height} variant="plain" />{note && <p className="tp-note">{note}</p>}</div>;
}

export function DashboardContent() {
  const { activeTabId } = useDashboardTabs(tabs);
  const { reviewedRows } = useDataApp();
  const annual = reviewedRows("annual_system", ["year"]);
  const priority = reviewedRows("priority_2025", ["line"]);
  const history = reviewedRows("line_history", ["year", "line"]);
  const categories = reviewedRows("delay_categories_2025", ["category"]);
  const [line, setLine] = useState("F");
  const old = annual.find((row) => row.year === "2022");
  const latest = annual.find((row) => row.year === "2025");
  const ranked = [...priority].sort((a, b) => a.rank - b.rank);
  const weak = [...priority].sort((a, b) => a.cjtPercent - b.cjtPercent);
  const service = [...priority].sort((a, b) => a.servicePercent - b.servicePercent);
  const selected = priority.find((row) => row.line === line) || ranked[0];
  const selectedHistory = history.filter((row) => row.line === line);
  const lineValues = selectedHistory.map((row) => row.cjtPercent);
  const lineDomain = lineValues.length
    ? [Math.floor(Math.min(...lineValues) - 1), Math.ceil(Math.max(...lineValues) + 1)]
    : [0, 100];
  const [lineChart] = chartConfigEntries({
    id: "lines-history", title: `${line} journey reliability, 2022–2025`, rows: selectedHistory,
    spec: { type: "line", x: "year", y: "cjtPercent", xScale: "category",
      yDomain: lineDomain,
      yLabel: "Journey reliability (%)", showXAxisLabel: false, colors: { cjtPercent: "#005da9" } },
  });
  const tab = activeTabId || "overview";
  const titles = {
    overview: "Reliability improved. Passenger-time burden remains large.",
    lines: "Some lines still deliver a weaker journey.",
    diagnostics: "Use operating signals to focus the next review.",
    priorities: "Investigate F, B, and Q first.",
  };
  return <article className="tp-dashboard">
    <header className="tp-intro"><div className="tp-intro__top"><span>Independent analysis</span><span>Jan 2022–Dec 2025 · MTA Open Data</span></div><h1>{titles[tab]}</h1></header>

    {tab === "overview" && <>
      <section className="tp-metrics" aria-label="Key findings">
        <MetricCard id="overview-cjt" queryId="annual_system" title="2025 journey reliability" value={pct(latest?.cjtPercent)} sourceRows={annual} description="Weekday customer journey time performance, 6 a.m.–11 p.m." />
        <MetricCard id="overview-change" queryId="annual_system" title="Change since 2022" value={`+${(latest?.cjtPercent - old?.cjtPercent).toFixed(2)} pp`} sourceRows={annual} description="Percentage points; like-for-like excluding the 42nd Street Shuttle is +1.43 pp." />
        <MetricCard id="overview-burden" queryId="annual_system" title="2025 net additional time" value={`${(latest?.netMinutes / 1e9).toFixed(2)}B min`} sourceRows={annual} description="Signed estimate across measured weekday unlinked trips." />
      </section>
      <div className="tp-grid">
        <Panel id="overview-trend" queryId="annual_system" title="Journey reliability rose from 83.88% to 85.40%" rows={annual} spec={{ type: "line", x: "year", y: "cjtPercent", xScale: "category", yDomain: [82, 87], yLabel: "Journey reliability (%)", showXAxisLabel: false, colors: { cjtPercent: "#005da9" } }} note="Passenger-weighted annual rate. The 42nd Street Shuttle has incomplete 2022 coverage." />
        <Panel id="overview-priority" queryId="priority_2025" title="Proposed investigation order" rows={ranked.slice(0, 6)} spec={{ type: "horizontalBar", x: "line", y: "score", yLabel: "Priority score", showXAxisLabel: false, colors: { score: "#005da9" } }} note="F, B, Q rank 1–3. D warrants a separate reliability review. The score does not predict intervention impact." />
      </div>
      <div className="tp-callout"><Route line="F" /><Route line="B" /><Route line="Q" /><span>High burden and poor reliability</span><Route line="D" /><span>Separate reliability review</span></div>
    </>}

    {tab === "lines" && <>
      <div className="tp-grid">
        <Panel id="lines-lowest" queryId="priority_2025" title="Lowest 2025 journey reliability" rows={weak.slice(0, 10)} height={350} spec={{ type: "horizontalBar", x: "line", y: "cjtPercent", yLabel: "Journey reliability (%)", showXAxisLabel: false, colors: { cjtPercent: "#005da9" } }} note="B is lowest at 78.74%; D is second lowest at 79.63%." />
        <div className="tp-panel"><div className="tp-panel__heading"><h2>Line history</h2><label>Line <select value={line} onChange={(event) => setLine(event.target.value)}>{[...priority].sort((a, b) => a.line.localeCompare(b.line)).map((row) => <option key={row.line} value={row.line}>{row.line}</option>)}</select></label></div>
          <div className="tp-line-stat"><Route line={selected?.line} /><strong>{pct(selected?.cjtPercent)}</strong><span>2025 reliability</span></div>
          <EvidenceChart {...lineChart} queryId="line_history" sourceRows={selectedHistory} height={220} variant="plain" />
          <p className="tp-note">{mins(selected?.netMinutesM)} net additional passenger minutes in 2025 · {selected?.incidentMonths}/12 incident months observed.</p>
        </div>
      </div><p className="tp-note">The scorecard uses 23 comparison groups. N and W are combined as NW for source comparability.</p>
    </>}

    {tab === "diagnostics" && <>
      <div className="tp-grid">
        <Panel id="diag-categories" queryId="delay_categories_2025" title="2025 weekday delay incidents by category" rows={categories} height={330} spec={{ type: "horizontalBar", x: "category", y: "incidents", yLabel: "Incidents", showXAxisLabel: false, colors: { incidents: "#005da9" } }} note="Counts show reported workload, not exposure-adjusted risk." />
        <Panel id="diag-service" queryId="priority_2025" title="Lowest 2025 peak service delivered" rows={service.slice(0, 10)} height={330} spec={{ type: "horizontalBar", x: "line", y: "servicePercent", yLabel: "Scheduled trains delivered (%)", showXAxisLabel: false, colors: { servicePercent: "#005da9" } }} note="Selected weekday peak timepoints only. Source ratios can exceed 100%." />
      </div>
      <div className="tp-callout"><Route line="F" /><strong>{priority.find((row) => row.line === "F")?.delayIncidents.toLocaleString("en-US")}</strong><span>weekday delay incidents</span><strong>{pct(priority.find((row) => row.line === "F")?.servicePercent)}</strong><span>peak service delivered</span></div>
      <p className="tp-note">Customer journeys, incidents, and peak service cover different hours. Co-movement is a lead for investigation, not causality.</p>
    </>}

    {tab === "priorities" && <>
      <section className="tp-metrics" aria-label="Priority lines">{ranked.slice(0, 3).map((row) => <MetricCard key={row.line} id={`priority-${row.line}`} queryId="priority_2025" title={`#${row.rank} · ${row.line} line`} value={mins(row.netMinutesM)} sourceRows={[row]} description={`${pct(row.cjtPercent)} reliability · rank ${row.rankBest}–${row.rankWorst} across five weight scenarios`} />)}</section>
      <div className="tp-grid">
        <Panel id="priority-matrix" queryId="priority_2025" title="Reliability vs net passenger-time burden" rows={priority} height={350} spec={{ type: "scatter", x: "cjtPercent", y: "netMinutesM", series: "quadrant", xLabel: "Journey reliability (%)", yLabel: "Net minutes (millions)" }} note="The high-burden, poor-reliability lines sit toward the upper left. Medians: 161.36M minutes and 84.95% reliability." />
        <div className="tp-panel tp-priority-list"><h2>What to review next</h2>{[["F", "Highest net burden; inspect poor months and peak delivery."], ["B", "Lowest reliability; test whether recent improvement continued."], ["Q", "High burden; locate platform and train-time drivers."], ["D", "Second-lowest reliability; targeted review despite lower burden."]].map(([route, detail]) => <div className="tp-priority-item" key={route}><Route line={route} /><span>{detail}</span></div>)}<p className="tp-note">Proposed weights: 40% reliability · 40% passenger burden · 20% peak service.</p></div>
      </div>
      <DataComponent id="priority-table" queryId="priority_2025" title="2025 comparison groups" kind="table" variant="card" displayRows={ranked} sourceRows={ranked}>
        <DataTable rows={ranked} columns={[{ field: "line", label: "Line" }, { field: "rank", label: "Rank" }, { field: "cjtPercent", label: "CJTP %" }, { field: "netMinutesM", label: "Net minutes, M" }, { field: "servicePercent", label: "Peak service %" }]} />
      </DataComponent>
    </>}
    <footer className="tp-footer">Historical snapshot retrieved 19 Nov 2026 · Independent analysis, not an official MTA recommendation</footer>
  </article>;
}
