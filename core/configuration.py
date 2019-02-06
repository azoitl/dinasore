from core import fb_resources
from core import fb
from core import fb_interface
from xml.etree import ElementTree as ETree
import logging


class Configuration:

    def __init__(self, config_id, config_type):
        self.fb_dictionary = dict()

        self.config_id = config_id

        self.create_fb('START', config_type)

    def get_fb(self, fb_name):
        fb_element = None
        try:
            fb_element = self.fb_dictionary[fb_name]
        except KeyError as error:
            logging.error('can not find that fb')
            logging.error(error)

        return fb_element

    def set_fb(self, fb_name, fb_element):
        self.fb_dictionary[fb_name] = fb_element

    def create_fb(self, fb_name, fb_type):
        logging.info('creating a new fb...')

        fb_res = fb_resources.FBResources(fb_type)

        exists_fb = fb_res.exists_fb()
        if not exists_fb:
            # Downloads the fb definition and python code
            logging.info('fb doesnt exists, needs to be downloaded ...')
            fb_res.download_fb()

        fb_definition, fb_exe = fb_res.import_fb()

        # check if if happened any importing error
        if fb_definition is not None:
            fb_element = fb.FB(fb_name, fb_type, fb_exe, fb_definition)
            self.set_fb(fb_name, fb_element)
            logging.info('created fb type: {0}, instance: {1}'.format(fb_type, fb_name))

        else:
            logging.error('can not create the fb type: {0}, instance: {1}'.format(fb_type, fb_name))

    def create_connection(self, source, destination):
        logging.info('creating a new connection...')

        source_attr = source.split(sep='.')
        destination_attr = destination.split(sep='.')

        source_fb = self.get_fb(source_attr[0])
        source_name = source_attr[1]
        destination_fb = self.get_fb(destination_attr[0])
        destination_name = destination_attr[1]

        connection = fb_interface.Connection(destination_fb, destination_name)
        source_fb.add_connection(source_name, connection)

        logging.info('connection created between {0} and {1}'.format(source, destination))

    def create_watch(self, source, destination):
        logging.info('creating a new watch...')

        source_attr = source.split(sep='.')
        source_fb = self.get_fb(source_attr[0])
        source_name = source_attr[1]

        source_fb.set_attr(source_name, set_watch=True)

        logging.info('watch created between {0} and {1}'.format(source, destination))

    def delete_watch(self, source, destination):
        logging.info('deleting a new watch...')

        source_attr = source.split(sep='.')
        source_fb = self.get_fb(source_attr[0])
        source_name = source_attr[1]

        source_fb.set_attr(source_name, set_watch=False)

        logging.info('watch deleted between {0} and {1}'.format(source, destination))

    def write_connection(self, source_value, destination):
        logging.info('writing a connection...')
        destination_attr = destination.split(sep='.')
        destination_fb = self.get_fb(destination_attr[0])
        destination_name = destination_attr[1]

        # Verifies if is to write an event
        if source_value == '$e':
            logging.info('writing an event...')
            v_type, value, is_watch = destination_fb.read_attr(destination_name)
            if value is not None:
                # If the value is not None increment
                destination_fb.push_event(destination_name, value + 1)
            else:
                # If the value is None push 1
                destination_fb.push_event(destination_name, 1)

        # Writes a hardcoded value
        else:
            logging.info('writing a hardcoded value...')
            destination_fb.set_attr(destination_name, source_value)

        logging.info('connection ({0}) configured with the value {1}'.format(destination, source_value))

    def read_watches(self, start_time):
        logging.info('reading watches...')

        resources_xml = ETree.Element('Resource', {'name': self.config_id})

        for fb_name, fb_element in self.fb_dictionary.items():
            fb_xml, watches_len = fb_element.read_watches(start_time)

            if watches_len > 0:
                resources_xml.append(fb_xml)

        fb_watches_len = len(resources_xml.findall('FB'))
        return resources_xml, fb_watches_len

    def start_work(self):
        logging.info('starting the fb flow...')
        for fb_name, fb_element in self.fb_dictionary.items():
            if fb_name != 'START':
                fb_element.start()

        outputs = self.get_fb('START').fb_exe()
        self.get_fb('START').update_outputs(outputs)

    def stop_work(self):
        logging.info('stopping the fb flow...')
        for fb_name, fb_element in self.fb_dictionary.items():
            if fb_name != 'START':
                fb_element.stop()
