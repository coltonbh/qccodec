import pytest

from qccodec.encoders.terachem import PADDING, XYZ_FILENAME, encode
from qccodec.exceptions import EncoderError


def test_write_input_files(spec_factory):
    """Test write_input_files method."""
    spec_factory = spec_factory("energy")
    spec_factory.keywords.update({"purify": "no", "some-bool": False})

    native_input = encode(spec_factory)
    # Testing that we capture:
    # 1. Driver
    # 2. Structure
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)

    correct_tcin = (
        f"{'run':<{PADDING}} {spec_factory.calctype.value}\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {spec_factory.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {spec_factory.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {spec_factory.model.method}\n"
        f"{'basis':<{PADDING}} {spec_factory.model.basis}\n"
        f"{'purify':<{PADDING}} {spec_factory.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(spec_factory.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin


def test_write_input_files_renames_hessian_to_frequencies(spec_factory):
    """Test write_input_files method for hessian."""
    # Modify input to be a hessian calculation
    spec_factory = spec_factory("hessian")
    spec_factory.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(spec_factory)

    assert native_input.input_file == (
        f"{'run':<{PADDING}} frequencies\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {spec_factory.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {spec_factory.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {spec_factory.model.method}\n"
        f"{'basis':<{PADDING}} {spec_factory.model.basis}\n"
        f"{'purify':<{PADDING}} {spec_factory.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(spec_factory.keywords['some-bool']).lower()}\n"
    )


def test_encode_raises_error_qcio_args_passes_as_keywords(spec_factory):
    """These keywords should not be in the .keywords dict. They belong on structured
    qcio objects instead."""
    qcio_keywords_from_terachem = ["charge", "spinmult", "method", "basis", "run"]
    spec_factory = spec_factory("energy")
    for keyword in qcio_keywords_from_terachem:
        spec_factory.keywords[keyword] = "some value"
        with pytest.raises(EncoderError):
            encode(spec_factory)
