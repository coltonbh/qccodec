import json
from pathlib import Path

from qcio import Results

# Load trajectory.json answer
traj_path = Path(__file__).parent / "trajectory.json"
traj_json = json.loads(traj_path.read_text())
trajectory: list[Results] = [Results(**item) for item in traj_json]

# Load excited-state-trajectory.json answer
es_traj_path = Path(__file__).parent / "excited-state-trajectory.json"
es_traj_json = json.loads(es_traj_path.read_text())
es_trajectory: list[Results] = [Results(**item) for item in es_traj_json]
