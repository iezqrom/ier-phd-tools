import csv
import numpy as np
import os
import time
from datetime import date


##################################################################
###################### Saving data ##############################
################################################################

############ apending to file with all subjects ############
def apendAll(file, folder, subj_n, data):
    llaves = data.keys()
    one_key = [*llaves][0]

    of1 = open('./{}/{}.csv'.format(folder, file), 'a')
    data_writer = csv.writer(of1)
    if type(data[one_key]) == list:

        if subj_n == 1:
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
                empy = ''
                for i in np.arange((len(v) -1)):
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



############# Individual files #############
def saveIndv(file, folder, data):
    """
    Example data:


    """

    llaves = data.keys()
    one_key = [*llaves][0]

    of2 = open('./{}/{}.csv'.format(folder, file), 'w')
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


############# Age files #############
def apendSingle(file, folder, subj_n, data_point):

    of3 = open('./{}/{}.csv'.format(folder, file), 'a')

    writer_subject = csv.writer(of3)
    writer_subject.writerow([subj_n, data_point])

    of3.close()

#################################################################
########## Pipeline to check & create folder architecture #######
#################################################################

def tbORtesting(testing):
    """
        Function to check whether we are testing with a participant or troubleshooting the experiment
    """
    if testing in ('y', 'n'):
        if testing == 'n':
            print('You are troubleshooting')
        else:
            print('We are testing a participant')
    else:
        raise Exception("Variable 'testing' can only take values 'y' or 'n'.")

def checkORcreate(path):
    """
        Function to check whether a folder exists.
        If it does NOT exist, it is created
    """
    print(path)
    folder_name = os.path.split(path)[1]
    if not os.path.isdir(path):
        print(f"\nFolder '{folder_name}' does NOT exist, creating it for you...\n")
        os.mkdir(path) 
    else:
        print(f"\nFolder '{folder_name}' exists, ready to continue...\n")
    return path

def depthToSrc():
    """
        Function to check how deep we are with respect to src_testing
    """
    path = os.path.abspath(os.getcwd())
    print(f"Current working directory: {path}")
    backwardsUnit = '../'
    backwards = '../'
    while True:
        splitted = os.path.split(path)
        if splitted[1] == 'src_testing':
            break
        elif splitted[0] == '/':
            raise Exception("Can't find folder 'src_testing' in folder tree")
        else:
            backwards = backwards + backwardsUnit
            path = splitted[0]

    return backwards

def folderAnalysis(backs):
    """
        Function to check whether the folder src_analysis exists.
        If the folder doesn't exist it is created automatically
    """
    path = f"./{backs}src_analysis"
    
    path_anal = checkORcreate(path)

    return path_anal

def folderTesting(path, testing):
    """
        Function to check whether the folder to save the data today exists.
        If the folder does't exist it is created automatically
    """
    if testing == 'y':
        head_folder_name = 'test'
    
    elif testing == 'n':
        head_folder_name = 'tb'

    todaydate = date.today().strftime("%d%m%Y")
    folder_name = head_folder_name + "_" + todaydate
    path = path + "/" + folder_name

    path = checkORcreate(path)
  
    return path

def folderDataFigs(path):
    path_figure = path + "/" + 'figures'
    path_figure = checkORcreate(path_figure)

    path_data = path + "/" + 'data'
    path_data = checkORcreate(path_data)

    return [path_figure, path_data]


def folderChreation(testing = 'n'):
    """
        Function of functions to check whether we have all the folder architecture in place.
    """
    tbORtesting(testing)
    steps_back = depthToSrc()
    path_anal = folderAnalysis(steps_back)
    path_day = folderTesting(path_anal, testing)
    path_figs, path_data = folderDataFigs(path_day)

    return [path_figs, path_data]



###### OLD TRASH

# def apendIndv(indv_file, subj_n, data):
#     llaves = data.keys()
#
#     of2 = open('../src_analysis/data/{}.csv'.format(indv_file), 'w')
#     writer_subject = csv.writer(of2)
#
#     writer_subject.writerow(llaves)
#
#     for i in np.arange(len(data[[*llaves][0]])):
#         rowToWrite = []
#         for j in llaves:
#             datapoint = data[j][i]
#             rowToWrite.append(datapoint)
#
#         writer_subject.writerow(rowToWrite)
#
#     of2.close()

# def apendAll(name_file, subj_n, data):
#     llaves = data.keys()
#     of1 = open('../src_analysis/data/{}.csv'.format(name_file), 'a')
#     data_writer = csv.writer(of1)
#
#     if subj_n == '1':
#         data_writer.writerow(llaves)
#
#     for i in np.arange(len(data[[*llaves][0]])):
#         rowToWrite = []
#         for j in llaves:
#             datapoint = data[j][i]
#             rowToWrite.append(datapoint)
#
#         data_writer.writerow(rowToWrite)
#
#     of1.close()
