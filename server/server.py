### Ting-Yao Hu, 2016.07
### benken.tyhu@gmail.com

import BaseHTTPServer
import time
import cgi
import json

#HOST_NAME = 'localhost'
HOST_NAME = ''
PORT_NUMBER = 9001

class parkManager(object):
    def __init__(self):
        self.slot_lab = [1]*24
        self.latlng = [(40.494081,-80.26099)]*9+[(40.494081,-80.26120)]*8+[(40.494081,-80.26078)]*7
    def assignSlot(self):
        obj = {}
        for i,lab in enumerate(self.slot_lab):
            if lab==0:
                lnt = self.latlng[i][0]
                lat = self.latlng[i][1]
                return self.latlngjstr(lnt,lat)
        return self.dummyResponse()
    def latlngjstr(self,lat,lng):
        obj = {}
        obj['slot'] = True
        obj['lat'] = lat
        obj['lng'] = lng
        return json.dumps(obj)

    def update_detection(self,lst):
        self.slot_lab = lst

    def dummyResponse(self):
        obj = {}
        obj['slot'] = False
        return json.dumps(obj)

parkmanager = parkManager()

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
            lst = form['detection'].value.split(',')
            ilst = [int(i) for i in lst]
            print ilst
            parkmanager.update_detection(ilst)
            responseText = parkmanager.dummyResponse()
        
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
