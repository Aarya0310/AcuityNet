from pydantic import BaseModel


class PatientSummary(BaseModel):
    patient_id: str
    display_name: str
    bed_id: str
    unit: str