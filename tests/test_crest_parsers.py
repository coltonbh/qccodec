from pathlib import Path

import pytest
from qcio import CalcType, ProgramInput

from qccodec.parsers.crest import (
    parse_conformers,
    parse_energy,
    parse_energy_numhess,
    parse_g98_freqs,
    parse_g98_normal_modes,
    parse_gradient,
    parse_numhess1,
    parse_rotamers,
    parse_trajectory,
    parse_version,
)

from .conftest import ParserTestCase, run_test_harness
from .data.crest.answers import (
    conformers,
    frequencies,
    gradients,
    hessians,
    normal_modes,
    optimizations,
)

######################################################
##### Top level tests for all registered parsers #####
######################################################


test_cases = [
    ParserTestCase(
        name="Parse version",
        parser=parse_version,
        contents=Path("crest_stdout.txt"),
        contents_stdout=True,
        calctype=CalcType.energy,
        success=True,
        answer="3.0.1",
    ),
    ParserTestCase(
        name="Parse version MatchNotFoundError",
        parser=parse_version,
        contents="No version to parse",
        contents_stdout=True,
        calctype=CalcType.energy,
        success=False,
    ),
    ParserTestCase(
        name="Parse energy CalcType.energy",
        parser=parse_energy,
        contents=Path("crest.engrad"),
        contents_stdout=False,
        calctype=CalcType.energy,
        success=True,
        answer=-0.335557824179335,
    ),
    ParserTestCase(
        name="Parse energy CalcType.gradient",
        parser=parse_energy,
        contents=Path("crest.engrad"),
        contents_stdout=False,
        calctype=CalcType.gradient,
        success=True,
        answer=-0.335557824179335,
    ),
    ParserTestCase(
        name="Parse gradient CalcType.gradient",
        parser=parse_gradient,
        contents=Path("crest.engrad"),
        contents_stdout=False,
        calctype=CalcType.gradient,
        success=True,
        answer=gradients.water,
    ),
    ParserTestCase(
        name="Parse gradient CalcType.energy",
        parser=parse_gradient,
        contents=Path("crest.engrad"),
        contents_stdout=False,
        calctype=CalcType.energy,
        success=True,
        answer=gradients.water,
    ),
    ParserTestCase(
        name="Parse energy CalcType.hessian",
        parser=parse_energy_numhess,
        contents=Path("hessian_stdout.txt"),
        contents_stdout=True,
        calctype=CalcType.hessian,
        success=True,
        answer=-110.490788960984773,
    ),
    ParserTestCase(
        name="Parse numhess1",
        parser=parse_numhess1,
        contents=Path("numhess1"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=hessians.water,
    ),
    ParserTestCase(
        name="Parse frequencies HF",
        parser=parse_g98_freqs,
        contents=Path("g98HF.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=frequencies.HF,
    ),
    ParserTestCase(
        name="Parse frequencies water",
        parser=parse_g98_freqs,
        contents=Path("g98.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=frequencies.water,
    ),
    ParserTestCase(
        name="Parse frequencies caffeine",
        parser=parse_g98_freqs,
        contents=Path("g98big.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=frequencies.caffeine,
    ),
    ParserTestCase(
        name="Parse normal_modes HF",
        parser=parse_g98_normal_modes,
        contents=Path("g98HF.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=normal_modes.HF,
    ),
    ParserTestCase(
        name="Parse normal_modes water",
        parser=parse_g98_normal_modes,
        contents=Path("g98.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=normal_modes.water,
    ),
    ParserTestCase(
        name="Parse normal_modes caffeine",
        parser=parse_g98_normal_modes,
        contents=Path("g98big.out"),
        contents_stdout=False,
        calctype=CalcType.hessian,
        success=True,
        answer=normal_modes.caffeine,
    ),
    ParserTestCase(
        name="Parse conformers",
        parser=parse_conformers,
        contents=Path("crest_conformers.xyz"),
        contents_stdout=False,
        calctype=CalcType.conformer_search,
        success=True,
        answer=conformers.conformers,
    ),
    ParserTestCase(
        name="Parse rotamers",
        parser=parse_rotamers,
        contents=Path("crest_rotamers.xyz"),
        contents_stdout=False,
        calctype=CalcType.conformer_search,
        success=True,
        answer=conformers.rotamers,
    ),
    ParserTestCase(
        name="Parse optimization",
        parser=parse_trajectory,
        contents=Path("optstdout.txt"),
        contents_stdout=True,
        calctype=CalcType.optimization,
        success=True,
        answer=optimizations.optimization,
        extra_files=["crest.engrad", "crestopt.log"],
    ),
]


@pytest.mark.parametrize("test_case", test_cases, ids=lambda tc: tc.name)
def test_crest_parsers(test_data_dir, prog_input_factory, tmp_path, test_case):
    """
    Tests the crest parsers to ensure that they correctly parse the output files and
    behave correctly within the decode function.
    """
    run_test_harness(test_data_dir, prog_input_factory, tmp_path, test_case)


####################################################
################ Additional Tests ##################
####################################################


def test_parse_conformers_charge_multiplicity_updates(test_data_dir, prog_input_factory):
    # Change charge and multiplicity in prog_input
    prog_input = prog_input_factory("conformer_search")
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["structure"]["charge"] = -2
    prog_input_dict["structure"]["multiplicity"] = 3
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    directory = test_data_dir / "crest"
    data = parse_conformers(directory, None, ProgramInput(**prog_input_dict))
    # Check conformer energies
    for struct in data["conformers"]:
        assert struct.charge == -2
        assert struct.multiplicity == 3


def test_parse_rotamers_charge_multiplicity_updates(test_data_dir, prog_input_factory):
    # Change charge and multiplicity in prog_input
    prog_input = prog_input_factory("conformer_search")
    prog_input_dict = prog_input.model_dump()
    prog_input_dict["structure"]["charge"] = 3
    prog_input_dict["structure"]["multiplicity"] = 5
    # Using fake prog_input for water; need .structure.charge and .multiplicity
    directory = test_data_dir / "crest"
    data = parse_rotamers(directory, None, ProgramInput(**prog_input_dict))
    # Check conformer energies
    for struct in data["rotamers"]:
        assert struct.charge == 3
        assert struct.multiplicity == 5
