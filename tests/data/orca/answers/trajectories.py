import json
from pathlib import Path

from qcio import ProgramOutput

# Load trajectory.json answer
traj_path = Path(__file__).parent / "trajectory.json"
traj_json = json.loads(traj_path.read_text())
trajectory: list[ProgramOutput] = [ProgramOutput(**item) for item in traj_json]
