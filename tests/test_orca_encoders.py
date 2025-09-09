import pytest
from qcio import ProgramInput
from qcio.utils import water

from qccodec.encoders.orca import encode


@pytest.mark.parametrize(
    "calctype, extra_keywords",
    [
        ("energy", {}),
        ("gradient", {}),
        ("hessian", {"freq": {"numfreq": True}}),
        ("optimization", {"geom": {"maxiter": 30}}),
        ("transition_state", {"geom": {"calc_hess": True, "numhess": True}}),
    ],
)
def test_write_orca_input_files(calctype: str, extra_keywords: dict[str, object]):
    """Test write_input_files method."""
    inp_obj = ProgramInput(
        calctype=calctype,
        model={"method": "revdsd-pbep86-d4/2021", "basis": "def2-svp"},
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


if __name__ == "__main__":
    test_write_orca_input_files(
        "optimization", {"geom": {"maxiter": 30, "calc_hess": True, "numhess": True}}
    )
