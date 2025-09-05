from collections.abc import Mapping, Sequence

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
    # Set calctype, either directly or (if necessary) via the %method block
    runtype = None
    calctype = None
    if inp_obj.calctype.value == CalcType.hessian:
        calctype = "freq"
    elif inp_obj.calctype.value == CalcType.optimization:
        calctype = "opt"
    elif inp_obj.calctype.value == CalcType.transition_state:
        calctype = "optts"
    else:
        runtype = inp_obj.calctype.value

    # Collect lines for input file
    inp_lines = []

    # Global variables
    global_variables = inp_obj.keywords.get("%", [])
    if not isinstance(global_variables, Sequence):
        msg = f"Expected a sequence for '%' global variables, but got {type(global_variables)}:\n{global_variables}"
        raise EncoderError(msg)

    for global_variable in global_variables:
        inp_lines.append(f"% {global_variable}")

    # Model
    inp_lines.append(f"! {inp_obj.model.method} {inp_obj.model.basis}")

    # Global keywords
    global_keywords = inp_obj.keywords.get("!", [])
    if not isinstance(global_keywords, Sequence):
        msg = f"Expected a sequence for '!' global keywords, but got {type(global_keywords)}:\n{global_keywords}"
        raise EncoderError(msg)

    for global_keyword in global_keywords:
        inp_lines.append(f"! {global_keyword}")

    # CalcType, if it needs to be set as a global keyword
    if calctype is not None:
        inp_lines.append(f"! {calctype}")

    # Method block, with CalcType if it needs to be set here
    method_key = caseless_keyword_lookup(inp_obj.keywords, "method")
    if runtype is not None or method_key in inp_obj.keywords:
        method_keywords = inp_obj.keywords.get(method_key, {})
        if not isinstance(method_keywords, Mapping):
            msg = f"Expected a mapping for 'method' block keywords, but got {type(method_keywords)}:\n{method_keywords}"
            raise EncoderError(msg)

        inp_lines.append(f"%{method_key}")
        # Set the CalcType via the 'RunTyp' keyword, if needed
        runtype_key = caseless_keyword_lookup(method_keywords, "runtyp")
        if runtype is not None:
            if runtype_key in method_keywords:
                msg = (
                    f"Keyword '{runtype_key}' should not be set as a method block "
                    f"keyword. It should be set at '.calctype'."
                )
                raise EncoderError(msg)
            inp_lines.append(f"    {runtype_key:<{PADDING}} {runtype}")
        # Set other method block keywords, if any
        for method_keyword, method_keyval in dict(method_keywords).items():
            inp_lines.append(f"    {method_keyword:<{PADDING}} {method_keyval}")
        inp_lines.append("end")

    # Other blocks
    for key in inp_obj.keywords:
        if key not in {"!", "%", "method"}:
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
def caseless_keyword_lookup(keywords: Mapping, key: str) -> str:
    """Find a caseless keyword in a mapping.

    If present, returns the keyword in the mapping. Otherwise, returns the input keyword.
    """
    return next((k for k in keywords if are_equal_caseless_strings(k, key)), key)


def are_equal_caseless_strings(obj1: object, obj2: object) -> bool:
    """Check if two objects are strings that are caselessly equal."""
    if isinstance(obj1, str) and isinstance(obj2, str):
        return obj1.casefold() == obj2.casefold()
    return False
