import re
import os
import numpy as np
import h5py


class ReAnRaw(object):
    """Grab h5py file. Don't include format in string"""

    def __init__(self, input):
        "We get the data from the h5py files, then we find the parameters used."

        self.read = h5py.File("{}.hdf5".format(input), "r")

        self.parameters = []

        for i in self.read.keys():
            self.parameters.append(re.split("(\d+)", i)[0])

        self.parameters = list(set(self.parameters))

        self.data = {}
        self.metadata = {}

        for p in self.parameters:
            self.data[p] = []

        print("These are the parameters measured in this thermal video")
        print(self.parameters)

    def datatoDic(self):
        "Transform videos data into a dictionary"

        self.len_subto = len(self.read.keys()) / len(self.parameters)

        for index, parameter in enumerate(self.parameters):
            for j in np.arange(self.len_subto):
                temp_parameter_name = f"{parameter}" + str(int(j))
                if temp_parameter_name in self.read:
                    try:
                        if len(self.read[temp_parameter_name].shape) > 0:
                            frame_da = self.read[temp_parameter_name][:]
                            self.data[parameter].append(frame_da)
                        else:
                            print(f"Length of parameter data {temp_parameter_name} is smaller or equal to 0 ")
                    except:
                        print("No data for parameter {}".format(temp_parameter_name))
                else:
                    print("No data for parameter {}".format(temp_parameter_name))

    def attrstoDic(self):
        "Transform videos attributes into a dictionary"
        for attribute_key in self.read.attrs.keys():
            self.metadata[attribute_key] = self.read.attrs[attribute_key]

    def extractOpenClose(self, name):
        shus = np.asarray(self.data[name])
        self.open = np.where(shus[:-1] != shus[1:])[0]

    def extractMeans(self, name_image="image", name_coor="fixed_coor", r=20):
        """
        Method to extract mean of ROI (default: fixed_coor)
        """

        self.min_pixel = []
        self.means = []
        self.surround = []

        for i in np.arange(len(self.data[name_image])):

            minimoC = np.min(self.data[name_image][i])

            xs = np.arange(0, 160)
            ys = np.arange(0, 120)

            # print(self.data[name_coor][i])

            try:
                shape = np.shape(self.data[name_coor][i])[1]
                # print(shape)
                cs = self.data[name_coor][i][:, 0]
                cy = cs[1]
                cx = cs[0]
            except:
                cs = self.data[name_coor][i]
                cy = cs[1]
                cx = cs[0]

            mask = (xs[np.newaxis, :] - cy) ** 2 + (
                ys[:, np.newaxis] - cx
            ) ** 2 < r ** 2

            roiC = self.data[name_image][i][mask]
            mean = round(np.mean(roiC), 2)

            unmask = np.invert(mask)
            unroiC = self.data[name_image][i][unmask]
            meanSU = round(np.mean(unroiC), 2)

            self.means.append(mean)
            self.min_pixel.append(minimoC)
            self.surround.append(meanSU)


########################################################################
############ Functions Miscellaneous
#########################################################################


def GrabNamesOrder(pattern, folder):
    """Get the file names with a given pattern in order
    Example pattern: '^m2_([0-9]+)_mof'
    """
    pattern = re.compile(pattern)
    names = []    

    for filename in os.listdir("{}".format(folder)):
        if pattern.match(filename):
            names.append(filename)
        else:
            continue
    names.sort(key=natural_keys)

    return names


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def grabManyvideos(root_path, folder_name, pattern="mol_.*\.hdf5$"):
    """
    pattern for SDT videos f'sdt_.*\.hdf5$'
    """

    patternc = re.compile(pattern)
    names = []

    for filename in os.listdir(f"{root_path}/{folder_name}/videos/"):
        if patternc.match(filename):
            # print(filename)
            name, form = filename.split(".")
            names.append(name)
        else:
            continue

    names.sort(key=natural_keys)
    print(names)
    return names


def pairwise(vs):
    it = iter(vs)
    while True:
        try:
            yield next(it), next(it)
        except StopIteration:
            if len(vs) % 2 != 0:
                yield vs[-1], None
            return

def saveMetadata(metadata, file):
    for k, v in metadata.items():
        file.attrs[f"{k}"] = v


def init_h5file(path, name_file):
    f = h5py.File(f"{path}/{name_file}.hdf5", "w")
    return f