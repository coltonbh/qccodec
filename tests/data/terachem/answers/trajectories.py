import json
from pathlib import Path

from qcio import CalcType, ProgramInput, Results

# Load trajectory.json answer
traj_path = Path(__file__).parent / "trajectory.json"
traj_json = json.loads(traj_path.read_text())
trajectory: list[Results] = [Results(**item) for item in traj_json]

# Load excited-state-trajectory.json answer
es_traj_path = Path(__file__).parent / "excited-state-trajectory.json"
es_traj_json = json.loads(es_traj_path.read_text())
es_trajectory: list[Results] = [Results(**item) for item in es_traj_json]

# Load ch3-trajectory.json answer
ch3_traj_path = Path(__file__).parent / "ch3-trajectory.json"
ch3_traj_json = json.loads(ch3_traj_path.read_text())
ch3_trajectory: list[Results] = [Results(**item) for item in ch3_traj_json]


def _build_optimization_spec(
    results: list[Results], charge: int = 0, multiplicity: int = 1
) -> ProgramInput:
    """
    Construct an optimization ProgramInput that matches the provided trajectory answers.

    Returns a fresh ProgramInput so tests can mutate copies without touching the stored data.
    """
    first_entry = results[0]
    spec_dict = first_entry.input_data.model_dump()
    spec_dict["calctype"] = CalcType.optimization
    return ProgramInput(**spec_dict)


trajectory_spec: ProgramInput = _build_optimization_spec(trajectory)
es_trajectory_spec: ProgramInput = _build_optimization_spec(es_trajectory)
ch3_trajectory_spec: ProgramInput = _build_optimization_spec(ch3_trajectory, charge=1)
