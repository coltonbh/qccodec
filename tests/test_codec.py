import pytest

from qccodec.codec import decode, encode
from qccodec.encoders import terachem
from qccodec.exceptions import EncoderError


def test_main_terachem_energy(terachem_file):
    """Test the main terachem energy encoder."""
    contents = terachem_file("water.energy.out")
    computed_props = decode("terachem", "energy", stdout=contents)
    assert computed_props.energy == -76.3861099088


def test_encode_raises_error_with_invalid_calctype(prog_input_factory):
    prog_input_factory = prog_input_factory("transition_state")  # Not currently supported by crest encoder
    with pytest.raises(EncoderError):
        encode(prog_input_factory, "crest")


def test_main_terachem_encoder(prog_input_factory):
    prog_input_factory = prog_input_factory("energy")
    prog_input_factory.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(prog_input_factory, "terachem")
    correct_tcin = (
        f"{'run':<{terachem.PADDING}} {prog_input_factory.calctype.value}\n"
        f"{'coordinates':<{terachem.PADDING}} {terachem.XYZ_FILENAME}\n"
        f"{'charge':<{terachem.PADDING}} {prog_input_factory.structure.charge}\n"
        f"{'spinmult':<{terachem.PADDING}} {prog_input_factory.structure.multiplicity}\n"
        f"{'method':<{terachem.PADDING}} {prog_input_factory.model.method}\n"
        f"{'basis':<{terachem.PADDING}} {prog_input_factory.model.basis}\n"
        f"{'purify':<{terachem.PADDING}} {prog_input_factory.keywords['purify']}\n"
        f"{'some-bool':<{terachem.PADDING}} "
        f"{str(prog_input_factory.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin
