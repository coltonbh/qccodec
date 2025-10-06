"""Simple data models to support parsing of QM program output files."""

from dataclasses import dataclass
from typing import Any

from .exceptions import DataCollectorError


class DataCollector(dict):
    """A dictionary for collecting data from parsers."""

    def add_data(self, target: str | tuple[str, ...], value: Any) -> None:
        """
        Assign a value into the DataCollector at the specified target.

        If target is a string, the value is assigned to that key.
        If target is a tuple, the method navigates through nested dictionaries,
        creating them as needed, and assigns the value at the final key.
        """
        keys = target if isinstance(target, tuple) else (target,)
        d = self
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        if keys[-1] in d:
            raise DataCollectorError(
                f"Target '{keys}' already exists in DataCollector. You cannot add the same target twice."
            )
        d[keys[-1]] = value


@dataclass
class NativeInput:
    """Native input file data for a quantum chemistry program. 
    
    Writing these files to disk should produce a valid input.

    Attributes:
        input_file: input file for the program
        geometry: xyz file or other geometry file required for the calculation
        geometry_filename: filename of the geometry file referenced in the input
    """

    input_file: str
    geometry_file: str | None = None
    geometry_filename: str | None = None

    def __post_init__(self):
        """Ensure that geometry_filename is set if geometry is set."""
        if self.geometry_file and not self.geometry_filename:
            raise ValueError(
                "geometry_filename must be set if geometry_file is provided. "
                "Set geometry_filename to the name of the geometry file as referenced "
                "in the input file."
            )
