"""
=======
cs_tag
=======

Parse SAM entries with ``cs`` short tag from ``minimap2`` output.

See here for details on short ``cs`` tag format:
https://lh3.github.io/minimap2/minimap2.html

"""


import regex


_CS_OPS = {
    'identity': ':[0-9]+',
    'substitution': r'\*[acgtn][acgtn]',
    'insertion': r'\+[acgtn]+',
    'deletion': r'\-[acgtn]+',
    }
"""dict: Short ``cs`` tag operation regular expression matches."""

_CS_STR_REGEX = regex.compile('(' + '|'.join(list(_CS_OPS.values())) + ')+')
"""regex.Regex: matches full-length short ``cs`` tags."""

_CS_OP_REGEX = regex.compile('|'.join(f"(?P<{op_name}>{op_str})" for
                                      op_name, op_str in _CS_OPS.items()))
"""regex.Regex: matches single ``cs`` operation, group name is operation."""


def split_cs(cs_string, *, invalid='raise'):
    """Split a short ``cs`` tag into its constituent operations.

    Parameters
    ----------
    cs_string : str
        The short ``cs`` tag.
    invalid : {'raise', 'ignore'}
        If `cs_string` is not a valid string, raise an error or ignore it
        and return `None`.

    Return
    ------
    list or None
        List of the individual ``cs`` operations, or `None` if invalid
        `cs_string` and `invalid` is 'ignore'.

    Example
    -------
    >>> split_cs(':32*nt*na:10-gga:5+aaa:10')
    [':32', '*nt', '*na', ':10', '-gga', ':5', '+aaa', ':10']

    >>> split_cs('bad:32*nt*na:10-gga:5', invalid='ignore') is None
    True

    >>> split_cs('bad:32*nt*na:10-gga:5')
    Traceback (most recent call last):
    ...
    ValueError: invalid `cs_string` of bad:32*nt*na:10-gga:5

    """
    m = _CS_STR_REGEX.fullmatch(cs_string)
    if m is None:
        if invalid == 'ignore':
            return None
        elif invalid == 'raise':
            raise ValueError(f"invalid `cs_string` of {cs_string}")
        else:
            raise ValueError(f"invalid `invalid` of {invalid}")
    else:
        return m.captures(1)


def cs_op_type(cs_op, *, invalid='raise'):
    """Get type of ``cs`` operation.

    Parameters
    ----------
    cs_op : str
        A **single** operation in a short ``cs`` tag.
    invalid : {'raise', 'ignore'}
        If `cs_string` is not a valid string, raise an error or ignore it
        and return `None`.

    Returns
    -------
    {'substitution', 'insertion', 'deletion', 'identity', None}
        Type of ``cs`` operation, or `None` if `cs_string` invalid and
        `invalid` is 'ignore'.

    Example
    -------
    >>> cs_op_type('*nt')
    'substitution'
    >>> cs_op_type(':45')
    'identity'
    >>> cs_op_type('*nt:45')
    Traceback (most recent call last):
    ...
    ValueError: invalid `cs_op` of *nt:45
    >>> cs_op_type('*nt:45', invalid='ignore') is None
    True

    """
    m = _CS_OP_REGEX.fullmatch(cs_op)
    if m is None:
        if invalid == 'ignore':
            return None
        elif invalid == 'raise':
            raise ValueError(f"invalid `cs_op` of {cs_op}")
        else:
            raise ValueError(f"invalid `invalid` of {invalid}")
    else:
        return m.lastgroup


class Alignment:
    """Process a SAM alignment with a ``cs`` tag to extract features.

    Parameters
    ----------
    sam_alignment : pysam.AlignedSegment
        Aligned segment from `pysam <https://pysam.readthedocs.io>`_,
        must have a short format ``cs`` tag (see
        https://lh3.github.io/minimap2/minimap2.html).

    Attributes
    ----------
    query_name : str
        Name of query in alignment.
    target_name : str
        Name of alignment target.
    cs : str
        The ``cs`` tag.
    query_clip5 : int
        Length at 5' end of query not in alignment.
    query_clip3 : int
        Length at 3' end of query not in alignment.
    target_clip5 : int
        Length at 5' end of target not in alignment.
    target_lastpos : int
        Last position of alignment in target (exclusive).

    """

    def __init__(self, sam_alignment):
        """See main class docstring."""
        self.query_name = sam_alignment.query_name
        self.target_name = sam_alignment.reference_name
        self.query_clip5 = sam_alignment.query_alignment_start
        self.query_clip3 = (sam_alignment.query_length -
                            sam_alignment.query_alignment_end)
        self.target_clip5 = sam_alignment.reference_start
        self.target_lastpos = sam_alignment.reference_end

        if sam_alignment.is_reverse:
            raise ValueError(f"alignment {self.name} is reverse orientation")

        if sam_alignment.has_tag('cs'):
            self.cs = sam_alignment.get_tag('cs')
        else:
            raise ValueError(f"alignment {self.name} has no `cs` tag")

        # build something that is self._cs_ops from split_cs

        # build a numpy array of the length in reference of each cs_op,
        # this could self._cs_op_lengths

        # you should somehow be able to build self._cs_op_ends
        # and self._cs_op_starts using reference start plus
        # numpy.cumsum(self._cs_op_lengths)

        assert len(self._cs_ops) == len(self._cs_op_lengths)
        assert len(self._cs_ops) == len(self._cs_op_ends)
        assert len(self._cs_ops) == len(self._cs_op_starts)

    def extract_cs(self, start, end, *,
                   max_clip5=0, max_clip3=0):
        """Extract ``cs`` tag corresponding to feature in target.

        Parameters
        ----------
        start : int
            Start of feature in target in 0, 1, ... numbering.
        end : int
            End of feature in target (not inclusive of this site).
        max_clip5 : int
            If alignment does not fully cover 5' end of feature,
            add gaps to returned ``cs`` string for uncovered region
            up to this length.
        max_clip3 : int
            Like `max_clip5` but for 3' end of feature.

        Returns
        -------
        str or `None`
            If region of target covered by feature is aligned, return
            str with ``cs`` tag for this portion of alignment. If that region
            is not covered (even adding any padding from `max_clip5` /
            `max_clip3`), return `None`.

        """
        # identify operations to include using numpy.argmin / argmax
        # on self.cs_op_starts / self._cs_op_ends
        # make sure we have indexing correct (0- or 1-based)

        # when you handle insertions on ends, document that
        raise RuntimeError('not yet implemented')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
