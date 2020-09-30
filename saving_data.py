import csv
import numpy as np


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
