from backend.app.prediction.fallback import deterministic_prediction


class PredictionAdapter:
    def __init__(self, provider=None):
        self.provider = provider

    def predict(self, latest_observation, vitals, effective_settings=None):
        threshold = float((effective_settings or {}).get("critical_risk_threshold", 0.7))
        if self.provider is not None:
            try:
                result = self.provider.predict(latest_observation, effective_settings or {})
                return result
            except Exception:
                pass
        return deterministic_prediction(latest_observation, vitals, threshold)