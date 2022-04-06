import csv
import numpy as np
import os
import time
from datetime import date
import pandas as pd
import subprocess
import re
import shutil
from classes_text import (
    printme,
    agebyExperimenter,
    sexbyExperimenter,
    handednessbyExperimenter,
)
import copy

##################################################################
###################### Storing data ##############################
################################################################
def buildDict(*keys):
    """
    Build dictionary to store data during experiment
    """
    data = {}
    list_llaves = list([*keys])
    print(list_llaves)
    for i in np.arange(len(list_llaves)):
        data[list_llaves[i]] = []

    return data


def copyDict(data):
    """
    Function to copy dictionary
    """
    return copy.deepcopy(data)


def appendDataDict(data, tempdata):
    """
    Append data to dictionary
    """
    keys = data.keys()
    for i, k in enumerate(keys):
        data[k].append(tempdata[i])

    return data


def subjFile(path, file="subjs.csv"):
    """
    Function to create subject file (date, time, age, valid, state (ex 1)/tb 1))
    """
    of1 = open(f"{path}/data/{file}", "w")
    data_writer = csv.writer(of1)

    header = ["Date", "Time", "NumDayWithin", "Age", "Valid", "State"]

    data_writer.writerow(header)

    of1.close()


def setSubjNumDec(age, numdaywithin, situ, file="subjs.csv"):
    """
    Function to save subject date, time, valid and age
    """
    steps_back = depthToSrc()
    path = f"{steps_back}data/{file}"
    if not open(path):
        subjFile(path)
    sf = open(f"./{steps_back}data/{file}", "a")
    data_writer = csv.writer(sf)

    t = time.localtime()
    time_now = time.strftime("%H_%M_%S", t)
    todaydate = date.today().strftime("%Y%m%d")

    if situ == "tb":
        state = 0
    elif situ == "ex":
        state = 1

    data_writer.writerow([todaydate, time_now, numdaywithin, age, 0, state])

    sf.close()

    return todaydate, time_now


def getSubjNumDec(file="subjs.csv", day=None):
    steps_back = depthToSrc()

    if day:
        numdaywithin = None
    else:
        df = pd.read_csv(f"./{steps_back}data/{file}")
        nums_within = df.loc[:, "NumDayWithin"]

        numdaywithin = int(nums_within.to_numpy()[-1])

    return numdaywithin


def getAgeSex(situ, path):
    if situ == "tb":
        age = 1
        sex = 0
    elif situ == "ex":
        age = getOrAsk(agebyExperimenter, path, "age")
        sex = getOrAsk(sexbyExperimenter, path, "sex")

    return age, sex


def getAgeSexHandedness(situ, path):
    if situ == "tb":
        age = 1
        sex = 0
        handedness = 3
    elif situ == "ex":
        age = getOrAsk(agebyExperimenter, path, "age")
        sex = getOrAsk(sexbyExperimenter, path, "sex")
        handedness = getOrAsk(handednessbyExperimenter, path, "handedness")

    return age, sex, handedness


def getSubjNum(situ):
    if situ == "tb":
        subject_n = numberSubjDay()
    elif situ == "ex":
        subject_n = numberSubjDay("y")

    return subject_n


##################################################################
###################### Saving data ##############################
################################################################


def writeValue(name, value):
    of = open(f"{name}", "w")
    of.write(str(value))
    of.close()


def tempSaving(path, header, temp_file_name="temp_data"):
    """
    Function to initiliase temporary file to store data in case the
    script fails
    """
    temp_file = open(f"{path}/{temp_file_name}.csv", "w")
    temp_data_writer = csv.writer(temp_file)
    temp_data_writer.writerow(header)
    temp_file.close()
    return [temp_data_writer, temp_file, temp_file_name]


def findTempFiles(path):
    """
    Function to find temporary files in folder
    """
    pattern = "^temp_"
    patternc = re.compile(pattern)
    names = []

    for filename in os.listdir(f"{path}"):
        if patternc.match(filename):
            # print(filename)
            name, form = filename.split(".")
            names.append((name, form))
        else:
            continue

    return names


def changeNameTempFile(path, outcome="failed"):
    """
    Function to change the name of the temporary files with current date and time.
    This functions should be placed in the except sections. It is triggered when the script fails
    """
    names = findTempFiles(path)
    t = time.localtime()
    time_now = time.strftime("%H_%M_%S", t)
    todaydate = date.today().strftime("%Y%m%d")
    for i, n in enumerate(names):
        temp_file_name = n[0].split("temp_", 1)[1]
        shutil.copyfile(
            f"{path}/{n[0]}.{n[1]}",
            f"./{path}/{temp_file_name}_{outcome}_{todaydate}_{time_now}.{n[1]}",
        )


############ apending to file with all subjects ############
def apendAll(folder, subj_n, data, file="data_all"):
    """
    Function to append participant's data to a csv file with the
    data with all the participants for an experiment.
    Data structure should be a dictionary. It can handle two levels of keys.
    """
    llaves = data.keys()
    one_key = [*llaves][0]
    subj_n = int(subj_n)

    of1 = open(f"{folder}/{file}.csv", "a")
    data_writer = csv.writer(of1)
    if type(data[one_key]) == list:

        if subj_n == 1:
            # print(subj_n)
            # print(llaves)
            data_writer.writerow(llaves)

        for i in np.arange(len(data[[*llaves][0]])):
            rowToWrite = []
            for j in llaves:
                datapoint = data[j][i]
                rowToWrite.append(datapoint)

            data_writer.writerow(rowToWrite)
    elif type(data[one_key]) == dict:
        one_array = data[[*llaves][0]]
        one_array_llaves = one_array.keys()
        # Headers if we are doing the first subject
        if subj_n == 1:
            rait = []
            for k, v in data.items():
                rait.append(k)
                empy = ""
                for i in np.arange((len(v) - 1)):
                    rait.append(empy)
            data_writer.writerow(rait)

            # We write the name of each data array n_condition times
            # This could be done above but we do it separately for clarity
            name_arrays = []
            for k, v in data.items():
                for c, b in v.items():
                    name_arrays.append(c)
            data_writer.writerow(name_arrays)

        # Write data
        for i in np.arange(len(one_array[[*one_array_llaves][0]])):
            rowToWrite = []
            for k, v in data.items():
                for c, b in v.items():
                    datapoint = data[k][c][i]
                    rowToWrite.append(datapoint)

            data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nData saved to CSV with all participants\n")


############# Individual files #############
def saveIndv(file, folder, data):
    """
    Function to save data of a participant to an individual file.
    Data structure should be a dictionary with one level of keys.
    """

    llaves = data.keys()
    one_key = [*llaves][0]

    of2 = open("{}/{}.csv".format(folder, file), "w")
    writer_subject = csv.writer(of2)

    if type(data[one_key]) == list:
        writer_subject.writerow(llaves)

        for i in np.arange(len(data[[*llaves][0]])):
            rowToWrite = []
            # print(type(llaves))
            for j in llaves:
                # print(type(data[j][i]))
                datapoint = data[j][i]
                rowToWrite.append(datapoint)

            writer_subject.writerow(rowToWrite)

    elif type(data[one_key]) == dict:
        one_array = data[[*llaves][0]]
        one_array_llaves = one_array.keys()
        # We write the name of each condition
        rait = []
        for k, v in data.items():
            rait.append(k)
            empy = k
            for i in np.arange((len(v) - 1)):
                rait.append(empy)
        writer_subject.writerow(rait)

        # We write the name of each data array n_condition times
        # This could be done above but we do it separately for clarity
        name_arrays = []
        for k, v in data.items():
            for c, b in v.items():
                name_arrays.append(c)
        writer_subject.writerow(name_arrays)

        for i in np.arange(len(one_array[[*one_array_llaves][0]])):
            rowToWrite = []
            for k, v in data.items():
                for c, b in v.items():
                    datapoint = data[k][c][i]
                    rowToWrite.append(datapoint)

            writer_subject.writerow(rowToWrite)

    of2.close()

    print(f"\nData saved to an individual CSV\n")


########################################################
############# Saving variables #########################
########################################################
############# SINGLE VARIABLE #############
def apendSingle(file, folder, subj_n, data_point):
    """
    Function to save a single value to a csv that contains
    more values from a given experiment.
    """

    of3 = open("{}/{}.csv".format(folder, file), "a")

    writer_subject = csv.writer(of3)
    writer_subject.writerow([subj_n, data_point])

    of3.close()


######## Saving Zaber


def saveZaberPos(file, path, data, header=["Zaber", "x", "y", "z"]):
    """
    Function to save one position of multiple Zaber sets
    """

    llaves = list(data.keys())
    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    data_writer.writerow(header)

    for i in llaves:
        rowToWrite = [i, data[i]["x"], data[i]["y"], data[i]["z"]]
        data_writer.writerow(rowToWrite)
    of1.close()

    print(f"\nZaber position saved\n")


######## Saving ROI
def saveROI(file, path, data, header=["Axis", "1"]):
    """
    Function to save one ROI centre
    """
    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    data_writer.writerow(header)
    rows = ["x", "y"]

    for i, r in enumerate(rows):
        rowToWrite = [r, data[i]]
        data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nROI position saved\n")


######## Saving Grid All
def saveGridAll(path, data, file="temp_grid"):
    """
    Function to save all grids
    """
    print(f"\nSaving grids in temporary file...\n")

    for i in data.keys():
        saveGridIndv(file, path, data, i)

    print(f"\nGrids saved in temporary file...\n")


######## Saving Grid Indv
def saveGridIndv(file, path, data, zaber):
    """
    Function to save grid of one Zaber
    """

    file = file + f"_{zaber}"

    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    header = [str(int(i)) for i in list(data[zaber].keys())]
    header.insert(0, "Axis")

    data_writer.writerow(header)
    rows = ["x", "y", "z"]

    for i, r in enumerate(rows):
        rowToWrite = [r]
        rowToWrite.extend(
            [data[zaber][str(int(x))][r] for x in list(data[zaber].keys())]
        )
        data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nGrid position of {zaber} saved\n")


######## Saving ALL ROI centres
def saveROIAll(path, data, file="temp_ROIs"):
    """
    Function to save all ROI centres of a grid
    """

    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    grid_i = list(np.arange(1, len(data) + 0.1))
    header = [str(int(i)) for i in grid_i]
    header.insert(0, "Axis")

    data_writer.writerow(header)
    rows = ["x", "y"]

    for i, r in enumerate(rows):
        rowToWrite = [r]
        rowToWrite.extend([data[str(int(x))][i] for x in grid_i])
        data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nROI position saved\n")


def savePanTiltAll(path, data, file="temp_PanTilts"):
    """
    Function to save all ROI centres of a grid
    """

    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    grid_i = list(np.arange(1, len(data) + 0.1))
    header = [str(int(i)) for i in grid_i]
    header.insert(0, "Axis")

    data_writer.writerow(header)
    rows = ["x", "y", "z"]

    for i, r in enumerate(rows):
        rowToWrite = [r]
        rowToWrite.extend([data[str(int(x))][i] for x in grid_i])
        data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nROI position saved\n")


######## Saving ALL haxes
def saveHaxesAll(path, data, file="temp_haxes"):
    """
    Function to save all ROI centres of a grid
    """

    of1 = open(f"{path}/{file}.csv", "w")
    data_writer = csv.writer(of1)

    header = list(data.keys())
    header.insert(0, "Position")

    data_writer.writerow(header)
    rows = ["1", "2", "3"]

    for i, r in enumerate(rows):
        rowToWrite = [r]
        rowToWrite.extend([data[x][i] for x in data.keys()])
        data_writer.writerow(rowToWrite)

    of1.close()

    print(f"\nHaxes saved\n")


def handle_iti_save(temp_row, data, path, file_name):
    data = appendDataDict(data, temp_row)
    temp_file = open(f"{path}/{file_name}.csv", "a")
    temp_data_writer = csv.writer(temp_file)
    temp_data_writer.writerow(temp_row)
    temp_file.close()

    return data


########################################################
################## PERMISSIONS #########################
########################################################


def rootToUser(*paths):
    pwd = os.getcwd()
    print(f"\nCurrent directory is: {pwd}\n")
    paths = [*paths]

    path = os.path.realpath(__file__)
    root_path = path.rsplit("/", 1)[0]

    for i in paths:
        os.chdir(i)
        subprocess.call([f"{root_path}/brapper.sh", root_path])
        print(f"\nChanged permissions of following path: {i}\n")
        os.chdir(pwd)


#################################################################
########## Pipeline to check & create folder architecture #######
#################################################################


def tbORtesting(testing):
    """
    Function to check whether we are testing with a participant or troubleshooting the experiment
    """
    if testing in ("y", "n"):
        if testing == "n":
            printme("You are troubleshooting")
        else:
            printme("We are testing a participant")
    else:
        raise Exception("Variable 'testing' can only take values 'y' or 'n'.")


def checkORcreate(path):
    """
    Function to check whether a folder exists.
    If it does NOT exist, it is created
    """
    folder_name = os.path.split(path)[1]
    if not os.path.isdir(path):
        print(f"\nFolder '{folder_name}' does NOT exist, creating it for you...\n")
        os.mkdir(path)
    else:
        print(f"\nFolder '{folder_name}' exists, ready to continue...\n")
    return path


def substring_exists(substring, string):
    if substring in string:
        return True
    else:
        return False


def depthToSrc():
    """
    Function to check how deep we are with respect to src_testing
    """
    path = os.path.abspath(os.getcwd())
    print(f"Current working directory: {path}")
    backwardsUnit = "../"
    backwards = "../"
    while True:
        splitted = os.path.split(path)
        if splitted[1] == "src_testing":
            backwards = "../"
            break
        elif splitted[0] == "/":
            backwards = "./"
            break
        elif substring_exists("expt", splitted[-1]):
            backwards = ""
            break
        else:
            backwards = backwards + backwardsUnit
            path = splitted[0]

    return backwards


def folderData(backs):
    """
    Function to check whether the folder data exists.
    If the folder doesn't exist it is created automatically
    """
    path = f"./{backs}data"

    path_anal = checkORcreate(path)

    return path_anal


def numberSubjDay(testing="n"):
    if testing == "y":
        head_folder_name = "ex"

    elif testing == "n":
        head_folder_name = "tb"

    backwards = depthToSrc()

    todaydate = date.today().strftime("%Y%m%d")
    folder_name = f"{head_folder_name}_" + todaydate + "_"

    patternf = re.compile(folder_name)
    # print(patternf)
    nums = []

    for foldername in os.listdir(f"./{backwards}data/"):
        # print(foldername)
        if patternf.match(foldername):
            # print(foldername)
            # name = foldername.split('_')
            nums.append(foldername[-1])
        else:
            continue

    nums = sorted(nums, reverse=False)
    print(nums)
    if len(nums) >= 1:
        numdaysubj = int(nums[-1])
    else:
        numdaysubj = 0

    return numdaysubj + 1


def folderTesting(path, testing, numdaysubj=None, existing_folder_name=None):
    """
    Function to check whether the folder to save the data today exists.
    If the folder does't exist it is created automatically
    """
    if testing == "y":
        head_folder_name = "ex"

    elif testing == "n":
        head_folder_name = "tb"

    if not existing_folder_name:
        todaydate = date.today().strftime("%Y%m%d")
        folder_name = head_folder_name + "_" + todaydate + "_" + str(numdaysubj)
        path = path + "/" + folder_name
    else:
        folder_name = head_folder_name + "_" + existing_folder_name
        path = path + "/" + folder_name

    path = checkORcreate(path)

    return path


def folderDataLocalFigs(path):
    path_figs = path + "/" + "figures"
    path_figs = checkORcreate(path_figs)

    path_datalocal = path + "/" + "data"
    path_datalocal = checkORcreate(path_datalocal)

    return [path_figs, path_datalocal]


def folderChreation(numdaysubj=None, testing="n", folder_name=None):
    """
    Function of functions to check whether we have all the folder architecture in place to save data and figures.
    """
    print(testing)
    tbORtesting(testing)
    steps_back = depthToSrc()
    path_data = folderData(steps_back)
    path_day = folderTesting(path_data, testing, numdaysubj, folder_name)
    path_figs, path_datalocal = folderDataLocalFigs(path_day)

    return [path_day, path_data, path_figs, path_datalocal]


def folderVideos(path):
    """
    Function to check whether the folder videos exists.
    If the folder doesn't exist it is created automatically
    """

    path_video = path + "/" + "videos"
    path_video = checkORcreate(path_video)

    return path_video


def folderVhrideos(numdaysubj, testing="n", folder_name=None):
    """
    Function of functions to check whether we have all the folder architecture in place to save videos.
    """
    steps_back = depthToSrc()
    path_data = folderData(steps_back)
    path_day = folderTesting(path_data, testing, numdaysubj, folder_name)
    path_video = folderVideos(path_day)

    return path_video


def folderAudios(path):
    """
    Function to check whether the folder videos exists.
    If the folder doesn't exist it is created automatically
    """

    path_audio = path + "/" + "audios"
    path_audio = checkORcreate(path_audio)

    return path_audio


def folderArudio(numdaysubj, testing="n", folder_name=None):
    """
    Function of functions to check whether we have all the folder architecture in place to save videos.
    """
    steps_back = depthToSrc()
    path_data = folderData(steps_back)
    path_day = folderTesting(path_data, testing, numdaysubj, folder_name)
    path_audio = folderAudios(path_day)

    return path_audio


def rm_mk_folder_name(path_day):
    if os.path.exists(f"./src_testing/temp_folder_name.txt"):
        os.remove(f"./src_testing/temp_folder_name.txt")

    saveIndvVar("./src_testing/", path_day, "temp_folder_name")


#################################################################
########## Pipeline to set subject number & others ##############
#################################################################


def setSubjNum(file_pattern="data_subj_(.*).csv", folder_pattern="ex_(.)"):
    """
    Function to set the number of the subject automatically
    """
    patternc = re.compile(file_pattern)
    patternf = re.compile(folder_pattern)
    names = []
    subjs = []

    for foldername in os.listdir(f"./../../data/"):
        if patternf.match(foldername):
            for filename in os.listdir(f"./../../data/{foldername}/data/"):
                if patternc.match(filename):
                    print(filename)
                    name, form = filename.split(".")
                    names.append(filename)
                    r = patternc.search(filename)
                    subjs.append(int(r.group(1)))
                else:
                    continue

    if len(subjs) < 1:
        subject_n = 1
    else:
        subjs.sort()
        subject_n = subjs[-1] + 1

    return subject_n


def saveIndvVar(path, var, file_name):
    """
    Function to save subject number in temporary file
    """
    with open(f"{path}/{file_name}.txt", "w") as f:
        f.write(str(var))


def txtToVar(path, file):
    """
    Function to recover subject number in temporary files
    """
    with open(f"{path}/{file}.txt", "r") as f:
        var = f.readline()
    return var


def create_temp_name(name):
    t = time.localtime()
    time_now = time.strftime("%H_%M_%S", t)
    todaydate = date.today().strftime("%Y%m%d")
    name_temp_file = f"{name}_temp_{time_now}_{todaydate}"
    return name_temp_file


#################################################################
######################## Reading from CSV #######################
#################################################################


def getOrAsk(func, path, file_name):
    if os.path.exists(f"{path}/{file_name}.csv"):
        value = getValue(path, file=f"{file_name}")
    else:
        value = func()

    return value


def csvtoDictZaber(path, file="temp_zaber_pos.csv"):
    """
    Transforming csv of one set of  Zabers to dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Zaber")
    dictfromcsv = {}

    for i in df.index.values:
        dictfromcsv[i] = {}

    for colu in df.columns:
        # print(colu)
        for r in df[colu].index.values:
            dictfromcsv[r][colu] = df[colu][r]

    return dictfromcsv


def csvToDictPanTiltsAll(path, file="temp_PanTilts.csv"):
    """
    Transforming csv of all ROIs to a dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Axis")
    PanTilts = df.to_dict()

    for i in PanTilts:
        PanTilts[i] = PanTilts[i]["x"], PanTilts[i]["y"], PanTilts[i]["z"]

    return PanTilts


def csvToDictROI(path, file="temp_ROI.csv"):
    """
    Transforming csv of one ROI to a dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Axis")
    cd = df.to_dict()
    centreROI = cd["1"]["x"], cd["1"]["y"]
    return centreROI


def getValue(path, file="age.csv"):
    """
    Get single value age from csv file
    """
    dataframe = pd.read_csv(f"{path}/{file}", header=None)
    value = dataframe[1][0]
    return value


def csvToDictGridAll(path, file_pattern="temp_grid_(.*).csv"):

    patternc = re.compile(file_pattern)
    names = []
    zabers = []

    for filename in os.listdir(f"{path}"):
        if patternc.match(filename):
            name, form = filename.split(".")
            names.append(filename)
            r = patternc.search(filename)
            zabers.append(r.group(1))
        else:
            continue

    grid = {}
    for n, z in zip(names, zabers):
        grid[z] = csvToDictGridIndv(path, n)

    return grid


def csvToDictGridIndv(path, file):
    """
    Transforming csv of one Grid to a dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Axis")

    grid_indv = df.to_dict()
    return grid_indv


def csvToDictROIAll(path, file="temp_ROIs.csv"):
    """
    Transforming csv of all ROIs to a dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Axis")

    ROIs = df.to_dict()

    for i in ROIs:
        ROIs[i] = ROIs[i]["x"], ROIs[i]["y"]

    return ROIs


def csvToDictHaxes(path, file="temp_haxes.csv"):
    """
    Transforming csv of haxes to a dictionary
    """
    df = pd.read_csv(f"{path}/{file}", index_col="Position")

    haxes = df.to_dict()

    for i in haxes:
        haxes[i] = [haxes[i][1], haxes[i][2], haxes[i][3]]

    return haxes


def check_file_path_save(path, file_name, variable, subject_n, format="csv"):
    if not os.path.exists(f"{path}/{file_name}.{format}"):
        apendSingle(file_name, path, subject_n, variable)


#################################################################
######################## Deleting ###############################
#################################################################


def delTempFiles(path):
    """
    Function to delete temporary files
    """
    names = findTempFiles(path)

    for i, n in enumerate(names):
        os.remove(f"{path}/{n[0]}.{n[1]}")

    print("Temporary data file Removed!")

#################################################################
######################## Globals ################################
#################################################################

def globalsToDict(globals):
    all_globals = {}
    for d in dir(globals):
        if type(d) is not None:
            print(globals.__dict__[d])
            if "__" not in d:
                all_globals[d] = [globals.__dict__[d]]
    return all_globals

import ast
def recoverGlobals(path, name_file='all_globals'):
    """
        Function to recover globals from a file
    """
    pd_globals = pd.read_csv(f"{path}/{name_file}.csv")
    dict_globals = pd_globals.to_dict(orient='records')[0]
    for key, value in dict_globals.items():
        if type(value) is str:
            try:
                dict_globals[key] = ast.literal_eval(value)
            except:
                pass
    return dict_globals
