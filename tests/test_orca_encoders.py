import pytest
from qcio import CalcType, Model, ProgramInput
from qcio.utils import water

from qccodec.encoders.orca import encode
from qccodec.exceptions import EncoderError


@pytest.mark.parametrize(
    "calctype, extra_keywords",
    [
        (CalcType.energy, {}),
        (CalcType.gradient, {}),
        (CalcType.hessian, {"freq": {"numfreq": True}}),
        (CalcType.optimization, {"geom": {"maxiter": 30}}),
        (CalcType.transition_state, {"geom": {"calc_hess": True, "numhess": True}}),
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
