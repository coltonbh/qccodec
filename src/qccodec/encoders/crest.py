import copy
import os
from typing import Any

import tomli_w
from qcio import CalcSpec, CalcType

from qccodec.exceptions import EncoderError
from qccodec.models import NativeInput

SUPPORTED_CALCTYPES = {
    CalcType.conformer_search,
    CalcType.optimization,
    CalcType.energy,
    CalcType.gradient,
    CalcType.hessian,
}


def encode(inp_obj: CalcSpec) -> NativeInput:
    """Translate a CalcSpec into CREST inputs files.

    Args:
        inp_obj: The qcio CalcSpec object for a computation.

    Returns:
        NativeInput with .input_files being a crest.toml file and .geometry_file the
            Structure's xyz file.
    """
    validate_input(inp_obj)
    struct_filename = "structure.xyz"

    return NativeInput(
        input_file=tomli_w.dumps(_to_toml_dict(inp_obj, struct_filename)),
        geometry_file=inp_obj.structure.to_xyz(),
        geometry_filename=struct_filename,
    )


def validate_input(inp_obj: CalcSpec):
    """Validate the input for CREST.

    Args:
        inp_obj: The qcio CalcSpec object for a computation.

    Raises:
        EncoderError: If the input is invalid.
    """
    # These values come from other parts of the CalcSpec and should not be set
    # in the keywords.
    non_allowed_keywords = ["charge", "uhf"]
    for keyword in non_allowed_keywords:
        if keyword in inp_obj.keywords:
            raise EncoderError(
                f"{keyword} should not be set in keywords for CREST. It is already set "
                "on the Structure or CalcSpec elsewhere.",
            )
    if "runtype" in inp_obj.keywords:
        _validate_runtype_calctype(inp_obj.keywords["runtype"], inp_obj.calctype)


def _validate_runtype_calctype(runtype: str, calctype: CalcType):
    """Validate that the runtype is supported for the calctype."""
    invalid_runtype = False
    valid_runtypes = set()

    if calctype == CalcType.conformer_search:
        valid_runtypes = {"imtd-gc", "imtd-smtd", "entropy", "nci", "nci-mtd"}
        if runtype not in valid_runtypes:
            invalid_runtype = True

    elif calctype == CalcType.optimization:
        valid_runtypes = {"optimize", "ancopt"}
        if runtype not in valid_runtypes:
            invalid_runtype = True

    elif calctype in {CalcType.energy, CalcType.gradient}:
        valid_runtypes = {"singlepoint"}
        if runtype not in valid_runtypes:
            invalid_runtype = True

    elif calctype == CalcType.hessian:
        valid_runtypes = {"numhess"}
        if runtype not in valid_runtypes:
            invalid_runtype = True

    if invalid_runtype:
        raise EncoderError(
            f"Unsupported runtype {runtype} for calctype {calctype}. Valid runtypes "
            f"are: {valid_runtypes}.",
        )


def _to_toml_dict(inp_obj: CalcSpec, struct_filename: str) -> dict[str, Any]:
    """Convert a CalcSpec object to a dictionary in the CREST format of TOML.

    This function makes it easier to test for the correct TOML structure.
    """
    # Start with existing keywords
    toml_dict = copy.deepcopy(inp_obj.keywords)

    # Top level keywords
    # Logical cores was 10% faster than physical cores, so not using psutil
    toml_dict.setdefault("threads", min(os.cpu_count() or 16, 16))
    toml_dict["input"] = struct_filename

    # Set default runtype if not already set
    if "runtype" not in inp_obj.keywords:
        if inp_obj.calctype == CalcType.conformer_search:
            toml_dict["runtype"] = "imtd-gc"
        elif inp_obj.calctype == CalcType.optimization:
            toml_dict["runtype"] = "optimize"
        elif inp_obj.calctype in {CalcType.energy, CalcType.gradient}:
            toml_dict["runtype"] = "singlepoint"
        elif inp_obj.calctype == CalcType.hessian:
            toml_dict["runtype"] = "numhess"
        else:
            raise EncoderError(
                f"Unsupported calctype {inp_obj.calctype} for CREST encoder.",
            )

    # Calculation level keywords
    calculation = toml_dict.pop("calculation", {})
    calculation_level = calculation.pop("level", [])
    if len(calculation_level) == 0:
        calculation_level.append({})
    for level_dict in calculation_level:
        level_dict["method"] = inp_obj.model.method
        level_dict["charge"] = inp_obj.structure.charge
        level_dict["uhf"] = inp_obj.structure.multiplicity - 1

    calculation["level"] = calculation_level
    toml_dict["calculation"] = calculation

    return toml_dict
