"""Parsers for Orca output files."""

import itertools
import re
from enum import Enum
from pathlib import Path
from typing import Generator, Optional, Union

import numpy as np
from qcio import (
    CalcType,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointResults,
    Structure,
)

from qccodec.exceptions import ParserError

from ..registry import register
from .utils import re_finditer, re_search


class OrcaFileType(str, Enum):
    """Orca filetypes.

    Maps file types to their suffixes as written in the Orca output directory
    (except for STDOUT and DIRECTORY).
    """

    STDOUT = "stdout"
    DIRECTORY = "directory"
    HESS = ".hess"  # basename.hess


def iter_files(
    stdout: Optional[str], directory: Optional[Union[Path, str]]
) -> Generator[tuple[OrcaFileType, Union[str, bytes, Path]], None, None]:
    """
    Iterate over the files in a Orca output directory.

    If stdout is provided, yields a tuple for it.

    If directory is provided, iterates over the directory to yield files according to
    program-specific logic.

    Args:
        stdout: The contents of the Orca stdout file.
        directory: The path to the directory containing the Orca output files.

    Yields:
        (FileType, contents) tuples for a program's output.
    """
    if stdout is not None:
        yield OrcaFileType.STDOUT, stdout

    if directory is not None:
        directory = Path(directory)
        # Check if the directory exists and is a directory
        if not directory.exists() or not directory.is_dir():
            raise ParserError(
                f"Directory {directory} does not exist or is not a directory."
            )
        yield OrcaFileType.DIRECTORY, directory

        # Read the basename from STDOUT
        if stdout is not None:
            basename = parse_basename(stdout)

            # Iterate over the files in the directory and yield their contents
            for filetype in OrcaFileType:
                # Ignore STDOUT and DIRECTORY as they are handled above
                if filetype not in (OrcaFileType.STDOUT, OrcaFileType.DIRECTORY):
                    # Get suffix from FileType value
                    file_suffix = filetype.value
                    file_path = directory / f"{basename}{file_suffix}"
                    if file_path.exists():
                        yield filetype, file_path.read_text()


@register(
    filetype=OrcaFileType.STDOUT,
    calctypes=[CalcType.energy, CalcType.gradient, CalcType.hessian],
    target="energy",
)
def parse_energy(contents: str) -> float:
    """Parse the final energy from Orca stdout."""
    regex = r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)"
    return float(re_search(regex, contents).group(1))


@register(
    filetype=OrcaFileType.STDOUT,
    calctypes=[CalcType.gradient, CalcType.hessian],
    target="gradient",
)
def parse_gradient(contents: str) -> list[list[float]]:
    """Parse the gradient from Orca stdout.

    Returns:
        The gradient as a list of 3-element lists.

    Raises:
        MatchNotFoundError: If no gradient data is found.
    """
    gradients = parse_gradients(contents)
    return gradients[-1]


def parse_gradients(contents: str) -> list[list[list[float]]]:
    """Parse all gradients from Orca stdout.

    Returns:
        The gradient as a list of 3-element lists.

    Raises:
        MatchNotFoundError: If no gradient data is found.
    """
    # Extract the gradient block lines
    header_regex = r"CARTESIAN GRADIENT.*?(?=\d)"  # non-greedy lookahead to first digit
    header_matches = re_finditer(header_regex, contents, flags=re.DOTALL)

    gradients = []
    for header_match in header_matches:
        block_start = header_match.end()
        block_lines = itertools.takewhile(
            lambda line: re.search(r"\d\s*$", line), contents[block_start:].splitlines()
        )

        # Parse values from block lines
        line_regex = r".*:\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)"
        line_matches = [re_search(line_regex, line) for line in block_lines]
        gradients.append([list(map(float, match.groups())) for match in line_matches])

    return gradients


@register(
    filetype=OrcaFileType.HESS,
    calctypes=[CalcType.hessian],
    target="hessian",
)
def parse_hessian(contents: str) -> list[list[float]]:
    """Parse the output directory of a Orca optimization calculation into a trajectory.

    Args:
        directory: Path to the directory containing the Orca output files.
        stdout: The contents of the Orca stdout file.
        input_data: The input object used for the calculation.

    Returns:
        A square Hessian matrix as a list of lists of floats.

    Raises:
        MatchNotFoundError: If no Hessian data is found.
        ParserError: If the extracted numbers cannot form a proper square matrix.
    """
    # Find hessian entry in basename.hess file
    entry = next(
        (block for block in contents.split("$") if block.startswith("hess")),
        None,
    )
    if entry is None:
        msg = "Failed to find hessian block in Hessian file."
        raise ParserError(msg)

    dim = int(entry.splitlines()[1])

    # Split the hessian entry into blocks on lines of the form '  0  1  2  3 ...'
    split_result = re.split(r"^\s*(?:\d+\s+)+\d+\s*$", entry, flags=re.MULTILINE)
    if not len(split_result) > 1:
        msg = f"Failed to parse blocks in hessian entry:\n{entry}"
        raise ParserError(msg)

    # Get the text for each block and
    blocks = [block.strip() for block in split_result[1:]]
    hessian: list[list[float]] = [[] for _ in range(dim)]
    for block in blocks:
        lines = block.splitlines()
        if not len(lines) == dim:
            msg = f"Block line count {len(lines)} does not match dimension {dim}:\n{block}"
            raise ParserError(msg)

        for i, line in enumerate(block.splitlines()):
            row = list(map(float, line.split()[1:]))
            hessian[i].extend(row)

    return hessian


@register(
    filetype=OrcaFileType.DIRECTORY,
    calctypes=[CalcType.optimization, CalcType.transition_state],
    target="trajectory",
)
def parse_trajectory(
    directory: Union[Path, str],
    stdout: str,
    input_data: ProgramInput,
) -> list[ProgramOutput]:
    """Parse the output directory of a Orca optimization calculation into a trajectory.

    Args:
        directory: Path to the directory containing the TeraChem output files.
        stdout: The contents of the TeraChem stdout file.
        input_data: The input object used for the calculation.

    Returns:
        A list of ProgramOutput objects.
    """
    basename = parse_basename(stdout)
    directory = Path(directory)
    file = directory / f"{basename}_trj.xyz"
    if not file.exists():
        msg = f"Trajectory file does not exist: {file}"
        raise ParserError(msg)

    # Parse the structures, energies, and gradients
    structures = Structure.open_multi(file)
    energies = [
        float(struct.extras[Structure._xyz_comment_key][-1]) for struct in structures
    ]
    gradients = list(map(np.array, parse_gradients(stdout)))

    # No gradient gets calculated after the last step, so use a fake gradient for the last step
    fake_gradient = np.zeros_like(gradients[0])
    if len(gradients) == len(structures) - 1:
        gradients.append(fake_gradient)

    # Parse program version
    program_version = parse_version(stdout)

    # Create the optimization trajectory
    trajectory: list[ProgramOutput] = [
        ProgramOutput(
            input_data=ProgramInput(
                calctype=CalcType.gradient,
                structure=struct,
                model=input_data.model,
            ),
            success=True,
            results=SinglePointResults(energy=energy, gradient=gradient),
            provenance=Provenance(
                program="orca",
                program_version=program_version,
            ),
        )
        for struct, energy, gradient in zip(structures, energies, gradients)
    ]

    return trajectory


@register(filetype=OrcaFileType.STDOUT, target=("extras", "program_version"))
def parse_version(string: str) -> str:
    """Parse version string from Orca stdout."""
    regex = r"Program Version (\d+\.\d+\.\d+)"
    match = re_search(regex, string)
    return match.group(1)


@register(filetype=OrcaFileType.STDOUT, target="calcinfo_natoms")
def parse_natoms(contents: str) -> int:
    """Parse number of atoms value from Orca stdout.

    Returns:
        The number of atoms as an integer.

    Raises:
        MatchNotFoundError: If the regex does not match.
    """
    regex = r"Number of atoms\s*...\s*(\d+)"
    match = re_search(regex, contents)
    return int(match.group(1))


def parse_basename(string: str) -> str:
    """Parse the file basename from Orca stdout."""
    regex = r"NAME\s+=\s+(.*)"
    match = re_search(regex, string)
    return Path(match.group(1)).stem
