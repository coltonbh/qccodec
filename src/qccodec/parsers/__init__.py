"""All parsers should follow a basic pattern:

1. Extract the parsed data, cast to its appropriate Python type, set it on the
    SinglePointData object at the appropriate attribute name.
2. Raise a MatchNotFound error if a match was not found
3. Register parser with the registry by decorating it with the parser() decorator

Use the .utils.regex_search() helper function in place of re.search() to
ensure that a MatchNotFoundError will be raised in a parser. More sophisticated parsers
that use re.findall (like terachem.parse_hessian) or rely upon not finding a match may
implement a different interface, but please strive to follow this basic patterns as much
as possible.
"""

# Required for parsers to register
from .terachem import *  # noqa:  F403
