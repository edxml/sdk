

# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

def truncate_string(string, max_length, trunc_head=False):
    """

    Returns a copy of specified string which is truncated if
    its length exceeds the specified length limit. Trailing ellipsis
    is used to indicate that the string was truncated.

    Args:
        string (str): Input string
        max_length (int): Max output length
        trunc_head (bool): Truncate head in stead of tail?

    Returns:

    """
    max_length = max(3, max_length)
    if len(string) > max_length:
        if trunc_head:
            return '...' + string[len(string)-max_length+3:]
        else:
            return string[:max_length - 3] + '...'
    else:
        return string
