import inspect
import shutil
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from qcio import CalcSpec, CalcType
from qcio.utils import water

from qccodec.codec import decode
from qccodec.exceptions import MatchNotFoundError
from qccodec.registry import ParserRegistry, registry


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def parser_registry():
    return ParserRegistry()


@pytest.fixture
def terachem_file(test_data_dir):
    """Return a function that reads a file from the 'terachem' subdirectory."""

    def _read(filename: str) -> str:
        return (test_data_dir / "terachem" / filename).read_text()

    return _read


@pytest.fixture
def crest_file(test_data_dir):
    """Return a function that reads a file from the 'crest' subdirectory."""

    def _read(filename: str) -> str:
        return (test_data_dir / "crest" / filename).read_text()

    return _read


@pytest.fixture(scope="session")
def spec_factory():
    """Create a function that returns a CalcSpec object with a specified
    calculation type."""

    def create_spec(calctype):
        return CalcSpec(
            structure=water,
            calctype=calctype,
            # Tests depend up this model; do not change
            model={"method": "hf", "basis": "sto-3g"},
        )

    return create_spec


@dataclass
class ParserTestCase:
    """Test case for a parser function.

    Attributes:
        name: A human-readable name for the test case.
        parser: The parser function to be tested.
        contents: The input data for the parser, either as a string or a Path.
        contents_stdout: Boolean indicating if the contents should be treated as stdout.
        calctype: The calculation type for the test case.
        success: Boolean indicating if the parser should succeed on the contents.
        decode_exc: Boolean indicating if an exception is expected for MatchNotFound
            errors during decode. Default is True. required=False parsers should not
            raise an error.
        answer: The expected output from the parser.
        clear_registry: Boolean indicating if the registry should be cleared of all other
            parsers before running the test. Default is True.
        extra_files: Optional list of additional files to be copied to the test directory.
        extra_files_names: Optional list of names for the extra files, these names will
            be used as the filenames in the test directory. If not provided, the
            filenames will be the same as in the extra_files list.
        calc_spec: Optional CalcSpec to be used instead of the default one created
            from the calctype.

    """

    name: str
    parser: Callable
    contents: str | Path
    contents_stdout: bool
    calctype: CalcType
    success: bool
    decode_exc: bool = True
    answer: Any | None = None
    clear_registry: bool = True
    extra_files: list[str] | None = None
    extra_files_names: list[str] | None = None
    calc_spec: CalcSpec | None = None


def _load_contents(directory, contents):
    """Load the contents of a TestCase."""
    if isinstance(contents, Path):
        # Contents is a Path, so we read the file directly.
        return (directory / contents).read_text()
    else:
        # Contents is a string, so we assume it's the content itself.
        return contents


def get_target_value(results, target):
    """Lookup the value of a target in the results dictionary.
    Args:
        results: The results dictionary.
        target: The target key or tuple of keys to look up.
    """
    keys = target if isinstance(target, tuple) else (target,)
    d = results
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    return d.get(keys[-1], None)


def _test_parser_direct(tc, contents, directory, spec, parser_spec):
    """Test the parser function directly with the provided contents.

    Args:
        tc: The TestCase object containing the test parameters.
        contents: The contents to be parsed.
        directory: The directory containing the test data files.
        spec: The CalcSpec to provide to directory parsers.
        parser_spec: The specification of the parser being tested.
    """
    if tc.success:
        # Successful execution of directory parser
        if parser_spec.filetype == "directory":
            parsed = tc.parser(
                directory,
                contents if tc.contents_stdout else None,
                spec,
            )
        else:
            # Successful execution of file parser
            parsed = tc.parser(contents)
        assert parsed == tc.answer, (
            f"{tc.name}: Direct parsing returned {parsed} instead of expected {tc.answer}"
        )

    else:
        with pytest.raises(MatchNotFoundError):
            if parser_spec.filetype == "directory":
                # Expect an exception for directory parser
                tc.parser(
                    directory,
                    contents if tc.contents_stdout else None,
                    spec,
                )
            else:
                # Expect an exception for file parser
                tc.parser(contents)


def _test_decode_integration(tc, contents, directory, spec, program, parser_spec):
    """
    Test the decode() integration, using only the parser under test (unless tc.clear_registry is False).

    Args:
        tc: The TestCase object containing the test parameters.
        contents: The contents to be parsed (needed if tc.contents_stdout is True).
        directory: The directory containing the test data files.
        spec: The CalcSpec to provide to decode().
        program: The name of the program being tested.
        parser_spec: The specification of the parser being tested.

    Notes:
        - This test doesn't work for cases when the parser is a directory parser
            (i.e., filetype == "directory") and then we pass fake contents like
            "No energy here" but the parser is operating on, e.g., the crest.engrad file
            in the test data directory. It will not raise an exception as the parser will
            see the crest.engrad file. We may want to update this function to use a
            temporary directory and then write the contents variable to a file in that
            directory using parser_spec.filetype.value.

    """
    if tc.success:
        # Successful execution of decode
        result = decode(
            program,
            tc.calctype,
            stdout=(contents if tc.contents_stdout else None),
            directory=directory,
            input_data=spec,
            as_dict=True,
        )
        if parser_spec.target is not None:
            final_value = get_target_value(result, parser_spec.target)
        else:
            # If the target is None, we assume the entire result is the value.
            final_value = result
        assert final_value == tc.answer, (
            f"{tc.name}: decode() returned {final_value} for target '{parser_spec.target}' "
            f"instead of expected {tc.answer}"
        )
    else:
        if tc.decode_exc:
            # Failed execution and required is True
            with pytest.raises(MatchNotFoundError):
                decode(
                    program,
                    tc.calctype,
                    stdout=(contents if tc.contents_stdout else None),
                    directory=directory,
                    input_data=spec,
                )
        else:
            # Failed execution and required is False
            result = decode(
                program,
                tc.calctype,
                stdout=(contents if tc.contents_stdout else None),
                directory=directory,
                input_data=spec,
                as_dict=True,
            )
            final_value = get_target_value(result, parser_spec.target)
            assert final_value in (None, {}), (
                f"{tc.name}: decode() returned non-empty value {final_value} when an empty result was expected."
            )


@contextmanager
def restore_registry(program: str):
    """Context manager that restores the original registry for a program."""
    original = registry.get_parsers(program)
    try:
        yield
    finally:
        registry.registry[program] = original


def run_test_harness(test_data_dir, spec_factory, tmp_path, tc):
    """
    Args:
        test_data_dir: The base directory containing test data files.
        spec_factory: A function that creates a CalcSpec given a CalcType.
        tmp_path: A temporary directory Path for the test.
        tc: The ParserTestCase object containing the test parameters.

    Notes:
        Runs the full test harness:
            1. Load the contents.
            2. Run the parser directly.
            3. Temporarily restrict the registry to only the parser under test,
                and run the decode() integration test.
    """
    program = inspect.getmodule(tc.parser).__name__.split(".")[-1]
    contents = _load_contents(test_data_dir / program, tc.contents)
    # Get the spec for the parser under test.
    parser_spec = registry.get_spec(tc.parser)

    spec = tc.calc_spec or spec_factory(tc.calctype)

    # Copy over extra files if provided.
    if tc.extra_files:
        # Use the extra_files_names if provided, otherwise use extra_files.
        extra_files_names = tc.extra_files_names or tc.extra_files
        for extra_file, extra_file_name in zip(tc.extra_files, extra_files_names):
            # Copy the extra file to the temporary directory.
            shutil.copy(
                test_data_dir / program / extra_file,
                tmp_path / extra_file_name,
            )

    if not tc.contents_stdout:
        # If contents is not stdout, copy the test data files.
        if parser_spec.filetype == "directory":
            # Use the name given in the contents variable.
            filepath = tmp_path / tc.contents
        else:
            # Use the filetype from the parser spec.
            filepath = tmp_path / parser_spec.filetype.value
        # Write the contents to the temporary file.
        filepath.write_text(contents)

    # Test the parser directly.
    _test_parser_direct(tc, contents, tmp_path, spec, parser_spec)

    # Now test integration via decode() with a restricted registry.
    with restore_registry(program):
        if tc.clear_registry:
            # Clear the registry of all other parsers for this program.
            registry.registry.pop(program)
            registry.registry[program] = [parser_spec]
        _test_decode_integration(tc, contents, tmp_path, spec, program, parser_spec)
