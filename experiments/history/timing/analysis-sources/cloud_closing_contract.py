"""Versioned output-type constraint only; no output repair or skill selection."""
from copy import deepcopy

CONTRACT = (
    '\n\nOutput serialization contract: Return one JSON object with exactly the keys '
    'composition, operations, and rationale. composition and rationale must be '
    'nonempty JSON strings. operations must be a JSON array whose items are only '
    'JSON strings containing existing operation identifiers from the supplied '
    'library. Never put an object, handle/parameters wrapper, or nested array in '
    'operations. A composition using the operation library requires exactly one '
    'such string; a composition without the operation library requires the empty '
    'array. Preserve the capability-selection rules above and use only supplied '
    'identifiers. Do not add any other top-level fields.'
)


def apply_contract(payload):
    result = deepcopy(payload)
    assert result['messages'][0]['role']=='system'
    assert isinstance(result['messages'][0]['content'],str)
    result['messages'][0]['content'] += CONTRACT
    recovered = deepcopy(result)
    recovered['messages'][0]['content'] = recovered['messages'][0]['content'][:-len(CONTRACT)]
    assert recovered == payload, 'Only the appended output-type contract may change'
    return result
