"""
Ting-Yao Hu, 2017.04
"""

import sys
import BaseHTTPServer
import time
import cgi
import json
import cv2

HOST_NAME = ''
PORT_NUMBER = 9001

"""
Camera manager: manage parking slots covered by one camera
"""
class CamManager(object):
    def __init__(self,slot_fn):
        self.slot2latlng = dict([(l.split(':')[0],l.split(':')[1]) for l in file(slot_fn)])
        self.occupy = {}
        self.slot2rowid = dict([(l.split(':')[0],int(l.split(':')[2])) for l in file(slot_fn)])
        for s in self.slot2latlng.keys():
            self.occupy[s] = 0

    def update(self, sidlst, olst):
        for sid, det in zip(sidlst,olst):
            if self.occupy[sid]!=-1:  ### not locked
                self.occupy[sid] = det

    def lock(self, sid):
        self.occupy[sid] = -1

    def unlock(self, sid):
        self.occupy[sid] = 1

    def get_empty_slot(self):
        for s in self.slot2latlng.keys():
            if self.occupy[s]==1: return s,self.slot2latlng[s],self.slot2rowid[s]
        return 'full','full','full'

"""
Parking field manager
"""
class ParkManager(object):
    def __init__(self):
        self.camdict = {}
        self.camdict[6] = CamManager('slot_latlng_6.txt')
        self.camdict[4] = CamManager('slot_latlng_4.txt')
        self.imgdict = {}
        self.imgdict[6] = None
        self.imgdict[4] = None

    def dummyResponse(self):
        obj = {}
        obj['slot'] = False
        return json.dumps(obj)

    def assignSlot(self):
        for cid in self.camdict.keys():
            sid,latlngstr,rowid = self.camdict[cid].get_empty_slot()
            if sid is not 'full': return self.latlngjstr(sid,cid,latlngstr,rowid)
        return self.dummyResponse()

    def latlngjstr(self,sid,cid,latlngstr,rowid):
        obj = {}
        obj['slot'] = True
        obj['camid'] = cid
        obj['slotid'] = sid
        obj['lat'] = float(latlngstr.split(',')[0])
        obj['lng'] = float(latlngstr.split(',')[1])
        obj['rowid'] = int(rowid)
        return json.dumps(obj)

    def update_detection(self, camid, sidlst, ilst):
        self.camdict[camid].update(sidlst,ilst)
        
    def lock(self, cid, sid):
        self.camdict[cid].lock(sid)

    def unlock(self, cid, sid):
        self.camdict[cid].unlock(sid)


parkmanager = ParkManager()
class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(s):
        form = cgi.FieldStorage(
            fp = s.rfile,
            headers = s.headers,
            environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':s.headers['Content-Type']},
        )
        cmd = form['cmd'].value
        if cmd=='request_slot':
            ### get an available slot
            responseText = parkmanager.assignSlot()
        elif cmd=='update':
            camid = int(form['camid'].value)
            sidlst = form['slotid'].value.split(':')
            lst = form['detection'].value.split(',')
            ilst = [int(i) for i in lst]
            print ilst
            parkmanager.update_detection(camid,sidlst,ilst)
            responseText = parkmanager.dummyResponse()
        elif cmd=='lock':
            camid = int(form['camid'].value)
            sid = form['slotid'].value
            parkmanager.lock(camid,sid)
            responseText = parkmanager.dummyResponse()

        elif cmd=='unlock':
            camid = int(form['camid'].value)
            sid = form['slotid'].value
            parkmanager.unlock(camid,sid)
            responseText = parkmanager.dummyResponse()

        elif cmd=='img':
            camid = int(form['camid'].value)
            data = form['imgfile'].file.read()
            print 'updating image...'
            imgfn = 'tmp'+str(camid)+'.jpg'
            outfile = open(imgfn,'wb')
            outfile.write(data)
            responseText = parkmanager.dummyResponse()

        if cmd=='request_img':
            print 'response image'
            camid = int(form['camid'].value)
            sid = str(form['slotid'].value)

            ### add slot box on image
            imgfn = 'tmp'+str(camid)+'.jpg'
            im = cv2.imread(imgfn)
            x1,x2,y1,y2 = [int(sl) for sl in sid.split(',')]
            cv2.rectangle(im, (x1,y1),(x2,y2), (0,255,0), 2)
            cv2.imwrite('send.jpg',im)

            s.send_response(200)
            s.send_header('Content-type', 'image/jpeg')
            s.end_headers()
            imgfn = 'send.jpg'
            s.wfile.write(open(imgfn,'rb').read())
            #s.wfile.write(responseText)

        else:
            print 'response: ',responseText
            s.send_response(200)
            s.send_header('Content-type', 'text')
            s.end_headers()
            s.wfile.write(responseText)


if __name__=='__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
