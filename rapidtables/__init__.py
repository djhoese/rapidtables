__author__ = "Altertech"
__license__ = "MIT"
__version__ = '0.0.34'

OUTPUT_RAW = 0
OUTPUT_GENERATOR = 1
OUTPUT_GENERATOR_TUPLES = 2

_TABLEFMT_SIMPLE = 1
_TABLEFMT_MD = 2
_TABLEFMT_RST = 3


def guess_widths(keys, headers, row_data, generate_header):
    """Determine best width for each column."""
    key_lengths = ()
    for ki, k in enumerate(keys):
        klen = 0
        for ri, r in enumerate(row_data):
            value = r.get(k)
            if value is not None:
                klen = max(klen, len(str(value)))
        if generate_header:
            hklen = len(headers[ki]) if headers else len(k)
            key_lengths += (max(hklen, klen),)
        else:
            key_lengths += (klen,)
    return key_lengths


def format_table(table,
                 fmt=0,
                 headers=None,
                 separator='  ',
                 align=1,
                 generate_header=True,
                 body_sep=None,
                 body_sep_fill='  ',
                 column_width=None):
    """Format list of dicts to table.

    If headers are not specified, dict keys MUST be strings

    Args:
        table: list or tuple of dicts
        fmt: 0 - raw (default), 1 - generator of strings, 2 - generator of
            tuples
        headers: list or tuple of headers (default: dict keys)
        separator: cell separator (default: "  ")
        align: 0 - no align, 1 - align decimals to right (default)
        generate_header: True (default) - create and return header
        body_sep: char to use as body separator (default: None)
        body_sep_fill: string used to fill body separator to next col
        column_width: list or tuple of integers or integer or True or None
            If `None` (default), read the entire table to find the best
            width for each column. If `True` use the first row of data to
            guess at good column widths. If a single integer, all columns
            will be the same width. Otherwise, use the specified widths for
            each column.

    Returns:
        body if generate_header is False and body_sep is None
        (header, body) if generate_header is True and body_sep is None
        (header, body sep., body) if generate_header is True and body_sep is
                                    not None

        if fmt is set to 1 or 2, body is returned as generator of strings or
        generator of tuples

    """
    calign = align == 0
    if not table:
        return
    if column_width is None:
        table = list(table)
        first_row = table[0]
        columns_to_use = table
        table = table[1:]
    else:
        # most performant way to deal with the table
        table = iter(table)
        # use first row to guess as parts of formatting
        first_row = next(table)
        columns_to_use = [first_row]

    keys = tuple(first_row)
    len_keys = len(keys)
    lkr = range(len_keys)
    len_keysn = len_keys - 1
    if not headers:
        headers = keys
    if not calign:
        key_isalpha = ()
    need_body_sep = body_sep is not None
    if fmt == OUTPUT_RAW:
        result = ''

    if isinstance(column_width, (int, float)):
        key_lengths = (column_width,) * len_keys
    elif isinstance(column_width, (tuple, list)):
        key_lengths = column_width
    else:
        # need to determine widths
        key_lengths = guess_widths(keys, headers, columns_to_use, generate_header)

    # figure out alphas
    for ki, k in enumerate(keys):
        alpha = False
        value = first_row.get(k)
        if value is not None:
            if not (calign and alpha):
                try:
                    float(value)
                except (TypeError, ValueError):
                    alpha = True
        if not calign:
            key_isalpha += (alpha,)

    # output
    # add header
    if generate_header:
        if fmt == OUTPUT_RAW or fmt == OUTPUT_GENERATOR:
            header = ''
            if need_body_sep:
                bsep = ''
            for i, ht, key_len in zip(lkr, headers, key_lengths):
                if need_body_sep:
                    if i < len_keysn:
                        bsep += body_sep * key_len + body_sep_fill
                    else:
                        bsep += body_sep * key_len
                if calign or key_isalpha[i]:
                    if i < len_keysn:
                        header += ht.ljust(key_len) + separator
                    else:
                        header += ht.ljust(key_len)
                else:
                    if i < len_keysn:
                        header += ht.rjust(key_len) + separator
                    else:
                        header += ht.rjust(key_len)
        else:
            header = ()
            if need_body_sep:
                bsep = ()
            for i, ht, key_len, key_alpha in zip(lkr, headers, key_lengths, key_isalpha):
                if need_body_sep:
                    bsep += ('-' * key_len,)
                if calign or key_alpha:
                    header += (ht.ljust(key_len),)
                else:
                    header += (ht.rjust(key_len),)

    def body_generator():
        for v in table:
            if fmt == OUTPUT_GENERATOR_TUPLES:
                row = ()
            else:
                row = ''
            for i, k in enumerate(keys):
                val = v.get(k)
                if val is not None:
                    if calign or key_isalpha[i]:
                        r = str(val).ljust(key_lengths[i])
                    else:
                        r = str(val).rjust(key_lengths[i])
                else:
                    r = ' ' * key_lengths[i]
                if fmt == OUTPUT_GENERATOR_TUPLES:
                    row += (r,)
                # OUTPUT_GENERATOR
                elif i < len_keysn:
                    row += r + separator
                else:
                    row += r
            yield row

    # add body
    if fmt == OUTPUT_RAW:
        result += '\n'.join(body_generator())
    else:
        result = body_generator()
    if generate_header and body_sep:
        return (header, bsep, result)
    elif generate_header:
        return (header, result)
    else:
        return result


def make_table(table, tablefmt='simple', headers=None, align=1):
    '''
    Generates ready-to-output table

    If headers are not specified, dict keys MUST be strings

    Args:
        table: list or tuple of dicts
        tablefmt: raw, simple (default), md (markdown) or rst (reStructuredText)
        headers: list or tuple of headers (default: dict keys)
        align: 0 - no align, 1 - align decimals to right (default)
    '''
    if tablefmt == 'raw':
        t = format_table(table, fmt=1, headers=headers, align=align)
        return t[0] + '\n' + len(t[0]) * '-' + '\n' + '\n'.join(t[1])
    else:
        if tablefmt == 'simple':
            body_sep = '-'
            separator = '  '
            body_sep_fill = '  '
            tfmt = _TABLEFMT_SIMPLE
        elif tablefmt == 'md':
            body_sep = '-'
            separator = ' | '
            body_sep_fill = '-|-'
            tfmt = _TABLEFMT_MD
        elif tablefmt == 'rst':
            body_sep = '='
            separator = '  '
            body_sep_fill = '  '
            tfmt = _TABLEFMT_RST
        else:
            raise RuntimeError('table format not supported')
        t = format_table(table,
                         fmt=1,
                         headers=headers,
                         align=align,
                         separator=separator,
                         body_sep_fill=body_sep_fill,
                         body_sep=body_sep)
        if tfmt == _TABLEFMT_MD:
            h = '|-' + t[1] + '-|\n| '
            return '| ' + t[0] + ' |\n' + h + ' |\n| '.join(t[2]) + ' |'
        elif tfmt == _TABLEFMT_RST:
            return t[1] + '\n' + t[0] + '\n' + t[1] + '\n' + '\n'.join(
                t[2]) + '\n' + t[1]
        if tfmt == _TABLEFMT_SIMPLE:
            return t[0] + '\n' + t[1] + '\n' + '\n'.join(t[2])


def print_table(table, tablefmt='simple', headers=None, align=1):
    '''
    Same as make_table but prints results to stdout
    '''
    print(make_table(table, tablefmt=tablefmt, headers=headers, align=align))
