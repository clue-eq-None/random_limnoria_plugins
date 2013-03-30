###
# Copyright (c) 2013, Sleep
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

import json
import urllib
import types

_ = PluginInternationalization('DuckDuckGoSimple')
url = "http://api.duckduckgo.com/?format=json&pretty=1&no_redirect=1&no_html=1&q=%s"

def splitwordgen(lineGen, maxLineLen, *args):
    """this generator splits overlong strings provided by the lineGen generator.
    provide args to the lineGen generator at will"""
    for line in lineGen(*args):
        if len(line) < maxLineLen: yield line
        else:
            last = 0
            while last < len(line):
                i = line.rfind(" ", last, last+maxLineLen)
                if i != -1:
                    yield line[last:i]
                    last = i + 1
                else:
                    yield line[last:last+maxLineLen]
                    last = last+maxLineLen


def print_coroutine(irc, user):
    try:
        # todo get from config
        directPrint = 1
        for i in xrange(0, directPrint): irc.reply((yield))
        tmp = (yield)
        irc._mores[user[0]] = (True, [tmp])
        irc._mores[user[1]] = irc._mores[user[0]][1]
        while True: irc._mores[user[0]][1].insert(0, (yield))
    except GeneratorExit as e:
        pass # irc.reply("e: "+str(e))

##
# Here are the generator generating responses from json fields
##
def genText_relatedTopics(daMap):
    relatesPerMsg = 5
    n = 1
    curStr = ircutils.bold("Related: ")
    for link in daMap[u'RelatedTopics']:
        if u'Topics' in link:
            for topic in link[u'Topics']:
                curStr += topic[u'Text']+" | "
                n+=1
                if n >= relatesPerMsg:
                    yield curStr
                    n = 0
                    curStr = ""
        else:
            curStr += link[u'Text']+" | "
            n+=1
            if n >= relatesPerMsg:
                yield curStr
                n = 0
                curStr = ""
    if n>0: yield curStr

def genText_Results(daMap):
    for link in daMap[u'Results']:
        if u'Topics' in link:
            for topic in link[u'Topics']:
                yield ircutils.bold(topic[u'Text']) + ": " + topic[u'FirstURL']
        else:
            yield ircutils.bold(link[u'Text']) + ": " + link[u'FirstURL']

def definitionHelper(x):
    if len(x[u'DefinitionSource']) > 0:
        yield ircutils.bold(x[u'DefinitionSource']+": ")+x[u'Definition']
    else:
        yield ircutils.bold("DuckDuckGo: ")+x[u'Definition']

supportedFields = {
    u'Redirect':[
        lambda x: [ircutils.bold("Redirect: ")+x[u'Redirect']],
        -1,
        "Print the redirect url (used by !bang syntax)"
    ],
    u'Definition':[
        definitionHelper,
        -1,
        "Print a definition ... doh"
    ],
    u'Answer':[
        lambda x: [ircutils.bold(x[u'AnswerType']+": ")+x[u'Answer']],
        -1,
        "Print a direct answer. (Used for DDGs internal commands like md5,calc..)"
    ],
    u'AbstractText':[
        lambda x: [ircutils.bold(x[u'AbstractSource']+": ")+x[u'AbstractText']],
        -1,
        "Print an abstract overview about the topic... kind of"
    ],
    u'RelatedTopics':[
        genText_relatedTopics,
        2,
        "Print a bunch of related infos incl. internal links"
    ],
    u'Results':[
        genText_Results,
        3,
        "Extrenal links. (in most cases offical sites from product x)"
    ]
}

@internationalizeDocstring
class DuckDuckGoSimple(callbacks.Plugin):
    """Add the help for "@plugin help DuckDuckGoSimple" here
    This should describe *how* to use this plugin."""
    threaded = True

    def _runCommandFunction(self, irc, msg, command):
        """Run a command from message, as if command was sent over IRC."""
        tokens = callbacks.tokenize(command)
        try:
            self.Proxy(irc.irc, msg, tokens)
        except Exception, e:
            log.exception('Uncaught exception in requested function:')

    def ddgfields(self, irc, msg, args):
        """no Parameter
        List all FIELDs and default values"""
        for field, value in supportedFields.items():
            irc.reply(field + " - " + value[2] + " ("+str(value[1])+")")

    def ddg(self, irc, msg, args):
        """[--<FIELD|*> <maxLines>] <ddg-cmd>
        Do a http://duckduckgo.com api search. For FIELDs and default values see 'ddgfields'.
        <maxLines> meaning: 0 = skip, -1 = unlimited, else limit to <maxLines> lines.
        EXAMPLE: ddg --* 0 --Definition 1 cat"""
        curLineRest = dict([(x,y[1]) for x,y in supportedFields.items()]) # baeh but meh... lineRestrictions.copy()
        # read params (TODO i saw some param binding calls in other fucs.. check that)
        i = 0
        while i < len(args)-1 and args[i].startswith("--"):
            nval = -1
            try: nval=int(args[i+1])
            except: 
                irc.reply(args[i+1] + " is not a valid int")    
                return
            key = args[i][2:]
            if key == "*":
                for restriction in curLineRest: curLineRest[restriction] = nval
            elif key not in supportedFields:
                irc.reply(key + " is no valid FIELD. See ddgfields")
                return           
            else:
                curLineRest[key] = nval
            i += 2


        # set up print coroutine
        user = msg.prefix.split('!', 1)
        printer = print_coroutine(irc, user)
        printer.next()

        maxReply = int(str(conf.supybot.reply.mores.length)) # lol
        if maxReply == 0: maxReply = 450

        turl = url % (urllib.quote_plus(" ".join(args[i:])))
        # TODO check how to use the log feature and log this as INFO
#        irc.reply("i'll send: " + turl)    
        # now comes the webrequest part
#        try:
        wfd = utils.web.getUrlFd(turl)
        data = json.loads(wfd.read())
        wfd.close()

        gotReturn = False
        for field in data.items():
            if len(field[1]) < 1 or field[0] not in supportedFields or curLineRest[field[0]] == 0: continue
            gotReturn = True
            n=0
            for lines in splitwordgen(supportedFields[field[0]][0], maxReply, data):
                if curLineRest[field[0]] != -1:
                    n+=1
                    if n > curLineRest[field[0]]: break
                #irc.reply(lines)
                printer.send(lines)

        if not gotReturn: irc.reply("DuckDuckGo.com found nothing according to your search criteria. Anyway it is a cool search-engine. It really is :)")
        else:
            #for i in xrange(0,int(str(conf.supybot.reply.mores.instant))):
            if len(irc._mores[user[0]][1]) > 0: self._runCommandFunction(irc, msg, "more")
#        except Exception as e:
            # Usually an urllib error
            # maybe handle some special cases here ?
#            raise e
        printer.close()

Class = DuckDuckGoSimple

# wtf is this ?
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
