export type RefreshInterval = 5 | 10 | 30 | "manual";
export type AutomaticRefreshInterval = Exclude<RefreshInterval, "manual">;

export interface RefreshConfiguration {
  supported_intervals: readonly RefreshInterval[];
  default_interval: AutomaticRefreshInterval;
}