import json
from pathlib import Path

from qcdata import ProgramOutput

# Load trajectory.json answer
traj_path = Path(__file__).parent / "trajectory.json"
traj_json = json.loads(traj_path.read_text())
trajectory: list[ProgramOutput] = [ProgramOutput(**item) for item in traj_json]

# Load ch3_trajectory.json answer (open-shell, multiplicity=2)
ch3_traj_path = Path(__file__).parent / "ch3_trajectory.json"
ch3_traj_json = json.loads(ch3_traj_path.read_text())
trajectory_ch3: list[ProgramOutput] = [ProgramOutput(**item) for item in ch3_traj_json]
