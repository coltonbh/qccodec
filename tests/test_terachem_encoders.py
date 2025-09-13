import pytest

from qccodec.encoders.terachem import PADDING, XYZ_FILENAME, encode
from qccodec.exceptions import EncoderError


def test_write_input_files(prog_inp):
    """Test write_input_files method."""
    prog_inp = prog_inp("energy")
    prog_inp.keywords.update({"purify": "no", "some-bool": False})

    native_input = encode(prog_inp)
    # Testing that we capture:
    # 1. Driver
    # 2. Structure
    # 3. Model
    # 4. Keywords (test booleans to lower case, ints, sts, floats)

    correct_tcin = (
        f"{'run':<{PADDING}} {prog_inp.calctype.value}\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {prog_inp.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {prog_inp.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )
    assert native_input.input_file == correct_tcin


def test_write_input_files_renames_hessian_to_frequencies(prog_inp):
    """Test write_input_files method for hessian."""
    # Modify input to be a hessian calculation
    prog_inp = prog_inp("hessian")
    prog_inp.keywords.update({"purify": "no", "some-bool": False})
    native_input = encode(prog_inp)

    assert native_input.input_file == (
        f"{'run':<{PADDING}} frequencies\n"
        f"{'coordinates':<{PADDING}} {XYZ_FILENAME}\n"
        f"{'charge':<{PADDING}} {prog_inp.structure.charge}\n"
        f"{'spinmult':<{PADDING}} {prog_inp.structure.multiplicity}\n"
        f"{'method':<{PADDING}} {prog_inp.model.method}\n"
        f"{'basis':<{PADDING}} {prog_inp.model.basis}\n"
        f"{'purify':<{PADDING}} {prog_inp.keywords['purify']}\n"
        f"{'some-bool':<{PADDING}} "
        f"{str(prog_inp.keywords['some-bool']).lower()}\n"
    )


def test_encode_raises_error_qcio_args_passes_as_keywords(prog_inp):
    """These keywords should not be in the .keywords dict. They belong on structured
    qcio objects instead."""
    qcio_keywords_from_terachem = ["charge", "spinmult", "method", "basis", "run"]
    prog_inp = prog_inp("energy")
    for keyword in qcio_keywords_from_terachem:
        prog_inp.keywords[keyword] = "some value"
        with pytest.raises(EncoderError):
            encode(prog_inp)
