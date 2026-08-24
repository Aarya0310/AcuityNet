from dataclasses import dataclass


P1042_VALUES = (
    (98, 82, 16, 122, 78, 36.8),
    (97, 88, 18, 118, 76, 36.9),
    (95, 96, 22, 112, 72, 37.1),
    (92, 108, 27, 104, 68, 37.4),
    (88, 122, 32, 96, 62, 37.8),
)


@dataclass
class P1042Scenario:
    seed: str = "p1042-demo"
    scenario_id: str = "p1042-deterioration-v1"
    scenario_version: str = "1"

    def __post_init__(self) -> None:
        if self.seed != "p1042-demo":
            raise ValueError("Unsupported scenario seed")

    def values_for(self, tick: int) -> tuple[int, int, int, int, int, float]:
        if tick < 0 or tick >= len(P1042_VALUES):
            raise ValueError("Scenario tick must be between 0 and 4")
        return P1042_VALUES[tick]

    def reset(self) -> int:
        return 0