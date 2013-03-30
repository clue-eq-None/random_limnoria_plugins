###
# Copyright (c) 2013, sleep
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

# chr, decode, encode, len, levenshtein, md5, ord, sha, soundex, and xor


import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

import re

_ = PluginInternationalization('MoreStrings')

@internationalizeDocstring
class MoreStrings(callbacks.Plugin):
    """Add the help for "@plugin help MoreStrings" here
    This should describe *how* to use this plugin."""
    pass

###
# List stuff
###
    def contains(self, irc, msg, args, item, words):
        """<item><listitem1-X>
        return true if list (which is everything after <item> contains <item>)
        else return False"""
        if item in words: irc.reply("True")
        else: irc.reply("False")
    contains = wrap(contains, ['anything', many('anything')])

###
# String stuff
###
    def rof(self, irc, msg, args, caseSensitive, splitby, word):
        """<splitBy><text>
        TODO do doc
        """
        if caseSensitive != None: i = word.lower().rfind(splitby.lower())           
        else: i = word.rfind(splitby)
        slen = len(splitby)
        if i == -1 or i+slen >= len(word): irc.reply(" ")
        else: irc.reply(word[i+slen:])
    rof = wrap(rof, [optional(('literal', '--i')), 'anything', 'text'])
    def lof(self, irc, msg, args, caseSensitive, splitby, word):
        """<splitBy><text>
        TODO do doc
        """
        if caseSensitive != None: i = word.lower().find(splitby.lower())           
        else: i = word.find(splitby)
        slen = len(splitby)
        if i < 2: irc.reply(" ")
        else: irc.reply(word[:i-1])
    lof = wrap(lof, [optional(('literal', '--i')), 'anything', 'text'])


Class = MoreStrings


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
