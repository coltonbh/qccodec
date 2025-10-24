from pathlib import Path

import pytest
from qcio import CalcType

from qccodec.parsers.orca import (
    parse_energy,
    parse_gradient,
    parse_hessian,
    parse_natoms,
    parse_trajectory,
    parse_version,
)

from .conftest import ParserTestCase, run_test_harness
from .data.orca.answers import gradients, hessians, trajectories

######################################################
##### Top level tests for all registered parsers #####
######################################################


test_cases = [
    ParserTestCase(
        name="Parse version",
        parser=parse_version,
        contents=Path("water.energy.out"),
        contents_stdout=True,
        calctype=CalcType.energy,
        success=True,
        answer="6.1.0",
    ),
    ParserTestCase(
        name="Parse energy from energy log",
        parser=parse_energy,
        contents=Path("water.energy.out"),
        contents_stdout=True,
        calctype=CalcType.energy,
        success=True,
        answer=-76.320421659333,
    ),
    ParserTestCase(
        name="Parse energy from gradient log",
        parser=parse_energy,
        contents=Path("water.grad.out"),
        contents_stdout=True,
        calctype=CalcType.gradient,
        success=True,
        answer=-76.320385565717,
    ),
    ParserTestCase(
        name="Parse energy from hessian log",
        parser=parse_energy,
        contents=Path("water.hess.out"),
        contents_stdout=True,
        calctype=CalcType.hessian,
        success=True,
        answer=-76.320421659333,
    ),
    ParserTestCase(
        name="Parse analytic gradient",
        parser=parse_gradient,
        contents=Path("water.grad.out"),
        contents_stdout=True,
        calctype=CalcType.gradient,
        success=True,
        answer=gradients.water_b3lyp,
    ),
    ParserTestCase(
        name="Parse numerical gradient",
        parser=parse_gradient,
        contents=Path("water.numgrad.out"),
        contents_stdout=True,
        calctype=CalcType.gradient,
        success=True,
        answer=gradients.water_revdsd,
    ),
    ParserTestCase(
        name="Parse analytic hessian",
        parser=parse_hessian,
        contents=Path("water.hess.out"),
        contents_stdout=True,
        calctype=CalcType.hessian,
        success=True,
        answer=hessians.water_b3lyp,
        extra_files=["water.hess.hess"],
    ),
    ParserTestCase(
        name="Parse numerical hessian",
        parser=parse_hessian,
        contents=Path("water.numhess.out"),
        contents_stdout=True,
        calctype=CalcType.hessian,
        success=True,
        answer=hessians.water_revdsd,
        extra_files=["water.numhess.hess"],
    ),
    ParserTestCase(
        name="Parse number of atoms water",
        parser=parse_natoms,
        contents=Path("water.energy.out"),
        contents_stdout=True,
        calctype=CalcType.energy,
        success=True,
        answer=3,
    ),
    ParserTestCase(
        name="Parse trajectory",
        parser=parse_trajectory,
        contents=Path("water.opt.out"),
        contents_stdout=True,
        calctype=CalcType.optimization,
        success=True,
        answer=trajectories.trajectory,
        clear_registry=False,
        extra_files=["water.opt_trj.xyz"],
    ),
]


@pytest.mark.parametrize("test_case", test_cases, ids=lambda tc: tc.name)
def test_orca_parsers(test_data_dir, prog_input_factory, tmp_path, test_case):
    """
    Tests the orca parsers to ensure that they correctly parse the output files and
    behave correctly within the decode function.
    """
    run_test_harness(test_data_dir, prog_input_factory, tmp_path, test_case)
