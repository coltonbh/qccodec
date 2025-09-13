import pytest

from qccodec.codec import decode, encode
from qccodec.encoders import terachem
from qccodec.exceptions import EncoderError


def test_main_terachem_energy(terachem_file):
    """Test the main terachem energy encoder."""
    contents = terachem_file("water.energy.out")
    computed_props = decode("terachem", "energy", stdout=contents)
    assert computed_props.energy == -76.3861099088


def test_encode_raises_error_with_invalid_calctype(prog_inp):
    prog_inp = prog_inp("transition_state")  # Not currently supported by crest encoder
    with pytest.raises(EncoderError):
        encode(prog_inp, "crest")


def test_main_terachem_encoder(prog_inp):
    prog_inp = prog_inp("energy")
    prog_inp.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(prog_inp, "terachem")
    correct_tcin = (
        f"{'run':<{terachem.PADDING}} {prog_inp.calctype.value}\n"
        f"{'coordinates':<{terachem.PADDING}} {terachem.XYZ_FILENAME}\n"
        f"{'charge':<{terachem.PADDING}} {prog_inp.structure.charge}\n"
        f"{'spinmult':<{terachem.PADDING}} {prog_inp.structure.multiplicity}\n"
        f"{'method':<{terachem.PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{terachem.PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{terachem.PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{terachem.PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin
