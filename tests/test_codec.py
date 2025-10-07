import pytest

from qccodec.codec import decode, encode
from qccodec.encoders import terachem
from qccodec.exceptions import EncoderError


def test_main_terachem_energy(terachem_file):
    """Test the main terachem energy encoder."""
    contents = terachem_file("water.energy.out")
    computed_props = decode("terachem", "energy", stdout=contents)
    assert computed_props.energy == -76.3861099088


def test_encode_raises_error_with_invalid_calctype(spec_factory):
    spec_factory = spec_factory("transition_state")  # Not currently supported by crest encoder
    with pytest.raises(EncoderError):
        encode(spec_factory, "crest")


def test_main_terachem_encoder(spec_factory):
    spec_factory = spec_factory("energy")
    spec_factory.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(spec_factory, "terachem")
    correct_tcin = (
        f"{'run':<{terachem.PADDING}} {spec_factory.calctype.value}\n"
        f"{'coordinates':<{terachem.PADDING}} {terachem.XYZ_FILENAME}\n"
        f"{'charge':<{terachem.PADDING}} {spec_factory.structure.charge}\n"
        f"{'spinmult':<{terachem.PADDING}} {spec_factory.structure.multiplicity}\n"
        f"{'method':<{terachem.PADDING}} {spec_factory.model.method}\n"
        f"{'basis':<{terachem.PADDING}} {spec_factory.model.basis}\n"
        f"{'purify':<{terachem.PADDING}} {spec_factory.keywords['purify']}\n"
        f"{'some-bool':<{terachem.PADDING}} "
        f"{str(spec_factory.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin
