"""Deterministic O3 selection, independent of measurements and GT."""


def select(proximity, scan_context):
    selected, allocation, seen = [], [], set()

    def take(pairs, limit, source):
        added = 0
        for pair in pairs:
            key = tuple(sorted(pair))
            if key in seen:
                continue
            if added >= limit or len(selected) >= 12:
                break
            seen.add(key)
            selected.append(key)
            allocation.append(source)
            added += 1

    take(proximity, 6, 'proximity_quota')
    take(scan_context, 6, 'sc_quota')
    take(proximity, 12, 'proximity_backfill')
    take(scan_context, 12, 'sc_backfill')
    return selected, allocation


def check():
    p = [(i,i+100) for i in range(12)]
    s = [(i,i+200) for i in range(12)]
    assert select(p,s)[0] == p[:6]+s[:6]
    assert select(p,[])[0] == p
    assert select([],s)[0] == s
    assert select(p,p)[0] == p
    assert select([(5,1),(1,5)],[(1,5),(9,2)])[0] == [(1,5),(2,9)]
    assert select([],[]) == ([],[])
    return 6
