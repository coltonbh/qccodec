import pytest

from qccodec.encoders.terachem import PADDING, XYZ_FILENAME, encode
from qccodec.exceptions import EncoderError


def test_write_input_files(spec):
    """Test write_input_files method."""
    spec = spec("energy")
    spec.keywords.update({"purify": "no", "some-bool": False})

    native_input = encode(spec)
    # Testing that we capture:
    # 1. Driver
    # 2. Structure
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)

    correct_tcin = (
        f"{'run':<{PADDING}} {spec.calctype.value}\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {spec.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {spec.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {spec.model.method}\n"
        f"{'basis':<{PADDING}} {spec.model.basis}\n"
        f"{'purify':<{PADDING}} {spec.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(spec.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin


def test_write_input_files_renames_hessian_to_frequencies(spec):
    """Test write_input_files method for hessian."""
    # Modify input to be a hessian calculation
    spec = spec("hessian")
    spec.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(spec)

    assert native_input.input_file == (
        f"{'run':<{PADDING}} frequencies\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {spec.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {spec.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {spec.model.method}\n"
        f"{'basis':<{PADDING}} {spec.model.basis}\n"
        f"{'purify':<{PADDING}} {spec.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(spec.keywords['some-bool']).lower()}\n"
    )


def test_encode_raises_error_qcio_args_passes_as_keywords(spec):
    """These keywords should not be in the .keywords dict. They belong on structured
    qcio objects instead."""
    qcio_keywords_from_terachem = ["charge", "spinmult", "method", "basis", "run"]
    spec = spec("energy")
    for keyword in qcio_keywords_from_terachem:
        spec.keywords[keyword] = "some value"
        with pytest.raises(EncoderError):
            encode(spec)
