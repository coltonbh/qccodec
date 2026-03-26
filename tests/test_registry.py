from enum import Enum

import pytest
from qcdata import CalcType

from qccodec.exceptions import RegistryError
from qccodec.registry import ParserSpec


class MockFileType(Enum):
    stdout = "stdout"
    input = "input"
    directory = "directory"


def mock_parser_function():
    pass


def another_mock_parser_function():
    pass


def test_get_parsers_by_program(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    parsers = parser_registry.get_parsers(program="mock_program")
    assert len(parsers) == 1
    assert parsers[0] == parser_spec


def test_get_parsers_by_program_and_filetype(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    parsers = parser_registry.get_parsers(
        program="mock_program", filetype=MockFileType.stdout
    )
    assert len(parsers) == 1
    assert parsers[0] == parser_spec


def test_get_parsers_by_program_and_calctype(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    parsers = parser_registry.get_parsers(
        program="mock_program", calctype=CalcType.energy
    )
    assert len(parsers) == 1
    assert parsers[0] == parser_spec


def test_get_parsers_no_match(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    parsers = parser_registry.get_parsers(
        program="mock_program", filetype=MockFileType.directory
    )
    assert len(parsers) == 0


def test_supported_programs(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    programs = parser_registry.supported_programs()
    assert len(programs) == 1
    assert programs[0] == "mock_program"


def test_supported_filetypes(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    filetypes = parser_registry.supported_filetypes("mock_program")
    assert len(filetypes) == 1
    assert filetypes[0] == "stdout"


def test_get_spec_for_registered_parser(parser_registry):
    parser_spec = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec)
    spec = parser_registry.get_spec(mock_parser_function)
    assert spec == parser_spec


def test_get_spec_for_unregistered_parser_raises_error(parser_registry):
    with pytest.raises(RegistryError, match="No parser registered for"):
        parser_registry.get_spec(mock_parser_function)


def test_parser_spec_without_target_raises_error(parser_registry):
    with pytest.raises(RegistryError):
        parser_spec = ParserSpec(
            parser=mock_parser_function,
            filetype=MockFileType.stdout,
            required=True,
            calctypes=[CalcType.energy],
            program="mock_program",
            target=None,
        )


def test_directory_parser_spec_without_target_ok(parser_registry):
    ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.directory,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target=None,
    )


def test_register_duplicate_target_raises_error(parser_registry):
    parser_spec1 = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_spec2 = ParserSpec(
        parser=another_mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_registry.register(parser_spec1)
    with pytest.raises(RegistryError, match="Duplicate parser target"):
        parser_registry.register(parser_spec2)


def test_register_different_targets_same_program(parser_registry):
    parser_spec1 = ParserSpec(
        parser=mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.energy],
        program="mock_program",
        target="energy",
    )
    parser_spec2 = ParserSpec(
        parser=another_mock_parser_function,
        filetype=MockFileType.stdout,
        required=True,
        calctypes=[CalcType.gradient],
        program="mock_program",
        target="gradient",
    )
    parser_registry.register(parser_spec1)
    parser_registry.register(parser_spec2)
    assert len(parser_registry.registry["mock_program"]) == 2
