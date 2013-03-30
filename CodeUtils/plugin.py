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
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('CodeUtils')



@internationalizeDocstring
class CodeUtils(callbacks.Plugin):
    """Add the help for "@plugin help CodeUtils" here
    This should describe *how* to use this plugin."""
    threaded = True

    def _runCommandFunction(self, irc, msg, command):
        """Run a command from message, as if command was sent over IRC."""
        tokens = callbacks.tokenize(command)
        try:
            self.Proxy(irc.irc, msg, tokens)
        except Exception, e:
            log.exception('Uncaught exception in requested function:')


    def replace(self, irc, msg, args):
        """[--d (" ")] <replace> <replacewith> [<string>,...]"""
        irc.reply(args[2:].join(" ").replace(args[0], args[1]))
    
    def rightOf(self, irc, msg, args):
        """[--d (" ")] <replace> <replacewith> [<string>,...]"""
        d = args[1:].join(" ")
        i = d.index(args[0])
        if i == -1: irc.reply("")
        else: irc.reply(d[i:])

    def foreachw(self, irc, msg, args):
        """[--d (" ")] <command> [<word>,...]
        """
        if len(args) < 3: #TODO
            return;
        delim = " "
        pos = 0
        if args[0] == '--d':
            delim = args[1]
            pos += 2
        cmd = args[pos]
        if cmd.find("%s") == -1: cmd += " %s"
        for line in args[pos+1:]:
            for part in line.split(delim):
                self._runCommandFunction(irc, msg, cmd.replace("%s", part))
    #foreach = wrap(foreach, [optional(('literal', ('--delim'))), ])


    def pyeval(self, irc, msg, args):
        """<Format containing %s (no %i or stuff)> <word> [<word>,...]
        Do a http://duckduckgo.com api search. For FIELDs and default values see 'ddgfields'.
        <maxLines> meaning: 0 = skip, -1 = unlimited, else limit to <maxLines> lines.
        EXAMPLE: ddg --* 0 --Definition 1 cat"""
        if len(args) < 1: return
        try: ret = eval(" ".join(args))
        except Exception as e:
            ret = str(e)
        irc.reply(ret)

    def pyexec(self, irc, msg, args):
        """<Format containing %s (no %i or stuff)> <word> [<word>,...]
        Do a http://duckduckgo.com api search. For FIELDs and default values see 'ddgfields'.
        <maxLines> meaning: 0 = skip, -1 = unlimited, else limit to <maxLines> lines.
        EXAMPLE: ddg --* 0 --Definition 1 cat"""
        if len(args) < 1: return
        try: exec args[0]
        except Exception as e:
            ret = str(e)

    def foreach(self, irc, msg, args):
        """<Format containing %s (no %i or stuff)> <word> [<word>,...]
        Do a http://duckduckgo.com api search. For FIELDs and default values see 'ddgfields'.
        <maxLines> meaning: 0 = skip, -1 = unlimited, else limit to <maxLines> lines.
        EXAMPLE: ddg --* 0 --Definition 1 cat"""
        if len(args) < 2: return
        if not "%s" in args[0]: args[0] += " %s"
        for word in args[1:]: self._runCommandFunction(irc, msg, args[0] % word)
#  cif = wrap(cif, ['boolean', 'something', 'something'])

Class = CodeUtils


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
