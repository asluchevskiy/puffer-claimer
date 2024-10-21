import csv
import random

from degensoft.decryption import is_base64, decrypt_private_key
from degensoft.utils import load_lines


def load_and_decrypt_wallets(filename, password='', shuffle=False):
    """
    Will load wallets.txt file, if wallets was encrypted, trying to decrypt with the password provided
    :param filename:
    :param password:
    :param shuffle:
    :return:
    """
    lines = load_lines(filename)
    wallets = []
    for line in lines:
        if password and is_base64(line):
            wallets.append(decrypt_private_key(line, password))
        else:
            wallets.append(line)
    if shuffle:
        random.shuffle(wallets)
    return wallets


class FileReader:
    def __init__(self, file_name):
        self.wallets = []
        self.file_name = file_name

    def load(self) -> list:
        raise NotImplemented()

    def decrypt(self, password):
        for item in self.wallets:
            for key in item:
                if is_base64(item[key]):
                    item[key] = decrypt_private_key(item[key], password)

    def is_encrypted(self):
        for item in self.wallets:
            for key in item:
                if is_base64(item[key]):
                    return True
        return False

    def check(self) -> bool:
        return True


class CsvFileReader(FileReader):
    def load(self) -> list:
        with open(self.file_name, 'r') as f:
            return self.load_csv(f)

    def load_csv(self, stream) -> list:
        dialect = csv.Sniffer().sniff(stream.readline(), delimiters=";,")
        stream.seek(0)
        reader = csv.DictReader(stream, dialect=dialect)
        for row in reader:
            self.wallets.append(row)
        return self.wallets
