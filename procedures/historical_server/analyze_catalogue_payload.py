#!/usr/bin/env python3
"""Offline structural analysis of the current catalogue study's paired replay.

Usage: python3 analyze_catalogue_payload.py --suite /path/to/downloaded/suite
       python3 analyze_catalogue_payload.py --self-test

Uses only the standard library. Never imports experiment code, loads a model,
contacts a provider, reads credentials, or changes frozen evidence. Writes only
catalogue-payload-analysis.json and catalogue-payload-analysis.txt in --suite.
Byte/character measurements are structural proxies, never token or cost counts.
"""

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile


CONDITIONS = ('projected', 'unprojected')
CATALOGUE_FIELDS = ('available_compositions', 'operation_program')
OMITTED_NAMES = frozenset({
    'implementation', 'source', 'source_name', 'provenance', 'capability_id',
    'skill_name', 'configuration', 'evidence',
})
SIZE_NOTE = (
    'Byte and character sizes are structural proxies, not actual model tokens '
    'or cost. Per-field sizes use canonical UTF-8 JSON (sorted keys, no optional '
    'spaces, ensure_ascii=False). Raw user-context text sizes are also reported. '
    'Portable image references are not the full transmitted multimodal payload.'
)
TOKEN_NOTE = (
    'Provider prompt_tokens are observed separately from replay-summary.json, '
    'counted once per recorded transport attempt. Missing usage is unknown, '
    'not zero. Exact token savings cannot be attributed to a context field '
    'without new API ablations; no field token or cost estimates are made.'
)


class AnalysisError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise AnalysisError(message)


def read_json(path):
    try:
        def reject_constant(value):
            raise ValueError('Nonfinite JSON constant: ' + value)
        return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)
    except (OSError, ValueError) as error:
        raise AnalysisError(str(path) + ': ' + str(error)) from error


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def size_text(value):
    return dict(characters=len(value), utf8_bytes=len(value.encode('utf-8')))


def size_json(value):
    return size_text(canonical(value))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def official_projection(value):
    """Mirror only the frozen planner's small catalogue projection for auditing."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key in OMITTED_NAMES:
                continue
            if key == 'operation_memory':
                if isinstance(child, list):
                    result[key] = [{'operation_count': len(item.get('operation_ids', []))}
                                   for item in child if isinstance(item, dict)]
                elif child:
                    result[key] = {'available': True}
                continue
            result[key] = official_projection(child)
        return result
    if isinstance(value, list):
        return [official_projection(child) for child in value]
    return value


def normalize_request(path):
    body = read_json(path)
    require(isinstance(body, dict) and isinstance(body.get('messages'), list),
            path.name + ': request/messages must be objects/list')
    normalized = deepcopy(body)
    text_locations, image_hashes = [], []
    for message_index, message in enumerate(normalized['messages']):
        require(isinstance(message, dict), path.name + ': invalid message')
        content = message.get('content')
        if not isinstance(content, list):
            continue
        for part_index, part in enumerate(content):
            require(isinstance(part, dict), path.name + ': invalid content part')
            if message.get('role') == 'user' and part.get('type') == 'text':
                text_locations.append((message_index, part_index))
            if part.get('type') != 'image_url':
                continue
            reference = part.get('image_url')
            require(isinstance(reference, dict), path.name + ': invalid image reference')
            digest, artifact = reference.get('sha256'), reference.get('artifact')
            require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest),
                    path.name + ': missing/invalid image SHA256')
            require(isinstance(artifact, str) and artifact and not Path(artifact).is_absolute(),
                    path.name + ': expected relative image artifact')
            image_path = (path.parent / artifact).resolve()
            require(image_path.is_relative_to(path.parent.resolve()),
                    path.name + ': image reference escapes replay directory')
            require(image_path.is_file(), path.name + ': missing image artifact ' + artifact)
            require(sha256(image_path) == digest, path.name + ': image bytes do not match SHA256')
            # Ignore only arm-specific artifact names; retain all other image settings.
            part['image_url'] = {key: value for key, value in reference.items() if key != 'artifact'}
            image_hashes.append(digest)
    require(len(text_locations) == 1, path.name + ': expected one user context text part')
    message_index, part_index = text_locations[0]
    text_part = normalized['messages'][message_index]['content'][part_index]
    text = text_part.get('text')
    require(isinstance(text, str), path.name + ': context text is not a string')
    try:
        context = json.loads(text)
    except ValueError as error:
        raise AnalysisError(path.name + ': invalid context JSON') from error
    require(isinstance(context, dict), path.name + ': context must be an object')
    require(all(field in context for field in CATALOGUE_FIELDS),
            path.name + ': missing catalogue field')
    text_part['text'] = canonical({key: value for key, value in context.items()
                                  if key not in CATALOGUE_FIELDS})
    return dict(context=context, residual=normalized, image_sha256_in_order=image_hashes,
                raw_context_text_size=size_text(text), request_file_sha256=sha256(path))


def recursive_key_counts(value):
    counts = Counter()
    if isinstance(value, dict):
        counts.update(value.keys())
        for child in value.values():
            counts.update(recursive_key_counts(child))
    elif isinstance(value, list):
        for child in value:
            counts.update(recursive_key_counts(child))
    return counts


def pointer(parts):
    return '/' + '/'.join(str(part).replace('~', '~0').replace('/', '~1') for part in parts)


def operation_memory_nodes(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = path + (key,)
            if key == 'operation_memory':
                yield child_path, child
            yield from operation_memory_nodes(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from operation_memory_nodes(child, path + (index,))


def lookup(value, path):
    for key in path:
        value = value[key]
    return value


def shape(value):
    result = dict(type=type(value).__name__)
    if isinstance(value, list):
        result['items'] = len(value)
        result['item_key_sets'] = sorted({','.join(sorted(item)) for item in value if isinstance(item, dict)})
        result['operation_counts'] = [item['operation_count'] for item in value
                                      if isinstance(item, dict) and 'operation_count' in item]
    elif isinstance(value, dict):
        result['keys'] = sorted(value)
    return result


def compare_field(projected, unprojected):
    psize, usize = size_json(projected), size_json(unprojected)
    pcounts, ucounts = recursive_key_counts(projected), recursive_key_counts(unprojected)
    nodes = []
    for path, raw in operation_memory_nodes(unprojected):
        try:
            selected = lookup(projected, path)
        except (KeyError, IndexError, TypeError):
            selected = None
        nodes.append(dict(path=pointer(path), unprojected=shape(raw), projected=shape(selected),
                          changed=canonical(raw) != canonical(selected)))
    return dict(projected=psize, unprojected=usize,
                savings_unprojected_minus_projected={key: usize[key] - psize[key] for key in psize},
                omitted_metadata_key_occurrences={key: dict(unprojected=ucounts[key], projected=pcounts[key],
                    decrease=ucounts[key] - pcounts[key]) for key in sorted(OMITTED_NAMES)},
                operation_memory_shapes=nodes)


def provider_usage(replay, layouts):
    rows = replay.get('rows')
    require(replay.get('finished') is True and isinstance(rows, list), 'Replay summary is not finished')
    expected = {(layout, condition) for layout in layouts for condition in CONDITIONS}
    observed = [(row.get('layout'), row.get('condition')) for row in rows if isinstance(row, dict)]
    require(len(observed) == len(expected) and set(observed) == expected,
            'Replay summary does not contain exactly the declared layout/condition pairs')
    aggregates = {}
    for condition in CONDITIONS:
        subset = [row for row in rows if row['condition'] == condition]
        known, missing, attempts = [], 0, 0
        for row in subset:
            ledgers = row.get('attempts')
            require(isinstance(ledgers, list) and ledgers, 'Replay row lacks its transport-attempt ledger')
            for ledger in ledgers:
                require(isinstance(ledger, dict), 'Replay transport attempt is not an object')
                attempts += 1
                usage = ledger.get('usage')
                value = usage.get('prompt_tokens') if isinstance(usage, dict) else None
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    known.append(value)
                else:
                    missing += 1
        aggregates[condition] = dict(logical_calls=len(subset), transport_attempts=attempts,
            prompt_tokens_reported_sum=sum(known) if known else None,
            prompt_tokens_reported_attempts=len(known), prompt_tokens_missing_attempts=missing,
            prompt_tokens_usage_complete=missing == 0)
    return aggregates


def analyze_suite(suite):
    suite = Path(suite).resolve()
    protocol = read_json(suite / 'protocol.json')
    require(isinstance(protocol, dict) and protocol.get('schema') == 'physicalrsi.catalogue-ablation/v1',
            'Expected the current catalogue-ablation protocol, not another experiment suite')
    layouts = protocol.get('layouts')
    require(isinstance(layouts, list) and layouts and all(isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in layouts)
            and len(set(layouts)) == len(layouts), 'Protocol layouts must be distinct nonnegative integers')
    require(isinstance(protocol.get('conditions'), list)
            and len(protocol['conditions']) == len(CONDITIONS)
            and set(protocol['conditions']) == set(CONDITIONS), 'Unexpected protocol conditions')
    replay_path = suite / 'replay/replay-summary.json'
    replay = read_json(replay_path)
    require(isinstance(replay, dict), 'Replay summary must be an object')
    usage = provider_usage(replay, layouts)
    pairs = []
    for layout in layouts:
        inputs = {condition: normalize_request(suite / 'replay' / f'layout-{layout:02d}-{condition}-request.json')
                  for condition in CONDITIONS}
        p, u = inputs['projected'], inputs['unprojected']
        pc, uc = p['context'], u['context']
        require(set(pc) == set(uc), f'Layout {layout}: context field sets differ')
        if pairs:
            require(set(pc) == set(pairs[0]['top_level_context_fields']),
                    f'Layout {layout}: top-level context fields differ across layouts')
        changed = sorted(key for key in pc if canonical(pc[key]) != canonical(uc[key]))
        require(changed == sorted(CATALOGUE_FIELDS), f'Layout {layout}: changes are not exactly the two catalogue fields')
        # Serialized equality keeps JSON true/false distinct from Python 1/0.
        require(canonical(p['residual']) == canonical(u['residual']),
                f'Layout {layout}: settings/images/messages or noncatalogue context differ')
        for field in CATALOGUE_FIELDS:
            require(canonical(official_projection(uc[field])) == canonical(pc[field]),
                    f'Layout {layout}: {field} does not match official projection')
        require(isinstance(pc['available_compositions'], dict) and isinstance(uc['available_compositions'], dict),
                f'Layout {layout}: composition catalogues must be objects')
        composition_handles = sorted(uc['available_compositions'])
        require(composition_handles == sorted(pc['available_compositions']), f'Layout {layout}: composition handles differ')
        for handle in composition_handles:
            require(canonical(pc['available_compositions'][handle].get('steps')) == canonical(uc['available_compositions'][handle].get('steps')),
                    f'Layout {layout}: executable composition steps differ')
        operations_p = pc['operation_program'].get('operations')
        operations_u = uc['operation_program'].get('operations')
        require(isinstance(operations_p, dict) and isinstance(operations_u, dict), f'Layout {layout}: operation registry missing')
        operation_handles = sorted(operations_u)
        require(operation_handles == sorted(operations_p), f'Layout {layout}: operation handles differ')
        fields = {field: compare_field(pc[field], uc[field]) for field in pc}
        for condition, context in [('projected', pc), ('unprojected', uc)]:
            # Each member includes its JSON key and colon; only commas/braces remain.
            for field, value in context.items():
                fields[field][condition + '_member'] = size_text(canonical({field: value})[1:-1])
            for metric in ('characters', 'utf8_bytes'):
                require(sum(fields[field][condition + '_member'][metric] for field in context)
                        + max(len(context) - 1, 0) + 2 == size_json(context)[metric], 'Internal size accounting failed')
        pairs.append(dict(layout=layout, integrity_verified=True, changed_context_fields=changed,
            official_projection_verified=True, image_sha256_in_order=p['image_sha256_in_order'],
            request_files={condition: dict(path=f'replay/layout-{layout:02d}-{condition}-request.json',
                sha256=inputs[condition]['request_file_sha256']) for condition in CONDITIONS},
            raw_context_text_size={condition: inputs[condition]['raw_context_text_size'] for condition in CONDITIONS},
            canonical_context_size={condition: size_json(inputs[condition]['context']) for condition in CONDITIONS},
            top_level_context_fields=fields, composition_handles_equal=True,
            composition_count=len(composition_handles), composition_handles=composition_handles,
            operation_handles_equal=True, operation_count=len(operation_handles), operation_handles=operation_handles))
    totals = {}
    for field in pairs[0]['top_level_context_fields']:
        totals[field] = {condition: {metric: sum(pair['top_level_context_fields'][field][condition][metric] for pair in pairs)
                                    for metric in ('characters', 'utf8_bytes')} for condition in CONDITIONS}
        totals[field]['savings_unprojected_minus_projected'] = {
            metric: totals[field]['unprojected'][metric] - totals[field]['projected'][metric]
            for metric in ('characters', 'utf8_bytes')}
    report = dict(schema='physicalrsi.catalogue-payload-analysis/v1', created_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha256(suite / 'protocol.json'), model=protocol.get('model'), layouts=layouts,
        pair_integrity_verified=True, size_measurement_note=SIZE_NOTE,
        metadata_count_note='Recursive key occurrence differences include descendants of omitted parent subtrees; they are not disjoint byte or token attribution.',
        operation_memory_note='Projected zero operation_count values for stage-program catalogues are existing official projection behavior, not an estimate of executable stage count.',
        aggregate_top_level_context_fields=totals, pairs=pairs,
        provider_observed_prompt_tokens=dict(source='replay/replay-summary.json', source_sha256=sha256(replay_path),
            note=TOKEN_NOTE, conditions=usage))
    catalogue_savings = {field: totals[field]['savings_unprojected_minus_projected']['utf8_bytes'] for field in CATALOGUE_FIELDS}
    text = '\n'.join([
        f'Verified {len(pairs)} replay pairs: only available_compositions and operation_program differ; settings, other context, image content SHA values, and candidate handles match.',
        'All projected catalogues exactly match the frozen official projection of their unprojected counterpart.',
        'Structural canonical UTF-8 JSON reductions across the replay pairs: ' + ', '.join(f'{field} {value:,} bytes' for field, value in catalogue_savings.items()) + '.',
        'Reductions come from omitted implementation/source/provenance/identity/evidence metadata and replacement of detailed operation memory with count summaries. Static task-name cues and executable stages are part of this bundled treatment.',
        SIZE_NOTE,
        'Observed provider prompt_tokens across all recorded transport attempts: ' + '; '.join(
            f"{condition}={usage[condition]['prompt_tokens_reported_sum']} ({usage[condition]['prompt_tokens_missing_attempts']} attempts missing usage)" for condition in CONDITIONS) + '.',
        'Provider evidence: replay/replay-summary.json. ' + TOKEN_NOTE,
    ]) + '\n'
    return report, text


def write_outputs(suite, report, text):
    for name, content in [('catalogue-payload-analysis.json', json.dumps(report, indent=2, ensure_ascii=False) + '\n'),
                          ('catalogue-payload-analysis.txt', text)]:
        target = Path(suite) / name
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(target)


def self_test():
    with tempfile.TemporaryDirectory(prefix='catalogue-payload-fixture-') as directory:
        suite = Path(directory)
        replay = suite / 'replay'
        replay.mkdir()
        (suite / 'protocol.json').write_text(json.dumps(dict(schema='physicalrsi.catalogue-ablation/v1',
            layouts=[1, 2], conditions=list(CONDITIONS), model='qwen3.7-plus')))
        full = dict(available_compositions={'learned': dict(steps=['memory.snapshot', 'pi05'],
            implementation={'module': 'static.identity'}, evidence={'path': 'source.py'})},
            operation_program={'operations': {'pickup': dict(description='Lift 绿色 scissors',
                skill_name='general-pickup', operation_memory=[{'memory_revision': 'revision', 'programs': {'act': {'steps': [1, 2]}}}],
                capability_memory={'operation_memory': [{'operation_ids': ['a', 'b'], 'source': {'path': 'memory.json'}}]})}})
        bodies = {}
        for layout in (1, 2):
            for condition in CONDITIONS:
                context = dict(instruction='Lift 绿色 scissors', observation={'camera': 0}, memory={}, previous_plan=None,
                               **(official_projection(full) if condition == 'projected' else deepcopy(full)))
                parts = [{'type': 'text', 'text': json.dumps(context, ensure_ascii=False)}]
                for index, data in enumerate((b'fixture image one', b'fixture image two')):
                    name = f'{condition}-{index}.png'
                    (replay / name).write_bytes(data)
                    parts.append({'type': 'image_url', 'image_url': {'artifact': name, 'sha256': hashlib.sha256(data).hexdigest()}})
                body = dict(model='qwen3.7-plus', enable_thinking=True, temperature=0,
                    response_format={'type': 'json_object'}, messages=[{'role': 'system', 'content': 'Frozen prompt'}, {'role': 'user', 'content': parts}])
                path = replay / f'layout-{layout:02d}-{condition}-request.json'
                path.write_text(json.dumps(body, ensure_ascii=False))
                bodies[path] = body
        rows = [dict(layout=1, condition='projected', usage={'prompt_tokens': 999}, attempts=[{'usage': {'prompt_tokens': 10}}, {'usage': {'prompt_tokens': 12}}]),
                dict(layout=2, condition='projected', attempts=[{'usage': {'prompt_tokens': 13}}]),
                dict(layout=1, condition='unprojected', attempts=[{'usage': {'prompt_tokens': 20}}]),
                dict(layout=2, condition='unprojected', attempts=[{'error': 'missing usage'}])]
        (replay / 'replay-summary.json').write_text(json.dumps(dict(finished=True, rows=rows)))
        report, text = analyze_suite(suite)
        assert report['pair_integrity_verified']
        assert report['provider_observed_prompt_tokens']['conditions']['projected']['prompt_tokens_reported_sum'] == 35
        assert report['provider_observed_prompt_tokens']['conditions']['unprojected']['prompt_tokens_missing_attempts'] == 1
        instruction_size = report['pairs'][0]['top_level_context_fields']['instruction']['projected']
        assert instruction_size['utf8_bytes'] > instruction_size['characters']
        assert report['pairs'][0]['top_level_context_fields']['operation_program']['operation_memory_shapes'][0]['projected']['operation_counts'] == [0]
        assert 'not actual model tokens' in text and 'without new API ablations' in text
        write_outputs(suite, report, text)
        assert read_json(suite / 'catalogue-payload-analysis.json')['pair_integrity_verified']
        target = replay / 'layout-01-unprojected-request.json'
        original = bodies[target]
        cases = []
        def change_context(body, mutate):
            context = json.loads(body['messages'][1]['content'][0]['text'])
            mutate(context)
            body['messages'][1]['content'][0]['text'] = json.dumps(context)
        cases.append(lambda b: b.update(temperature=1))
        cases.append(lambda b: b.update(temperature=False))
        cases.append(lambda b: b.update(enable_thinking=1))
        cases.append(lambda b: b['messages'][0].update(content='Changed system prompt'))
        cases.append(lambda b: change_context(b, lambda c: c.update(instruction='Other instruction')))
        cases.append(lambda b: change_context(b, lambda c: c['observation'].update(camera=False)))
        cases.append(lambda b: change_context(b, lambda c: c.update(extra='new field')))
        cases.append(lambda b: change_context(b, lambda c: c['operation_program']['operations'].update(extra={})))
        cases.append(lambda b: change_context(b, lambda c: c['available_compositions']['learned'].update(steps=['different'])))
        cases.append(lambda b: b['messages'][1]['content'].reverse())
        cases.append(lambda b: b['messages'][1]['content'][1]['image_url'].update(sha256='0' * 64))
        for mutate in cases:
            changed = deepcopy(original)
            mutate(changed)
            target.write_text(json.dumps(changed))
            try:
                analyze_suite(suite)
            except AnalysisError:
                pass
            else:
                raise AssertionError('Fixture mutation was not rejected')
            target.write_text(json.dumps(original, ensure_ascii=False))
        image = replay / 'unprojected-0.png'
        image.write_bytes(b'corrupt image')
        try:
            analyze_suite(suite)
        except AnalysisError:
            pass
        else:
            raise AssertionError('Corrupt image was not rejected')
    print('SELF_TEST_OK: valid renamed-image pair, Unicode sizes, projection shapes, retry usage, output files, and 12 integrity rejection fixtures')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--suite', type=Path)
    group.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        else:
            report, text = analyze_suite(args.suite)
            write_outputs(args.suite, report, text)
            print(text, end='')
            print('Wrote', args.suite.resolve() / 'catalogue-payload-analysis.json')
            print('Wrote', args.suite.resolve() / 'catalogue-payload-analysis.txt')
    except (AnalysisError, OSError, ValueError) as error:
        print('Payload analysis refused: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
