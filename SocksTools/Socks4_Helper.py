from twisted.internet import protocol, reactor
from twisted.protocols import socks
from twisted.internet.defer import Deferred
import time
import threading

class ESocks4(socks.SOCKSv4):
    factory = None  
    def __init__(self, factory):
        socks.SOCKSv4.__init__(self, None)
        self.factory = factory

    def connectionLost(self, reason):
        self.factory.connectionClosed(self)
        socks.SOCKSv4.connectionLost(self, reason)

    def connectionFailed(self, reason):
        self.factory.connectionLost(self)
        socks.SOCKSv4.connectionFailed(self, reason)       
    

class ESocks4Factory(protocol.ServerFactory):
    protocol = ESocks4
    connections = {}
    closecb = None
    def __init__(self, closeCb):
        self.closeCb = closeCb

    def buildProtocol(self, address, ):
        new = ESocks4(self)
        self.connections[new] = 1
        return new

    def connectionClosed(self, socks4Con):
        if socks4Con in self.connections:
#            print "Con closed. conns: ", (len(self.connections)-1), str(socks4Con)
            del self.connections[socks4Con]

    # use dereferd here but meh
    def closeConnection(self, fire=False):
        if len(self.connections) < 1:
            self.closeCb(self)
            return
        for con in self.connections:
            con.transport.loseConnection()
        if fire:
            for con in self.connections:
                con.transport.abortConnection()
        reactor.callLater(5, self.closeConnection, True)

"""
def fu():
    reactor.callLater(10, fu2)
def fu2():
    listener.stopListening()
    factory.closeConnection()
def fu3(fact):
    print "closed:", fact

listener = None
factory = ESocks4Factory(fu3)
reactor.callWhenRunning(fu)
listener = reactor.listenTCP(1079, factory)

class Twisted_Runner(threading.Thread):
    def __init__(self): 
        threading.Thread.__init__(self)
    def run(self):
        try: reactor.run(installSignalHandlers=0)
        except Exception as e: pass
thread = Twisted_Runner()
#thread.daemon = True
thread.start()
"""
