import type { SyntheticProvenance } from "../contracts/vitals";

interface ProvenanceBadgeProps {
  sequence: number;
  provenance: SyntheticProvenance;
  prototypeLabel: string;
}

export function ProvenanceBadge({ sequence, provenance, prototypeLabel }: ProvenanceBadgeProps) {
  return (
    <footer className="provenance" aria-label="Observation provenance">
      <span>Sequence: {sequence}</span>
      <span>Source: {provenance.source_name}</span>
      <span>Scenario: {provenance.scenario_id} v{provenance.scenario_version}</span>
      <span>Live bedside feed: {provenance.is_live_bedside_feed ? "yes" : "no"}</span>
      <span>Server label: {prototypeLabel}</span>
    </footer>
  );
}