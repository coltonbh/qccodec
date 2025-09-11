from collections.abc import Mapping
from typing import Any

from qcio import CalcType, ProgramInput

from qccodec.exceptions import EncoderError
from qccodec.models import NativeInput

SUPPORTED_CALCTYPES = {
    CalcType.energy,
    CalcType.gradient,
    CalcType.hessian,
    CalcType.optimization,
    CalcType.transition_state,
}
XYZ_FILENAME = "geometry.xyz"
PADDING = 20  # padding between keyword and value in tc.in


def encode(inp_obj: ProgramInput) -> NativeInput:
    """Translate a ProgramInput into Orca input files.

    Args:
        inp_obj: The qcio ProgramInput object for a computation.

    Returns:
        NativeInput with .input being an orca.inp file and .geometry an xyz file.
    """
    # NumGrad
    numgrad_key = caseless_keyword_lookup(inp_obj.keywords, "numgrad")
    numgrad_val = inp_obj.keywords.get(numgrad_key)
    needs_numgrad = numgrad_key in inp_obj.keywords and isinstance(numgrad_val, Mapping) or bool(numgrad_val)

    # Set calctype, either directly or (if necessary) via the %method block
    calctype = None
    method_block_calctype = None
    if inp_obj.calctype.value == CalcType.energy:
        method_block_calctype = "energy"
    elif inp_obj.calctype.value == CalcType.gradient:
        method_block_calctype = "numgrad" if needs_numgrad else "gradient"
    elif inp_obj.calctype.value == CalcType.hessian:
        calctype = f"freq {numgrad_key}" if needs_numgrad else "freq"
    elif inp_obj.calctype.value == CalcType.optimization:
        calctype = f"opt {numgrad_key}" if needs_numgrad else "opt"
    elif inp_obj.calctype.value == CalcType.transition_state:
        calctype = f"optts {numgrad_key}" if needs_numgrad else "optts"
    else:
        msg = f"Calculation type {inp_obj.calctype.value} is not yet implemented."
        raise NotImplementedError(msg)

    # Collect lines for input file
    inp_lines = []

    # maxcore
    maxcore_key = caseless_keyword_lookup(inp_obj.keywords, "maxcore")
    if maxcore_key in inp_obj.keywords:
        inp_lines.append(f"%maxcore {inp_obj.keywords[maxcore_key]}")

    # Model
    inp_lines.append(f"! {inp_obj.model.method}")

    # CalcType
    #   - If it needs to be set as a global keyword...
    if calctype is not None:
        inp_lines.append(f"! {calctype}")

    #   - If it needs to be set via the "method" block...
    method_key = caseless_keyword_lookup(inp_obj.keywords, "method")
    if method_block_calctype is not None or method_key in inp_obj.keywords:
        inp_lines.append(f"%{method_key}")

        # If CalcType needs to be set in the method block, do so...
        block_keywords = inp_obj.keywords.get(method_key, {})
        if method_block_calctype is not None:
            inp_lines.append(f"    {'runtyp':<{PADDING}} {method_block_calctype}")

        if not isinstance(block_keywords, dict):
            msg = f"Expected a mapping for '{method_key}' block keywords, but got {type(block_keywords)}:\n{block_keywords}"
            raise EncoderError(msg)

        # Make sure the 'runtyp' keyword is not being used
        runtyp_key = caseless_keyword_lookup(block_keywords, "runtyp")
        if runtyp_key in block_keywords:
            msg = f"Cannot use '{runtyp_key}' keyword. Calculation types must be set at '.calctype'."
            raise EncoderError(msg)

        # Set other method block keywords
        for block_keyword, block_keyval in dict(block_keywords).items():
            inp_lines.append(f"    {block_keyword:<{PADDING}} {block_keyval}")
        inp_lines.append("end")

    # Basis
    basis_key = caseless_keyword_lookup(inp_obj.keywords, "basis")
    if inp_obj.model.basis is not None or basis_key in inp_obj.keywords:
        inp_lines.append(f"%{basis_key}")
        if inp_obj.model.basis is not None:
            inp_lines.append(f'    {"basis":<{PADDING}} "{inp_obj.model.basis}"')

        block_keywords = inp_obj.keywords.get(basis_key, {})
        if not isinstance(block_keywords, Mapping):
            msg = f"Expected a mapping for '{basis_key}' block keywords, but got {type(block_keywords)}:\n{block_keywords}"
            raise EncoderError(msg)

        for block_keyword, block_keyval in dict(block_keywords).items():
            # Add necessary quotes to basis set definitions
            if isinstance(block_keyval, str) and not block_keyval.casefold() in {
                "true".casefold(),
                "false".casefold(),
            }:
                block_keyval = f'"{block_keyval}"'

            inp_lines.append(f"    {block_keyword:<{PADDING}} {block_keyval}")
        inp_lines.append("end")

    # NumGrad
    if needs_numgrad and isinstance(numgrad_val, Mapping):
        inp_lines.append(f"%{numgrad_key}")
        for block_keyword, block_keyval in dict(numgrad_val).items():
            inp_lines.append(f"    {block_keyword:<{PADDING}} {block_keyval}")
        inp_lines.append("end")

    # Blocks
    for key in inp_obj.keywords:
        if key.casefold() not in {"maxcore".casefold(), "basis".casefold(), "numgrad".casefold()}:
            block_keywords = inp_obj.keywords.get(key)

            if not isinstance(block_keywords, Mapping):
                msg = f"Expected a mapping for '{key}' block keywords, but got {type(block_keywords)}:\n{block_keywords}"
                raise EncoderError(msg)

            inp_lines.append(f"%{key}")
            for block_keyword, block_keyval in dict(block_keywords).items():
                inp_lines.append(f"    {block_keyword:<{PADDING}} {block_keyval}")
            inp_lines.append("end")

    # Structure
    charge = inp_obj.structure.charge
    multiplicity = inp_obj.structure.multiplicity
    inp_lines.append(f"* xyzfile {charge} {multiplicity} {XYZ_FILENAME}")
    return NativeInput(
        input_file="\n".join(inp_lines) + "\n",
        geometry_file=inp_obj.structure.to_xyz(),
        geometry_filename=XYZ_FILENAME,
    )


# Helpers
def caseless_keyword_lookup(keywords: dict[str, Any], key: str) -> str:
    """Find a caseless keyword in a mapping.

    If present, returns the keyword in the mapping. Otherwise, returns the input keyword.
    """
    return next((k for k in keywords if k.casefold() == key.casefold()), key)
