"""Offline reanalysis. Input: directory containing the 19 t97..t103 result JSONL files.
No network, credential access, detector invocation or invented model labels.
Usage: python audit_saved_contexts.py /path/to/snapshot/result-files
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import re


def tokens(text):
    return re.findall(r"[\w]+(?:['’][\w]+)?", text.lower())


def ngrams(words, n):
    return {tuple(words[i:i+n]) for i in range(len(words)-n+1)}


def main(root):
    records = {}
    names = {}
    files = sorted(root.rglob('API-RESULTS*.jsonl'))
    for path in files:
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            text = ''.join(w[-1] for w in row['windows'])
            assert hashlib.sha256(text.encode()).hexdigest() == row['sha256'], row['name']
            assert row['version'] == '4.1'
            cursor = 0
            for window in row['windows']:
                assert window[3] == cursor
                assert text[window[3]:window[4]] == window[-1]
                cursor = window[4]
            assert cursor == len(text)
            row['text'] = text
            records[row['sha256']] = row
            names[row['name']] = row
    pairs = []
    for target in records.values():
        text = target['text']
        if '\n' in text or not 30 <= len(text.split()) <= 200:
            continue
        for context in records.values():
            full = context['text']
            if context['sha256'] == target['sha256'] or full.count(text) != 1:
                continue
            start = full.index(text)
            end = start + len(text)
            if (start and full[start-1] != '\n') or (end < len(full) and full[end] != '\n'):
                continue
            old_human = all(w[0] == 'Human Written' for w in target['windows'])
            new_human = all(w[0] == 'Human Written' for w in context['windows'] if w[3] < end and w[4] > start)
            row = {'target': target['name'], 'context': context['name'],
                   'standalone_human': old_human, 'in_context_human': new_human}
            for n in (3, 4, 5):
                outside = ngrams(tokens(full[:start]), n) | ngrams(tokens(full[end:]), n)
                row[f'shared_{n}grams'] = sorted(' '.join(x) for x in ngrams(tokens(text), n) & outside)
            pairs.append(row)
    summary = []
    for n in (3, 4, 5):
        for present in (False, True):
            group = [r for r in pairs if r['standalone_human'] and bool(r[f'shared_{n}grams']) == present]
            summary.append({'n': n, 'shared_phrase_present': present, 'placements': len(group),
                            'new_nonhuman': sum(not r['in_context_human'] for r in group)})
    contrasts = [
        ('t101_borrow_h3', 't101b_borrow_h3',
         'The thank-you you weren’t waiting for might not come anyway.',
         'Your little one might not take it well at first.'),
        ('t103d_ig_belonging_s05', 't103f_ig_belonging_s06',
         'toward a belonging deeper than any group, one that',
         'toward somewhere you belong that'),
        ('t99_bb_stretch', 't100_bb_stretch',
         'I’d still take real suffering seriously, and do what you owe the people around you, but skip the part where you have to be miserable too.',
         'Do your part for people who are suffering, and skip the part where you have to be miserable too.')]
    checked = []
    for old, new, before, after in contrasts:
        a, b = names[old]['text'], names[new]['text']
        assert a.count(before) == 1 and a.replace(before, after) == b
        checked.append({'old': old, 'new': new, 'before': before, 'after': after,
                        'old_words': len(a.split()), 'new_words': len(b.split()),
                        'only_named_replacement': True})
    assert len(files) == 19 and len(records) == 102 and len(pairs) == 38
    print(json.dumps({'source_commit': 'dc929e66beb4b06cbc8b80d5be7eec7cd967c89f',
                      'files': len(files), 'unique_inputs': len(records), 'placements': len(pairs),
                      'summary': summary, 'contrasts': checked, 'rows': pairs,
                      'new_api_calls': 0,
                      'limitations': 'Retrospective dependent production sample. Lexical recurrence is not prosody or a causal classifier.'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    main(parser.parse_args().root)
