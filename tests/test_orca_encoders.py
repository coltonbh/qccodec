import pytest
from qcio import CalcType, Model, ProgramInput
from qcio.utils import water

from qccodec.encoders.orca import encode


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
def test_write_orca_input_files(calctype: CalcType, extra_keywords: dict[str, object]):
    """Test write_input_files method."""
    inp_obj = ProgramInput(
        calctype=calctype,
        model=Model(method="revdsd-pbep86-d4/2021", basis="def2-svp"),
        structure=water,
        keywords={
            "%": ["maxcore 500"],
            "!": ["def2-svp/c"],
            "scf": {
                "convergence": "verytight",
            },
            **extra_keywords,
        },
    )
    native_input = encode(inp_obj)
    print(native_input.input_file)
