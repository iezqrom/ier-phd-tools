import csv
import numpy as np


##################################################################
###################### Saving data ##############################
################################################################

############ apending to file with all subjects ############
def apendAll(name_file, subj_n, data):
    llaves = data.keys()
    of1 = open('./src_analysis/data/{}.csv'.format(name_file), 'a')
    data_writer = csv.writer(of1)

    if subj_n == '1':
        print('We are here')
        data_writer.writerow(llaves)

    for i in np.arange(len(subject[[*keys][0]])):
        rowToWrite = []
        for j in llaves:
            datapoint = subject[j][i]
            rowToWrite.append(datapoint)

        data_writer.writerow(rowToWrite)

    of1.close()



############# Individual files #############
def apendIndv(indv_file, subj_n, data):
    llaves = data.keys()

    of2 = open('./src_analysis/data/{}.csv'.format(indv_file), 'w')
    writer_subject = csv.writer(of2)

    writer_subject.writerow(llaves)

    for i in np.arange(len(subject[[*keys][0]])):
        rowToWrite = []
        for j in llaves:
            datapoint = subject[j][i]
            rowToWrite.append(datapoint)

        data_writer.writerow(rowToWrite)

    of2.close()

############# Age files #############
def apendAge(age_file, subj_n, age):

    of3 = open('./src_analysis/data/{}.csv', 'a')

    writer_subject = csv.writer(of3)
    writer_subject.writerow([subj_n, age])

    of3.close()
