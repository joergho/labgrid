import os
import requests

from lxml import etree

# Driver has been tested with:
# ALL4176 ("ALLNET MSR IO Zentrale Schaltsteckdosenleiste 6-fach")

PORT = 80

class Allnet_Actor:
    id = None
    state = None
    resultText = None

@staticmethod
def _sendCommand(url):
    # send request
    r = requests.get(url, timeout=1)
    # check success
    r.raise_for_status()

    # parse xml
    root = etree.fromstring(r.text.encode('utf-8'))
    
    # seach for actors if it is not the root
    if root.tag != 'actor':
      actorList = root.xpath('//actor')
      if len(actorList) == 1:
        print("no actors found")
        return []
    else:
      actorList = [root]    
    
    # create a new empty status list of one group
    actorArray = []
    
    # create new actor objects
    for actorNode in actorList:
      actor = Allnet_Actor()
      
      for child in actorNode:
        if child.tag == "state":
          actor.state = child.text == "1"
        elif child.tag == "id":
          actor.id = int(child.text)
        elif child.tag == "result_text":
          actor.resultText = child.text
          
      actorArray.append(actor)
      
    # get status groups (just one)
    return actorArray

def power_set(host, port, index, value):
    index = int(index)
    assert 1 <= index <= 6

    actorList = _sendCommand(f"http://{os.environ['ALLNET_CREDENTIALS']}@{host}:{port}/xml/?mode=actor&type=switch&id={index}&action={int(value)}")

    # check success
    assert len(actorList) == 1

    # parse output
    assert actorList[0].resultText in ["nothing todo", "switch on", "switch off"]


def power_get(host, port, index):

    index = int(index)
    assert 1 <= index <= 6

    actorList = _sendCommand(f"http://{os.environ['ALLNET_CREDENTIALS']}@{host}:{port}/xml/?mode=actor&type=list")

    # extract portNumber and status from actors
    for actor in actorList:
      if index == actor.id:
         return actor.state
    raise RuntimeError(f"Could not determine state of index {index}")
