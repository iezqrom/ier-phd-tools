import os, sys
import re
import pickle
import pandas as pd
import csv
import shutil
import time
import numpy as np

################################################################################
############################# FUNCTION #########################################
################################################################################


def error(e):
    print(e)
    exc_type, _, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)


def getNames(path_data, pattern):
    pattern_data_failed = pattern
    patternc_data_failed = re.compile(pattern_data_failed)
    names_data_failed = []

    for filename in os.listdir(f"{path_data}"):
        # print(filename)
        if patternc_data_failed.match(filename):
            # print(filename)
            name, form = filename.split(".")
            names_data_failed.append(name)
        else:
            continue

    names_data_failed.sort(key=natural_keys)

    return names_data_failed


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def recoverPickleRick(path_data, name_file):
    backup_file = open(f"{path_data}/{name_file}.pkl", "rb")
    recoveredPickle = pickle.load(backup_file)
    backup_file.close()
    return recoveredPickle


def savePickleRick(path_data, name_file, data):
    backup_file = open(f"{path_data}/{name_file}.pkl", "wb")
    pickle.dump(data, backup_file)
    backup_file.close()


def recoverData(names, path_data, data):
    print(names)
    if len(names) > 0:
        recovered_data = pd.read_csv(f"{path_data}/{names[-1]}.csv")
        lsrd = recovered_data.to_dict("list")
        data = {key: lsrd[key] for key, value in lsrd.items()}
        return data
    else:
        return data


def recoveredToTempWriter(
    names, path_data, data, temp_data_writer, temp_file_name="temp_data"
):
    if len(names) > 0:
        try:
            temp_file_name = names[-1]
        except:
            temp_file_name = temp_file_name

        temp_file = open(f"{path_data}/{temp_file_name}.csv", "a")
        temp_data_writer = csv.writer(temp_file)

        print("\nRecovering data from temporal failed attempt\n")
        recovered_data = pd.read_csv(f"{path_data}/{names[-1]}.csv")
        lsrd = recovered_data.to_dict("list")
        data = {key: lsrd[key] for key, value in lsrd.items()}
        print(data)

        for di, ds in enumerate(data["subject"]):
            pastTemprow = []
            # print(ds)
            keys = data.keys()
            for k in keys:
                pastTemprow.append(data[k][di])

            temp_data_writer.writerow(pastTemprow)

        temp_file.close()

    return temp_data_writer, data


def pusherWarning(n_pushes=2000):
    file_name = "./data/pusher_counter"
    file = open(file_name)
    old_value = int(file.read())

    if old_value > n_pushes:
        os.system("clear")
        print(old_value)
        input(
            "WARNING: PUSHER HAS PERFORMED MORE THAN 2000 PUSHES. CONSIDER REPLACING IT. Press enter to continue"
        )


def spaceLeftWarning():
    _, _, free = shutil.disk_usage("/")

    free_human = free // (2 ** 30)

    if free_human < 3:
        os.system("clear")
        print(
            f"WARNING: THERE ARE ONLY {free_human} GiB LEFT IN YOUR HARD DRIVE. YOU MIGHT NOT BE ABLE TO FINISH THE EXPERIMENT AND LOSE DATA. CONSIDER REMOVING FILES."
        )
        time.sleep(2)


def create_list(dictionary, index):
    return [dictionary[key][index] for key in dictionary.keys()]


def rewriteRecoveredData(data, path, file_name):
    if len(data[list(data.keys())[0]]) > 0:
        temp_file = open(f"{path}/{file_name}", "a")
        temp_data_writer = csv.writer(temp_file)

        for i in np.arange(0, len(data[list(data.keys())[0]])):
            row = create_list(data, i)
            temp_data_writer.writerow(row)

        temp_file.close()
    else:
        print("\nNo data to rewrite\n")
