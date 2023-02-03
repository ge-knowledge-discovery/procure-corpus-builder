import csv

class DocumentIndex(object):
    """A class to store and access the document index file retrieved from PMC, containing file metadata e.g. license, download location"""
    
    def __init__(self, csv_file, config):
        self.accession_id_index = None
        self.file_url_index = None
        self.license_index = None
        self.csv_dict = None
        self.csv_file = csv_file
        self.config = config
        self.csv_file_read = None
        self.__read_csv()
        self.__create_in_memory_dic()

    def __read_csv(self):
        """Read the CSV file"""
        opened_csv_file = open(self.csv_file, 'r', encoding='utf_8_sig')
        self.csv_file_read = csv.reader(opened_csv_file, delimiter=',')
        self.__set_csv_columns_index()

    def __set_csv_columns_index(self):
        """Remember certain column indices"""
        header_list = next(self.csv_file_read)
        self.accession_id_index = header_list.index(self.config.accession_id_csvheader)
        self.file_url_index = header_list.index(self.config.file_url_csvheader)
        self.license_index = header_list.index(self.config.license_csvheader)

    def __create_in_memory_dic(self):
        """Create an in-memory dictionary mapping PMC id to its metadata"""
        self.csv_dict = {}
        for row in self.csv_file_read:
            if len(row) >= 5:
                if row[self.accession_id_index] not in self.csv_dict:
                    self.csv_dict[row[self.accession_id_index]] = row

    @staticmethod
    def __separate_path_url(file_url):
        file_path = file_url[:file_url.rfind('/') + 1]
        file_name = file_url[file_url.rfind('/') + 1:]
        return file_path, file_name

    def get_metadata(self, accession_id: str) -> dict:
        """
        Find metadata for a given PMCID
        :param accession_id: query accession_id
        :return dict: {'result': True/False, 'ftp_file_path': 'ftp_file_path', 'file_name': 'file_name', 'pmc_id': 'pmc_id'}
        """
        license_list = ['CC BY', 'CC0']
        if accession_id in self.csv_dict:
            pmc_row = self.csv_dict[accession_id]
            if pmc_row[self.license_index] in license_list:
                file_path, file_name = self.__separate_path_url(pmc_row[self.file_url_index])
                return {'result': True, 'ftp_file_path': file_path, 'file_name': file_name, 'pmc_id': accession_id, "pmc_license": pmc_row[self.license_index]}

        return {'result': False, 'ftp_file_path': None, 'file_name': None, 'pmc_id': accession_id, "pmc_license": None}

