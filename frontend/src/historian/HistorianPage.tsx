import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { createHistorianAnnotation, getHistorian } from "../api/client";
import type { HistorianFactCategory, HistorianResponse, RuleEvaluation, TimelineEntry } from "../contracts/historian";
import { PrototypeBanner } from "../safety/PrototypeBanner";

const categoryLabels: Record<HistorianFactCategory, string> = {
  diagnosis: "Diagnoses",
  medication: "Medications",
  lab: "Labs",
  icu_event: "Previous ICU events",
};

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }).format(new Date(value));
}

export function HistorianPage({ patientId = "P-1042" }: { patientId?: string }) {
  const queryClient = useQueryClient();
  const historian = useQuery({ queryKey: ["historian", patientId], queryFn: () => getHistorian(patientId), retry: false });
  const [annotationText, setAnnotationText] = useState("");
  const [annotationError, setAnnotationError] = useState<string | null>(null);
  const [rulesOpen, setRulesOpen] = useState(false);

  async function submitAnnotation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = annotationText.trim();
    if (!text) {
      setAnnotationError("Enter a concise annotation before submitting.");
      return;
    }
    setAnnotationError(null);
    await createHistorianAnnotation(patientId, text);
    setAnnotationText("");
    await queryClient.invalidateQueries({ queryKey: ["historian", patientId] });
  }

  if (historian.isLoading) return <main className="historian-shell"><p role="status">Loading historian evidence...</p></main>;
  if (historian.isError || !historian.data) return <main className="historian-shell"><p role="alert">Historian evidence unavailable. REST retry required.</p><button type="button" onClick={() => void historian.refetch()}>Retry historian</button></main>;

  const record = historian.data;
  return (
    <main className="historian-shell">
      <header className="historian-header">
        <div><p className="eyebrow">AcuityNet / Medical Historian</p><h1>{record.patient_name}</h1><p className="patient-id">Patient {record.patient_id} / {record.bed_id} / {record.unit}</p></div>
        <div className="historian-state" role="status"><strong>{record.contextual_status === "complete" ? "Context complete" : "Baseline only"}</strong><span>{record.contextual_status === "complete" ? "All seeded evidence categories are available." : "Contextual risk is unavailable until the missing evidence is restored."}</span></div>
      </header>
      <PrototypeBanner />
      <section className="historian-summary" aria-label="Risk summary">
        <div><span>Baseline score</span><strong>{record.baseline_score.toFixed(2)}</strong></div>
        <div><span>Contextual score</span><strong>{record.contextual_score === null ? "Unavailable" : record.contextual_score.toFixed(2)}</strong></div>
        <div><span>Prediction</span><strong>{record.current_prediction.event}</strong><small>{(record.current_prediction.probability * 100).toFixed(0)}% probability / {record.current_prediction.horizon_minutes} min</small></div>
        <div><span>Risk level</span><strong>{record.current_prediction.level}</strong></div>
      </section>
      {record.contextual_status === "incomplete" ? <section className="historian-incomplete" role="alert"><strong>Contextual risk unavailable</strong><p>Baseline risk is shown without partial rule adjustments.</p><ul>{record.missing_evidence.map((item) => <li key={item}>{item}</li>)}</ul></section> : null}
      <section className="historian-facts" aria-label="Patient context"><h2>Patient context</h2><div className="fact-groups">{(Object.keys(categoryLabels) as HistorianFactCategory[]).map((category) => <FactGroup key={category} category={category} facts={record.facts.filter((fact) => fact.category === category)} />)}</div></section>
      <section className="historian-rules"><details open={rulesOpen} onToggle={(event) => setRulesOpen(event.currentTarget.open)}><summary aria-expanded={rulesOpen} onClick={(event) => { event.preventDefault(); setRulesOpen((open) => !open); }}>Research rules and explanation</summary>{rulesOpen ? <><p className="research-disclaimer">These configurable deltas are research-prototype explanations, not validated clinical weights or medical advice.</p><div className="rule-list">{record.rule_evaluations.map((rule) => <RuleRow key={rule.rule_key} rule={rule} />)}</div></> : null}</details></section>
      <section className="historian-timeline" aria-label="Evidence timeline"><h2>Evidence timeline</h2><ol>{record.timeline.map((entry) => <TimelineRow key={entry.entry_id} entry={entry} />)}</ol></section>
      <section className="historian-annotation"><h2>Doctor annotation</h2><p>Annotations are timestamped evidence and do not change the score or research rules.</p><form onSubmit={(event) => void submitAnnotation(event)}><label htmlFor="historian-annotation-text">Add a concise note</label><textarea id="historian-annotation-text" value={annotationText} maxLength={500} onChange={(event) => setAnnotationText(event.target.value)} /><button type="submit" disabled={!annotationText.trim()}>Add annotation</button>{annotationError ? <p role="alert">{annotationError}</p> : null}</form></section>
      <footer className="provenance" aria-label="Historian provenance"><span>Provenance: {record.provenance}</span><span>Source: {record.current_prediction.source_kind} / {record.current_prediction.source_version}</span><span>{record.prototype_label}</span></footer>
    </main>
  );
}

function FactGroup({ category, facts }: { category: HistorianFactCategory; facts: HistorianResponse["facts"] }) {
  return <div className="fact-group"><h3>{categoryLabels[category]}</h3>{facts.length ? <ul>{facts.map((fact) => <li key={fact.fact_id}><strong>{fact.label}</strong>{fact.value ? `: ${fact.value}${fact.unit ? ` ${fact.unit}` : ""}` : ""}<small>{formatTimestamp(fact.effective_at)} / {fact.source_name}</small></li>)}</ul> : <p>Evidence unavailable</p>}</div>;
}
function RuleRow({ rule }: { rule: RuleEvaluation }) { return <article className="rule-row"><strong>{rule.rule_name}</strong><span>{rule.rule_key} / {rule.rule_version}</span><b>{rule.delta >= 0 ? "+" : ""}{rule.delta.toFixed(2)}</b><p>{rule.explanation}</p></article>; }
function TimelineRow({ entry }: { entry: TimelineEntry }) { return <li className={`timeline-entry timeline-${entry.entry_type}`}><time dateTime={entry.occurred_at}>{formatTimestamp(entry.occurred_at)}</time><div><strong>{entry.title}</strong><p>{entry.detail}</p></div></li>; }
