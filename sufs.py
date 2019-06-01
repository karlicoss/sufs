#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os
from os.path import lexists
from typing import List, Dict
from subprocess import check_call


def run(from_: List[Path], to: Path):
    assert len(from_) > 0
    assert to.is_dir() and not to.is_symlink()

    # TODO maybe, have init method??
    existing = list(to.iterdir())

    for p in existing:
        assert p.is_symlink()

    # TODO not sure about is_dir here
    sets = [set(x for x in p.iterdir() if x.is_dir()) for p in from_]

    spec: Dict[str, Path] = {}
    errors = False
    for s in sets:
        for src in s:
            name = src.name
            if name in spec:
                print(f"Clashing path: {spec[name]}, {src}", file=sys.stderr)
                errors = True
            else:
                spec[name] = src
    assert not errors, 'Clashing names detected!'

    # check_call(['stat', str(to)])
    # assert not os.access(str(to), os.W_OK)
    # ugh. no nice method in python to remove permission...
    check_call(['chmod', 'u+w', str(to)])
    try:
        # remove old broken links which point to from_
        for p in existing:
            if p.exists():
                continue

            points_to = Path(os.readlink(p))
            for src in from_:
                try:
                    points_to.relative_to(src)
                    print(f'unlinking broken link {p}', file=sys.stderr)
                    p.unlink()
                    break
                except ValueError:
                    continue


        # link new stuff
        for name, src in spec.items():
            old = to / name
            if lexists(old):
                old_src = Path(os.readlink(old))
                if old_src == src:
                    print(f"skipping {old}, no need to update", file=sys.stderr)
                    continue
                else:
                    old.unlink()
            print(f"linking  {old} -> {src}", file=sys.stderr)
            old.symlink_to(src)
    finally:
        check_call(['chmod', 'ugo-w', str(to)])



def main():
    p = argparse.ArgumentParser()
    p.add_argument('--to', type=Path, required=True)
    p.add_argument('sources', type=Path, nargs='+')
    # TODO inotify and run as systemd service?
    # TODO what to do with broken symliks?
    # TODO assert no regular files
    args = p.parse_args()
    run(from_=args.sources, to=args.to)


def test(tmp_path):
    import pytest # type: ignore

    tdir = Path(tmp_path)
    c1 = tdir / 'c1'
    aaa1 = c1 / 'aaa'
    bbb  = c1 / 'bbb'
    c2 = tdir / 'c2'
    aaa2 = c2 / 'aaa'
    ccc  = c2 / 'ccc'
    c3 = tdir / 'c3'
    zzz  = c3 / 'zzz'

    for d in [aaa1, bbb, aaa2, ccc, zzz]:
        d.mkdir(exist_ok=True, parents=True)

    fff = c1 / 'file'
    fff.touch()

    merged = tdir / 'merged'

    with pytest.raises(Exception): # due to nonexistent dir
        run(from_=[c1, c2], to=merged)
    merged.mkdir(parents=True)



    run(from_=[c1], to=merged)
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb'}


    # should set proper permissions after
    with pytest.raises(PermissionError):
        (merged / 'alalala').touch()

    run(from_=[c1, c3], to=merged)
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb', merged / 'zzz'}

    zzz.rmdir()
    run(from_=[c1], to=merged)
    # zzz link stays regardless being deleted because it didn't point to any of source directories
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb', merged / 'zzz'}

    run(from_=[c1, c3], to=merged)
    # zzz goes now because in points to c3 which is managed
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb'}

    with pytest.raises(Exception): # due to duplicate file 'aaa'
        run(from_=[c1, c2], to=merged)

    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb'} # shouldn't change anything
    # TODO marker file?

    aaa1.rmdir()
    run(from_=[c1, c2], to=merged)
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb', merged / 'ccc'}

    run(from_=[c1, c2], to=merged)
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb', merged / 'ccc'}

    eee = c1 / 'eee'
    eee.mkdir()

    run(from_=[c1, c2], to=merged)
    assert set(merged.iterdir()) == {merged / 'aaa', merged / 'bbb', merged / 'ccc', merged / 'eee'}



if __name__ == '__main__':
    # TODO assert all exist first?
    # TODO ok link and error? not sure..
    main()
