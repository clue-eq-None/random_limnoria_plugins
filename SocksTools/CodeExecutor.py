import os, sys

from twisted.internet.protocol import ProcessProtocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred, gatherResults

script = """
import time
for x in range(3):
    time.sleep(1)
    print(x)
"""

class SimpleProcess(ProcessProtocol):
    def __init__(self, id, d):
        self.id = id
        self.d = d
    def outReceived(self, out):
        print('Received output: {out} from: {proc}'
              .format(out=repr(out), proc=self.id))
    def processEnded(self, reason):
        self.d.callback(None)

ds = []
for x in range(3):
    d = Deferred()
    reactor.callLater(
        x * 0.5, reactor.spawnProcess, SimpleProcess(x, d),
        sys.executable, [sys.executable, '-u', '-c', script],
        os.environ)
    ds.append(d)

gatherResults(ds).addBoth(lambda ignored: reactor.stop())

reactor.run()
