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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

#TODO maybe use supybot threads. i saw them somewhere
import threading
from twisted.internet import reactor, protocol
from twisted.protocols import socks
import time

import Socks4_Helper

_ = PluginInternationalization('SocksTools')

class Twisted_Runner(threading.Thread):
    ticks = 0
    def __init__(self): 
        threading.Thread.__init__(self)
    def run(self):  
        try: reactor.run(installSignalHandlers=0)
        except Exception as e: print "twisted e:", str(e) #self.irc.reply(e)
    def getticks(): return ticks
    def incTick(): self.ticks += 1      
tick = 1

@internationalizeDocstring
class SocksTools(callbacks.Plugin):
    """Add the help for "@plugin help SocksTools" here
    This should describe *how* to use this plugin."""
    threaded = True
    # TODO add locking for these fuckers
    # ports => (user, started, runTime, irc, factory, listener)
    proxies = {}
    # factory => port
    facToPort = {}
    checkInterval = 10
    # needed to handle reloads without creating one twisted cb each time
    lastTwistedCB = 0
    def __init__(self, irc):
        self.__parent = super(SocksTools, self)
        self.__parent.__init__(irc)
        # start twisted TODO if not already running
        if not reactor.running:
            print "starting up twisted reactor"
            thread = Twisted_Runner()
            thread.daemon = True
            thread.start()
#            time.sleep(1)
        else: print "Twisted reactor already running"
#        time.sleep(5)
        while not reactor.running:
            print "wait for reactor"
            time.sleep(2)
        print reactor.callFromThread(self._twistedLoop, irc)

    def _twistedLoop(self, irc):
        if irc.getCallback('SocksTools') == None: return
        for port, values in self.proxies.items():
            if values[2] > 0 and values[2] <= time.time():
                values[3].reply('Closing proxy on port '+str(port))
                values[5].stopListening()
                values[4].closeConnection()
        print "loop"
#        for proxy in self.proxies.values(): proxy[3].reply("loop")
        reactor.callLater(self.checkInterval, self._twistedLoop, irc)

    def _proxyClosedCb(self, proxy):
        if proxy not in self.facToPort:
            raise Exception("ProxyCloseCb called but that proxy didn't exists oO strange")
        # (user, started, runTime, replyTo, irc, factory, listener)
        stuff = self.proxies[self.facToPort[proxy]]
        stuff[3].reply("Proxyserver on port "+str(self.facToPort[proxy])+" closed.")
        del self.proxies[self.facToPort[proxy]]
        del self.facToPort[proxy]

    def _createSocks4Server(self, irc, port, runTime, user):   
        if port in self.proxies:
            irc.reply("There is already a Proxy running on port " + str(port))
            return
        irc.reply('Try to start proxy server for ' + str(runTime) + ' secs on port ' + str(port))
        factory = Socks4_Helper.ESocks4Factory(self._proxyClosedCb)
        try: listener = reactor.listenTCP(port, factory)
        except Exception as e:
            irc.reply("An exception occured: "+str(e))
            return
        started = time.time()
        if runTime > 0:
            runTime += started
        self.proxies[port] = [user, started, runTime, irc, factory, listener]
        self.facToPort[factory] = port
        irc.reply('Proxy on port '+str(port)+' successfully started')

    def _listSocks4Server(self, irc):
        irc.reply("%s %s %s %s" % ("port", "user", "started", "runtime"))
        for port, proxy in self.proxies.items():
            #user, started, runTime, replyTo
            irc.reply("%s %s %s %s" % (str(port), proxy[0], proxy[1], proxy[2]))

    def _removeSocks4Server(self, irc, port):
        if port not in self.proxies:
            irc.reply("There is no proxy running on port " + str(port))
            return
        # This should get removed at the next twisted tick
        self.proxies[port][2] = 1

    def socks4(self, irc, msg, args, argtype, port, runTime=60):
        """socks4 <add|remove|list> <port> <timeToRunInSec>
        handle (spawn/remove/list) sicks4 proxies"""
        if argtype == 'add':
            if port == None: return
            # TODO get botname
            self._createSocks4Server(irc, port, runTime, msg.prefix)
        elif argtype == 'list':
            self._listSocks4Server(irc)
        elif argtype == 'remove':
            self._removeSocks4Server(irc, port)
    socks4 = wrap(socks4, [('literal', ('add', 'remove', 'list')), optional('int'), optional('int')])

    def die(self):        
        # we don't want zombie thread do we ? ;)
        print "Del SocksTools"
        # dirty but yeah
        for i in xrange(0,2):
            for calls in reactor.getDelayedCalls():
                if calls.func == self._twistedLoop and calls.active():
                    print "cancel", calls
                    try: calls.cancel()
                    except Exception as e: print e
            time.sleep(1)
        for port, values in self.proxies.items():
            print "close port ", port
            values[3].reply('Closing proxy on port '+str(port))
            values[5].stopListening()
            values[4].closeConnection()     
        for calls in reactor.getDelayedCalls():
            if calls.func == self._twistedLoop and calls.active():
                print "cancel", calls
                try: calls.cancel()
                except Exception as e: print e

Class = SocksTools


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
