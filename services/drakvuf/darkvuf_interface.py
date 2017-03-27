import tornado
import tornado.web
import tornado.httpserver
import tornado.ioloop

import json 

import os
from os import path

#Settings

#DRAKVUF folder paths
mal_inc = '/home/max/autoDRAKVUF/malware_incoming'
mal_proc = '/home/max/autoDRAKVUF/malware_processing'
mal_fin = '/home/max/autoDRAKVUF/malware_finished'

port = 8090;


# Drakvuf http interface
class status_drak (tornado.web.RequestHandler):
	# return status information about the services state
    # number of samples beeing processed 
    def get(self):
    	tasks_pending = str(drak_stat.number_samples);
    	self.write(tasks_pending);
        print 'status' + tasks_pending


class feed_drak (tornado.web.RequestHandler):
    def post(self, filename):
        sample_id = filename
        print 'feed' + ' ' + filename
        print self.request.method

        inc_path = mal_inc + '/' + sample_id 

        if not os.path.isfile(inc_path):

            # update Service status
            drak_stat.samples.append(sample_id)
            drak_stat.update_sample_number()

            # writing the received sample to malware_incoming
            sample = self.request.body
            sample_file = open(inc_path, 'w+')
            sample_file.write(sample)

            # return true 
            self.write(sample_id)

        else:
            self.write('Error')

 

class check_drak (tornado.web.RequestHandler):
	# check if sample is ready
	# returns True/False
	def get(self, filename):
		sample_id = filename
		print 'check '+filename
		sample_path = mal_fin + '/' + sample_id + '/' + sample_id
		flag = os.path.isfile(sample_path)
		self.write(str(flag))


class results_drak (tornado.web.RequestHandler):

    def cleanup(self, result_folder):
        # deleting the whole result folder for a given sample (including all content)
        del_cmd = 'rm -rf ' + result_folder
        os.system(del_cmd)

    def get_results(self, folder):
        # get results 
        drakvuf_log_file = folder + '/' + 'drakvuf.log'
        f = open(drakvuf_log_file, 'r')
        log_raw = f.read()
        return log_raw

	def get(self, filename):
		sample_id = filename
		print 'results '+filename
        result_folder = mal_fin + '/' + filename
        results = self.get_results(result_folder)
        # self.cleanup

        # update Service status
        drak_stat.samples.remove(sample_id)
        drak_stat.update_sample_number()

        self.write(results)
        
      

    


class Info_drak(tornado.web.RequestHandler):
    def get(self):
        description = """
            <p>Description: This is the DRAKVUF Interface.
        """
        self.write(description)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', Info_drak),
            (r'/drakvuf/status', status_drak),
            (r'/drakvuf/feed/([a-zA-Z0-9\-]*)', feed_drak),
            (r'/drakvuf/check/([a-zA-Z0-9\-]*)', check_drak),
            (r'/drakvuf/results/([a-zA-Z0-9\-]*)', results_drak),
        ]
        settings = dict(
            template_path=path.join(path.dirname(__file__), 'templates'),
            static_path=path.join(path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.engine = None



class Service_Status:
	# contains list of all samples (IDs)
    def update_sample_number(self):
        self.number_samples = len(self.samples)

	def __init__(self):
		self.samples = [];
		self.number_samples = 0;



# global variables
drak_stat = Service_Status();


def main():

    drak_stat.samples = []
    drak_stat.number_samples = 0 


    server = tornado.httpserver.HTTPServer(Application())
    server.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()