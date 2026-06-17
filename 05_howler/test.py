#!/usr/bin/env python3
"""tests for howler.py"""

import os
import re
import random
import runpy
import string
from subprocess import getstatusoutput, getoutput
import sys
import pytest
import howler

# pylint: disable=redefined-outer-name
@pytest.fixture(scope="session")
def prg():
    """Program path that works on both Unix-like shells and Windows cmd."""
    if os.name == 'nt':
        prg = f'"{sys.executable}" ".\\howler.py"'
    else:
        prg = f'{sys.executable} ./howler.py'
    return prg


# --------------------------------------------------
def random_string():
    """generate a random string"""

    k = random.randint(5, 10)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k))


# --------------------------------------------------
def out_flag():
    """Either -o or --outfile"""

    return '-o' if random.randint(0, 1) else '--outfile'


# --------------------------------------------------
def test_exists():
    """exists"""

    assert os.path.isfile('./howler.py')


# --------------------------------------------------
def test_usage(prg):
    """usage"""

    for flag in ['-h', '--help']:
        rv, out = getstatusoutput(f'{prg} {flag}')
        assert rv == 0
        assert re.match("usage", out, re.IGNORECASE)


# --------------------------------------------------
def test_text_stdout(prg):
    """Test STDIN/STDOUT"""

    out = getoutput(f'{prg} "foo bar baz"')
    assert out.strip() == 'FOO BAR BAZ'


# --------------------------------------------------
def test_text_outfile(prg):
    """Test STDIN/outfile"""

    out_file = random_string()
    if os.path.isfile(out_file):
        os.remove(out_file)

    try:
        out = getoutput(f'{prg} {out_flag()} {out_file} "foo bar baz"')
        assert out.strip() == ''
        assert os.path.isfile(out_file)
        text = open(out_file, encoding='utf-8').read().rstrip()
        assert text == 'FOO BAR BAZ'
    finally:
        if os.path.isfile(out_file):
            os.remove(out_file)


# --------------------------------------------------
def test_file(prg):
    """Test file in/out"""

    for expected_file in os.listdir('test-outs'):
        try:
            out_file = random_string()
            if os.path.isfile(out_file):
                os.remove(out_file)

            basename = os.path.basename(expected_file)
            in_file = os.path.join('../inputs', basename)
            out = getoutput(f'{prg} {out_flag()} {out_file} {in_file}')
            assert out.strip() == ''
            produced = open(out_file, encoding='utf-8').read().rstrip()
            expected = open(os.path.join('test-outs', expected_file), encoding='utf-8').read().strip() #pylint: disable=line-too-long
            assert expected == produced
        finally:
            if os.path.isfile(out_file):
                os.remove(out_file)

# --------------------------------------------------
def test_no_args(prg):
    """No args should fail with usage/error output."""

    rv, out = getstatusoutput(f'{prg}')
    assert rv != 0
    assert re.search('usage|error', out, re.IGNORECASE)

# --------------------------------------------------
def test_bad_flag(prg):
    """Unknown flag should fail."""

    rv, out = getstatusoutput(f'{prg} --definitely-not-a-real-flag')
    assert rv != 0
    assert re.search('unrecognized|error', out, re.IGNORECASE)

# --------------------------------------------------
def test_missing_file_is_literal_text(prg):
    """Nonexistent file path should be treated as literal text."""

    fake_name = f'no_such_file_{random_string()}.txt'
    assert not os.path.isfile(fake_name)
    out = getoutput(f'{prg} {fake_name}')
    assert out.strip() == fake_name.upper()

# --------------------------------------------------
def test_empty_text(prg):
    """Empty input should still be valid and produce only newline."""

    out = getoutput(f'{prg} ""')
    assert out.strip() == ''

# --------------------------------------------------
def test_unicode_text(prg):
    """Unicode input should uppercase correctly."""

    out = getoutput(f'{prg} "naïve café"')
    assert out.strip() == 'NAÏVE CAFÉ'

# --------------------------------------------------
def test_outfile_overwrite(prg):
    """Existing outfile should be overwritten, not appended."""

    out_file = random_string()
    try:
        with open(out_file, 'wt', encoding='utf-8') as fh:
            fh.write('old content\n')

        out = getoutput(f'{prg} {out_flag()} {out_file} "new text"')
        assert out.strip() == ''

        text = open(out_file, encoding='utf-8').read().rstrip()
        assert text == 'NEW TEXT'
    finally:
        if os.path.isfile(out_file):
            os.remove(out_file)

# --------------------------------------------------
def test_get_args_text(monkeypatch):
    """Directly test parsing literal text input."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', 'foo bar baz'])
    args = howler.get_args()
    assert args.text == 'foo bar baz'
    assert args.outfile == ''

# --------------------------------------------------
def test_get_args_file_input(monkeypatch, tmp_path):
    """Directly test that get_args() detects a file path and returns its contents."""

    in_file = tmp_path / 'input.txt'
    in_file.write_text('foo bar baz\n', encoding='utf-8')

    monkeypatch.setattr(sys, 'argv', ['howler.py', str(in_file)])
    args = howler.get_args()
    assert args.text == 'foo bar baz'
    assert args.outfile == ''

# --------------------------------------------------
def test_get_args_help(monkeypatch, capsys):
    """Verify that -h exits with code 0 and prints usage."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', '-h'])

    with pytest.raises(SystemExit) as err:
        howler.get_args()

    captured = capsys.readouterr()
    assert err.value.code == 0
    assert re.match('usage', captured.out, re.IGNORECASE)

# --------------------------------------------------
def test_get_args_no_args(monkeypatch, capsys):
    """Directly test missing required arg handling."""

    monkeypatch.setattr(sys, 'argv', ['howler.py'])

    with pytest.raises(SystemExit) as err:
        howler.get_args()

    captured = capsys.readouterr()
    assert err.value.code != 0
    assert re.search('usage|error', captured.err, re.IGNORECASE)

# --------------------------------------------------
def test_get_args_bad_flag(monkeypatch, capsys):
    """Directly test bad option handling."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', '--bogus'])

    with pytest.raises(SystemExit) as err:
        howler.get_args()

    captured = capsys.readouterr()
    assert err.value.code != 0
    assert re.search('unrecognized|error', captured.err, re.IGNORECASE)

# --------------------------------------------------
def test_main_stdout(monkeypatch, capsys):
    """Verify that main() uppercases text and writes it to stdout."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', 'foo bar baz'])
    howler.main()

    captured = capsys.readouterr()
    assert captured.out == 'FOO BAR BAZ\n'

# --------------------------------------------------
def test_main_outfile(monkeypatch, tmp_path, capsys):
    """Verify that main() uppercases text and writes it to a file when -o is specified."""

    out_file = tmp_path / 'out.txt'

    monkeypatch.setattr(sys, 'argv', ['howler.py', '-o', str(out_file), 'foo bar baz'])
    howler.main()

    captured = capsys.readouterr()
    assert captured.out == ''
    assert out_file.read_text(encoding='utf-8') == 'FOO BAR BAZ\n'

# --------------------------------------------------
def test_main_empty_text(monkeypatch, capsys):
    """Verify that main() outputs a single newline for empty input."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', ''])
    howler.main()

    captured = capsys.readouterr()
    assert captured.out == '\n'

# --------------------------------------------------
def test_main_unicode(monkeypatch, capsys):
    """Verify that main() correctly uppercases unicode characters."""

    monkeypatch.setattr(sys, 'argv', ['howler.py', 'naïve café'])
    howler.main()

    captured = capsys.readouterr()
    assert captured.out == 'NAÏVE CAFÉ\n'

# --------------------------------------------------
def test_run_as_main(monkeypatch, capsys):
    """Execute the script through the __main__ guard."""

    script = os.path.join(os.path.dirname(__file__), 'howler.py')
    monkeypatch.setattr(sys, 'argv', ['howler.py', 'foo'])
    runpy.run_path(script, run_name='__main__')

    captured = capsys.readouterr()
    assert captured.out == 'FOO\n'
