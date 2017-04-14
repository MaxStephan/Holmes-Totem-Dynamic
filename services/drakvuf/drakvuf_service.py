import tornado
import tornado.web
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop

import json 

import os
from os import path

#Sample source path
mal_source = '/tmp'
config_path = './service.conf'

# Communcation with Drakvuf Interface
class drakvuf:
    def __init__(self):
        self.URL = '';
        self.http_client = tornado.httpclient.HTTPClient()

class Config:
    def __init__(self):
        self.HTTPBinding = '';
        self.VerifySSL = False;
        self.CheckFreeSpace = False;
        self.drakvufURL = '';
        self.MaxPending = 0;
        self.MaxAPICalls = 0;
        self.LogFile = '';
        self.Loglevel = '';

# global variables
drak = drakvuf()
drak_config = Config()


# HTTP Server for communication with Totem Dynamic
class status (tornado.web.RequestHandler):
	# return status information about the services state
    def get(self):
        print 'status'
        RespStatus = {'Degraded': False, 'Error': '', 'Freeslots': 0}

        # requesting status from drakvuf http server
        status_url = drak.URL + '/drakvuf/status'

        try:
            response = drak.http_client.fetch(status_url)
            # print response.body
            freeslots = drak_config.MaxPending - int(response.body)
            RespStatus["Freeslots"] = freeslots

        except tornado.httpclient.HTTPError as e:
            # HTTPError is raised for non-200 responses; the response
            # can be found in e.response.
            print "Error: " + str(e)
            RespStatus['Error'] = str(e)

        except Exception as e:
            # Other errors are possible, such as IOError.
            print "Error: " + str(e)
            # RespStatus['Error'] = str(e)

        RespStatus_json = json.dumps(RespStatus)
        # print max_pending
        # print RespStatus['Freeslots']
        self.write(RespStatus_json)




class feed (tornado.web.RequestHandler):

    def get(self, filename):
        sample_id = filename
        print 'feed' + ' ' + filename

        # read in sample
        RespNewTask = {'Error': '', 'TaskID': ''}
        sample_path = mal_source + '/' + sample_id

        if os.path.isfile(sample_path):
            # if sample exists
            sample_file = open(sample_path, 'r')
            sample = sample_file.read()

            # transfer to drakvuf
            http_header = {'Content-Type': 'application/octet-stream'}
            feed_url = drak.URL + '/drakvuf/feed/' + sample_id

            request = tornado.httpclient.HTTPRequest(feed_url, method = 'POST', headers = http_header, body = sample)

            try:
                response = drak.http_client.fetch(request)
                # print response.body
                resp_id = response.body
                RespNewTask["TaskID"] = resp_id

            except tornado.httpclient.HTTPError as e:
                # HTTPError is raised for non-200 responses; the response
                # can be found in e.response.
                print "Error: " + str(e)
                RespNewTask['Error'] = str(e)

            except Exception as e:
                # Other errors are possible, such as IOError.
                print "Error: " + str(e)
                # RespStatus['Error'] = str(e)

            sample_file.close()

        else:
            RespNewTask['Error'] = "No such sample"

        RespNewTask_json = json.dumps(RespNewTask)
        self.write(RespNewTask_json)




class check (tornado.web.RequestHandler):

    def get(self, filename):
        sample_id = filename
        RespCheckTask = {'Error': '', 'Done': False}
        
        check_url = drak.URL + '/drakvuf/check/' + sample_id

        try:
            response = drak.http_client.fetch(check_url)
            # print response.body
            if response.body == 'True':
                RespCheckTask["Done"] = True

        except tornado.httpclient.HTTPError as e:
            # HTTPError is raised for non-200 responses; the response
            # can be found in e.response.
            print "Error: " + str(e)
            RespCheckTask['Error'] = str(e)

        except Exception as e:
            # Other errors are possible, such as IOError.
            print "Error: " + str(e)
            # RespStatus['Error'] = str(e)

        RespCheckTask_json = json.dumps(RespCheckTask)
        # print max_pending
        # print RespStatus['Freeslots']
        self.write(RespCheckTask_json)


        

class results(tornado.web.RequestHandler):

    def get(self, filename):
        sample_id = filename
        print 'results '+filename
        RespTaskResults = {'Error': '', 'Results': ''}

        results_url = drak.URL + '/drakvuf/results/' + sample_id

        try:
            response = drak.http_client.fetch(results_url)
            # print response.body
            results_raw = {'Raw': response.body}
            RespTaskResults['Results'] = results_raw

        except tornado.httpclient.HTTPError as e:
            # HTTPError is raised for non-200 responses; the response
            # can be found in e.response.
            print "Error: " + str(e)
            RespTaskResults['Error'] = str(e)

        except Exception as e:
            # Other errors are possible, such as IOError.
            print "Error: " + str(e)
            # RespStatus['Error'] = str(e)

        RespTaskResults_json = json.dumps(RespTaskResults)
        # print max_pending
        # print RespStatus['Freeslots']
        self.write(RespTaskResults_json)
		



class Info(tornado.web.RequestHandler):
    def get(self):
        description = """
            <p>Copyright 2015 Holmes Processing
            <p>Description: This is the DRAKVUF Service for Totem-Dynamic.
        """
        self.write(description)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', Info),
            (r'/status', status),
            (r'/feed/([a-zA-Z0-9\-]*)', feed),
            (r'/check/([a-zA-Z0-9\-]*)', check),
            (r'/results/([a-zA-Z0-9\-]*)', results),
        ]
        settings = dict(
            template_path=path.join(path.dirname(__file__), 'templates'),
            static_path=path.join(path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.engine = None



def main():

    # read config file
    with open(config_path, 'r') as f:
     config_file = json.load(f)

    # port
    empty, port_string = config_file["HTTPBinding"].encode('ascii').split(':')
    port = int(port_string)
    print port

    # MaxPending
    maximum = config_file["MaxPending"]
    drak_config.MaxPending = int(maximum)
    print drak_config.MaxPending
    print config_file["MaxPending"]

    # drakvuf object
    drakvufURL = config_file["DRAKVUFURL"].encode('ascii')
    drak.URL = drakvufURL
    print drak.URL 


    # serve Totem Dynamic
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(port)
    # server.listen(11000)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

