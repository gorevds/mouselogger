from os import path, listdir, remove
import zipfile

from common import LOG_DIR


def add_to_archive(directory):
    if not path.exists(LOG_DIR):
        return

    files = []
    for file in listdir(LOG_DIR):
        if file.endswith(".txt"):
            files.append(file)

    if not len(files):
        return

    for file in files:
        file_zip = zipfile.ZipFile(directory + file[:-4] + '.zip', 'w')
        file_zip.write(directory + file, zipfile.ZIP_DEFLATED)
        file_zip.close()
        remove(directory + file)


def all_to_one(directory, name):
    z = zipfile.ZipFile(directory + name + '.zip', 'w', zipfile.ZIP_LZMA)
    for file in listdir(directory):
        if file.endswith(".zip"):
            continue
        z.write(directory + file)
        remove(directory + file)
    z.close()
