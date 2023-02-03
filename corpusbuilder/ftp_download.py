import pycurl
import logging
from corpusbuilder.helper import *

class FTPDownload(object):

    index_file_local = ""

    def __init__(self, config):
        self.file = None
        self.pbar = None
        self.config = config


    def get_index_file(self):
        """"Get the name of the index file to use (and download it if not available locally)"""
        if self.config.index_file_local:
            logging.info('Using local index file: ' + str(self.config.index_file_local))
            self.index_file_local = self.config.index_file_local

        else:
            logging.info('Downloading index file...')
            self.download_ftp_file(self.config.pubmed_ftp_path, self.config.index_file_name)
            self.index_file_local = self.config.corpus_download_dir + self.config.index_file_name
            logging.info('Downloaded index file')
        return self.index_file_local


    def download_ftp_file(self, path, file_name):
        """Download a file via FTP"""
        
        # if folder doesn't exist, create it
        create_dir(self.config.corpus_download_dir)

        # download the file
        try:
            output_file = self.config.corpus_download_dir + file_name

            curl=pycurl.Curl()
            curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
            curl.setopt(pycurl.PROXY, self.config.proxy)            # set proxy

            pmc_url = self.config.pubmed_ftp_server + '/' + path + '/' + file_name
            curl.setopt(pycurl.URL, pmc_url)

            fp = open(output_file, 'wb')
            curl.setopt(pycurl.WRITEDATA, fp)
            curl.perform()
            curl.close()
            fp.close()
        except Exception as e:
            logging.exception("Error downloading PMC paper archive")
