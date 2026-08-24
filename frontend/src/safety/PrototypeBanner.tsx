export const PROTOTYPE_LABEL = "Simulated ICU environment - research prototype - not for clinical use";

export function PrototypeBanner() {
  return <div className="prototype-banner" role="note">{PROTOTYPE_LABEL}</div>;
}