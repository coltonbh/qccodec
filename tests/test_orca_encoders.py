import pytest
from qcio import CalcType, Model, ProgramInput
from qcio.utils import water

from qccodec.encoders.orca import _validate_keywords, encode
from qccodec.exceptions import EncoderError


@pytest.mark.parametrize(
    "calctype, extra_keywords",
    [
        (CalcType.energy, {}),
        (CalcType.gradient, {}),
        (CalcType.gradient, {"numgrad": True}),
        (CalcType.gradient, {"numgrad": {"accuracy": 6, "dx": 0.002}}),
        (CalcType.hessian, {"freq": {"numfreq": True}}),
        (CalcType.hessian, {"freq": {"numfreq": True}, "numgrad": True}),
        (CalcType.optimization, {"geom": {"maxiter": 30}}),
        (CalcType.optimization, {"geom": {"maxiter": 30}, "numgrad": True}),
        (CalcType.transition_state, {"geom": {"calc_hess": True, "numhess": True}}),
        (
            CalcType.transition_state,
            {"geom": {"calc_hess": True, "numhess": True}, "numgrad": True},
        ),
    ],
)
def test_write_input_files(calctype: CalcType, extra_keywords: dict[str, object]):
    """Test write_input_files method."""
    inp_obj = ProgramInput(
        calctype=calctype,
        model=Model(method="revdsd-pbep86-d4/2021", basis="def2-svp"),
        structure=water,
        keywords={
            "maxcore": 500,
            "basis": {"auxc": "def2-svp/c", "decontractbas": True},
            "scf": {
                "convergence": "verytight",
            },
            **extra_keywords,
        },
    )
    native_input = encode(inp_obj)
    print(native_input.input_file)


def test_encode_raises_error_conflicting_runtyp_keyword():
    """For certain calctypes, the method block 'runtyp' keyword cannot be used."""
    inp_obj = ProgramInput(
        calctype=CalcType.energy,
        model=Model(method="hf", basis="sto-3g"),
        structure=water,
        keywords={
            "method": {"runtyp": "sp"},
            "basis": {"auxc": "def2-svp/c", "decontractbas": True},
            "scf": {
                "convergence": "verytight",
            },
        },
    )
    with pytest.raises(EncoderError):
        encode(inp_obj)


def test_validate_keywords_raises_error_if_coords_block_in_keywords():
    """The 'coords' block should not be set directly as a keyword."""

    keywords = {"coords": {"units": "angstrom"}}
    with pytest.raises(EncoderError):
        _validate_keywords(keywords)


def test_validate_keywords_raises_error_if_method_block_contains_method_keyword():
    """The 'method' keyword should not be set inside the 'method' block."""
    keywords = {"method": {"method": "b3lyp"}}
    with pytest.raises(EncoderError):
        _validate_keywords(keywords)


def test_validate_keywords_raises_error_if_method_block_contains_runtyp_keyword():
    """The 'runtyp' keyword should not be set inside the 'method' block."""
    keywords = {"method": {"runtyp": "sp"}}
    with pytest.raises(EncoderError):
        _validate_keywords(keywords)


def test_validate_keywords_raises_error_if_basis_block_contains_basis_keyword():
    """The 'basis' keyword should not be set inside the 'basis' block."""
    keywords = {"basis": {"basis": "def2-svp"}}
    with pytest.raises(EncoderError):
        _validate_keywords(keywords)
