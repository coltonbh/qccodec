import inspect
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from qcio import CalcType

from qccodec.exceptions import RegistryError


@dataclass
class ParserSpec:
    """Specification for a parser function.

    This class holds information about the parser function, the filetype it operates on,
    whether it is required, the calculation types it works on, and where to place the
    parsed output on the data collector.

    Attributes:
        parser: The parser function.
        filetype: The filetype that the parser is for.
        required: Whether a MatchNotFoundError should be raised in the decode function
            if the parser fails. Typically True, but should be set to False on parsers
            for values that are not always present such as excited state energies.
        calctypes: The calculation types that the parser works on.
        target: The location on the data collector where the parser's output should be placed.
        program: The name of the program that the parser is for. Set automatically by the
            `register` decorator.
    """

    parser: Callable
    filetype: Enum
    required: bool
    calctypes: list[CalcType]
    program: str
    target: str | tuple[str, ...] | None = None

    def __post_init__(self):
        """Ensure that the parser function is Callable and that target exists unless filetype is directory."""
        if not callable(self.parser):
            raise RegistryError(f"Parser '{self.parser}' is not Callable.")
        # Ensure all non-directory parsers have a target
        if self.target is None and self.filetype.value != "directory":
            raise RegistryError(
                f"Parser '{self.parser.__name__}' for program "
                f"'{self.program}' must have a target if it is not a directory parser."
            )
        # Ensure that the target is a string or tuple of strings
        if self.target and not isinstance(self.target, (str, tuple)):
            raise RegistryError(
                f"Target '{self.target}' must be a string or tuple of strings."
            )


@dataclass
class ParserRegistry:
    """Registry for parser functions."""

    registry: dict[str, list[ParserSpec]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def register(self, parser_spec: ParserSpec) -> None:
        """Register a new parser function. Enforce that no two parsers for the same program use the same target.

        Args:
            parser_spec: ParserSpec objects containing the parser function and
                information about the parser.
        """

        # Ensure that the target is unique for the program and filetype
        for registered_spec in self.registry.get(parser_spec.program, []):
            if (
                parser_spec.target is not None  # not directory parser
                and registered_spec.target == parser_spec.target  # Same target
                and set(parser_spec.calctypes)
                & set(registered_spec.calctypes)  # Shared
            ):
                raise RegistryError(
                    f"Duplicate parser target '{parser_spec.target}' and calctype "
                    f"'{set(parser_spec.calctypes)& set(registered_spec.calctypes)}' "
                    f"registered for program '{parser_spec.program}'."
                )
        self.registry[parser_spec.program].append(parser_spec)

    def get_parsers(
        self,
        program: str,
        filetype: Enum | None = None,
        calctype: CalcType | None = None,
    ) -> list[ParserSpec]:
        """Get all parser functions for a given program.

        Args:
            program: The program to get parsers for.
            filetype: Filter parsers for this filetype.
            calctype: Filter parsers for this calctype.

        Returns:
            List of ParserSpec objects.
        """

        parser_specs: list[ParserSpec] = self.registry[program]
        if not parser_specs:
            raise RegistryError(f"No parsers registered for program '{program}'.")

        # Filter parsers by filetype and calctype
        if filetype:
            parser_specs = [ps for ps in parser_specs if ps.filetype == filetype]

        if calctype:
            parser_specs = [ps for ps in parser_specs if calctype in ps.calctypes]
        return parser_specs

    def supported_programs(self) -> list[str]:
        """Get all programs with registered parsers.

        Returns:
            List of program names.
        """
        return list(self.registry.keys())

    def supported_filetypes(self, program: str) -> list[str]:
        """Get all filetypes for a given program.

        Args:
            program: The program to get filetypes for.

        Returns:
            List of filetypes.
        """
        return list(
            {parser_info.filetype.value for parser_info in self.get_parsers(program)}
        )

    def get_spec(self, parser: Callable) -> ParserSpec:
        """Get the ParserSpec for a given parser function.

        Args:
            parser: The parser function.

        Returns:
            The ParserSpec object.
        """
        for program, specs in self.registry.items():
            for spec in specs:
                if spec.parser == parser:
                    return spec
        raise RegistryError(f"No parser registered for '{parser.__name__}'.")


registry = ParserRegistry()


def register(
    *,
    filetype: Enum,
    calctypes: list[CalcType] | None = None,
    required: bool = True,
    target: str | tuple[str, ...] | None = None,
):
    """Decorator to register a function in the parser registry.

    Args:
        filetype: The filetype the parser operates on.
        calctypes: A list of calculation types on which this parser should operate. If None, it applies to all CalcTypes.
        required: If True and the parser fails a MatchNotFoundError will be raised.
            If False and the parser fails the value will be ignored.
        target: Where on the data collector to assign the parsed result.

    Example:
        ```python
        @register(filetype=FileType.stdout, calctypes=[CalcType.energy, CalcType.gradient], target="energy")
        def parse_energy(contents: str) -> float:
            # Parsing logic here
            return energy_value
        ```
    """

    def decorator(func):
        # Get the function's module name. Should match program name.
        module = inspect.getmodule(func).__name__
        program_name = module.split(".")[-1]

        # Create ParserSpec
        spec = ParserSpec(
            program=program_name,
            parser=func,
            filetype=filetype,
            required=required,
            # If calctypes is None, register for all CalcType values
            calctypes=calctypes if calctypes is not None else list(CalcType),
            target=target,
        )

        # Register the function in the global registry
        registry.register(spec)

        return func

    return decorator
