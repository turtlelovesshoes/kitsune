#!/usr/bin/env python

import itertools
import optparse
import re
import sys

try:
    import polib  # from http://bitbucket.org/izi/polib
except ImportError:
    print 'You need to install polib.  Do:'
    print ''
    print '   pip install polib'
    sys.exit()


USAGE = 'usage: %prog FILENAME'


INTERP_RE = re.compile(
    r'('
    r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxXeEfFgGcrs%])'
    r'|'
    r'(?:\{\S+?\})'
    r')')


def extract_tokens(msg):
    try:
        tokens = [token for token in INTERP_RE.findall(msg)]
        tokens.sort()
        return tuple(tokens)
    except TypeError:
        print 'TYPEERROR', repr(msg)


def equal(id_tokens, str_tokens):
    if str_tokens is None:
        # This means they haven't translated the msgid, so there's
        # no entry. I'm pretty sure this only applies to plurals.
        return True

    id_tokens = list(id_tokens)
    str_tokens = list(str_tokens)

    for id_token, str_token in itertools.izip_longest(
        id_tokens, str_tokens, fillvalue=None):
        if id_token is None or str_token is None:
            return False
        if id_token != str_token:
            return False
    return True


def verify(msgid, id_text, id_tokens, str_text, str_tokens, index):
    # If the token lists aren't equal and there's a msgstr, then that's
    # a problem. If there's no msgstr, it means it hasn't been translated.
    if not equal(id_tokens, str_tokens) and str_text.strip():
        print ('\nError for msgid: {msgid}\n'
               'tokens: {id_tokens} VS. {str_tokens}\n'
               '{key}: {id_text}\n'
               'msgstr{index}: {str_text}'.format(
            index='[{index}]'.format(index=index) if index is not None else '',
            key='id' if index in (None, '0') else 'plural',
            msgid=msgid,
            id_text=id_text,
            id_tokens=', '.join(id_tokens),
            str_text=str_text.encode('ascii', 'replace'),
            str_tokens=', '.join(str_tokens)))

        return False

    return True


def verify_file(fname):
    po = polib.pofile(fname)

    count = 0
    bad_count = 0
    for entry in po:
        if not entry.msgid_plural:
            if not entry.msgid and entry.msgstr:
                continue
            id_tokens = extract_tokens(entry.msgid)
            str_tokens = extract_tokens(entry.msgstr)
            if not verify(entry.msgid, entry.msgid, id_tokens, entry.msgstr,
                          str_tokens, None):
                bad_count += 1

        else:
            for key in sorted(entry.msgstr_plural.keys()):
                if key == '0':
                    # This is the 1 case.
                    text = entry.msgid
                else:
                    text = entry.msgid_plural
                id_tokens = extract_tokens(text)

                str_tokens = extract_tokens(entry.msgstr_plural[key])
                if not verify(entry.msgid, text, id_tokens,
                              entry.msgstr_plural[key], str_tokens, key):
                    bad_count += 1

        count += 1

    print ('\nVerified {count} messages in {fname}. '
           '{badcount} possible errors.'.format(
            count=count, fname=fname, badcount=bad_count))


if __name__ == '__main__':
    parser = optparse.OptionParser(usage=USAGE)
    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    verify_file(args[0])
