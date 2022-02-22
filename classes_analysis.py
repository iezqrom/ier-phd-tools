####### Analysis for experiments with thermodes


class analyseTTT(ploTTT):
    # def __init__(self):
    #     ploTTT.__init__(self, file, subject)

    @staticmethod
    def QQplot(file, distribution, parameters, path_qq, name_qq, range):
        percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs.append(sub_data.perCorrect)

        theor = []
        dataD = []

        for i in np.arange(len(percs_indvs)):
            theor.append(
                cdfProbPlot(percs_indvs[i], dist=distribution, sparams=parameters)[0]
            )
            dataD.append(
                cdfProbPlot(percs_indvs[i], dist=distribution, sparams=parameters)[1]
            )

        subs = 1

        fig = plt.figure(figsize=(10, 10), facecolor="w")

        for i in np.arange(len(percs_indvs)):
            ax = fig.add_subplot(4, 2, subs)
            ax.plot(
                theor[i][0],
                theor[i][1],
                "bo",
                theor[i][0],
                dataD[i][0] * theor[i][0] + dataD[i][1],
                "r",
            )
            ax.set_xlabel("Theoretical quantiles")
            ax.set_ylabel("Data quantiles")
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            subs += 1

        fig.legend(["Fit", "Perfect fit"])
        plt.suptitle("Distribution of {}: {}".format(range, distribution))
        plt.subplots_adjust(top=2)
        plt.ylim([50, 100])
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        plt.savefig("./{}/{}.svg".format(path_qq, name_qq), transparent=True)

        return [percs_indvs, theor, dataD]

    def linearFit(self):
        self.s, self.i = np.polyfit(self.rates, self.perCorrect, 1)
        self.y_line = self.s * self.rates + self.i

    def plotLinearFit(self, color, title, path_fit, name_fit, save="Y"):
        fig, ax = plt.subplots(1, 1)
        plt.plot(
            self.rates,
            self.perCorrect,
            "-{}".format(color),
            self.rates,
            self.y_line,
            "--{}".format(color),
        )

        plt.ylim([50, 100])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.hlines(y=75, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
        plt.xticks(self.rates)
        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.text(0.2, 55, "Slope:  " + str(round(self.s)))
        plt.text(0.2, 51, "Intercept: " + str(round(self.i)))
        plt.title(title)

        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path_fit, name_fit), transparent=True)

    def bootstrapping(self, file, function, revolts, bootedObvs):
        self.revolts = revolts
        self.percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                self.percs_indvs.append(sub_data.bootedObvs)

        self.BS_samples = []

        for i in np.arange(revolts):
            bootstrapped_sample = skl.utils.resample(self.percs_indvs, n_samples=8)
            BS_array = np.asarray(bootstrapped_sample)
            BS_mean = function(bootstrapped_sample, axis=0)
            self.BS_samples.append(BS_mean)

        self.funced_BS = np.mean(self.BS_samples, axis=0)

    def plotBoot(
        self,
        title,
        path,
        name,
        color_funced,
        color_parent,
        functionApplied,
        alpha=0.03,
        save="Y",
    ):

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, "-{}".format(color_funced))
        ax.plot(self.rates, self.perCorrect, "-{}".format(color_parent))

        for L in self.BS_samples:
            ax.plot(self.rates, L, color="#4D4B50", alpha=alpha)

        plt.legend(
            [
                "Bootstrapped {}".format(functionApplied),
                "Parent data",
                "Bootstrapped samples",
            ]
        )
        plt.ylim([50, 100])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.title(title)
        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.xticks(self.rates)

        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    # Here we get the slopes of all bootstrapped samples
    def slopBoot(self):

        self.s_indvs = []
        self.i_indvs = []

        for i in np.arange(len(self.BS_samples)):
            s_dummy, i_dummy = np.polyfit(self.rates, self.BS_samples[i], 1)
            self.s_indvs.append(s_dummy)
            self.i_indvs.append(i_dummy)

    # Here we plot the linear fit to all our bootstrapped samples
    def plotSlop(
        self,
        title,
        path,
        name,
        color_funced,
        color_parent,
        functionApplied,
        alpha=0.03,
        save="Y",
    ):

        self.y_line_indvs = []

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, "-{}".format(color_funced))
        ax.plot(self.rates, self.perCorrect, "-{}".format(color_parent))

        for i in np.arange(len(self.s_indvs)):
            self.y_line_indvs.append(self.s_indvs[i] * self.rates + self.i_indvs[i])
            ax.plot(self.rates, self.y_line_indvs[i], "--", alpha=alpha)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([50, 100])

        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.xticks(self.rates)

        plt.legend(
            [
                "Bootstrapped {}".format(functionApplied),
                "Parent data",
                "Bootstrapped samples",
            ]
        )
        plt.title(title)
        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    def CIBoot(self, data, lowBound, highBound):
        self.sorted_data = np.sort(data)

        self.lowCI = self.sorted_data[
            np.round(self.revolts * (lowBound / 100) / 2).astype(int)
        ]
        self.highCI = self.sorted_data[
            np.round(self.revolts * (highBound / 100) / 2).astype(int)
        ]

    @staticmethod
    def CIdifff(data1, data2, lowBound, highBound, revolts):
        data1 = np.asarray(data1)
        data2 = np.asarray(data2)
        bootdiff = np.subtract(data1, data2)
        sorted_bootdiff = np.sort(bootdiff)

        ci_diff = (
            sorted_bootdiff[np.round(revolts * (lowBound / 100) / 2).astype(int)],
            sorted_bootdiff[np.round(revolts * (highBound / 100) / 2).astype(int)],
        )

        return ci_diff, bootdiff

    @staticmethod
    def pValueBoots(
        data1, data2, obvs_value, revolts, round_place, function, args=None, x=[]
    ):
        eng = me.start_matlab()

        pooled = np.append(data1, data2)
        bs_samples = []

        for i in np.arange(10000):
            bootstrapped_sample = skl.utils.resample(
                pooled, n_samples=(len(data1) + len(data2))
            )
            BS_array = np.asarray(bootstrapped_sample)
            bs_1 = BS_array[0 : len(data1)]
            bs_2 = BS_array[len(data1) : (len(data1) + len(data1))]

            if function == np.polyfit:
                s_1, i_1 = function(x, bs_1, args)
                s_2, i_2 = function(x, bs_2, args)

            if function == eng.nonParamAnalysis:

                [xfit, pfit, threshold, s_1, sd_th, sd_sl] = eng.nonParamAnalysis(
                    x, nargout=6
                )
                [xfit, pfit, threshold, s_2, sd_th, sd_sl] = eng.nonParamAnalysis(
                    x, nargout=6
                )

            bs_s = s_1 - s_2
            bs_samples.append(bs_s)

        thres_values = [i for i in bs_samples if i >= obvs_value]

        p_value = round((len(thres_values) + 1) / (revolts + 1), round_place)

        return p_value

    @staticmethod
    def poolST(data1, data2):
        pooled = []
        for i, j in zip((data1, data2)):
            temp = np.array([i, j])
            pooled.append(temp)

    def timePerformance(self, exclude=None):

        self.hits_time = []
        for i in np.arange(max(self.RawData["n_subject"])):
            if i == exclude:
                pass
            else:
                temp_subset = self.RawData.loc[self.RawData["n_subject"] == i + 1]
                # print(temp_subset)
                self.hits_time.append(temp_subset["grade"])
                self.grade_t = np.mean(np.asarray(self.hits_time), axis=0)

    def AUCPerformance(self, n_chunks):
        self.AUC_chunks = []
        self.n_chunks = n_chunks
        self.chunks = np.split(self.grade_t, n_chunks)
        self.AUCS = np.empty(n_chunks)

        for i in np.arange(n_chunks):
            self.AUCS[i] = np.trapz(self.chunks[i])

        for i in np.arange(len(self.hits_time)):
            dummy_chunk = np.split(self.hits_time[i], n_chunks)
            dummy_AUCs = np.empty(n_chunks)

            for i in np.arange(len(dummy_chunk)):
                dummy_AUCs[i] = np.trapz(dummy_chunk[i])

            self.AUC_chunks.append(dummy_AUCs)

    def AUCPlot(self, path, name, color, min_y, max_y, title=None):

        fig, ax = plt.subplots(1, 1)
        ax.plot(
            np.arange(1, len(self.AUCS) + 0.1, step=1), self.AUCS, "-{}".format(color)
        )

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([min_y, max_y])
        plt.xlim([1, self.n_chunks])

        for i in np.arange(len(self.hits_time)):
            ax.plot(
                np.arange(1, len(self.AUCS) + 0.1, step=1),
                self.AUC_chunks[i],
                color="k",
                alpha=0.1,
            )

        plt.xticks(np.arange(1, self.n_chunks + 0.1, step=1))
        plt.xlabel("Periods")
        plt.ylabel("AUC")

        # plt.title(title)
        plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    def jackKnifeNonParametric(self, file, repeats, me):
        # import matlab.engine as me
        percs_indvs_T = []
        eng = me.start_matlab()

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs_T.append(sub_data.sf)

        self.n_T = len(percs_indvs_T)
        self.indexT = np.arange(self.n_T)

        self.xfit_jkT = []
        self.pfit_jkT = []
        self.threshold_jkT = []
        self.slopes_jkT = []
        self.sd_th_jkT = []
        self.sd_sl_jkT = []

        percs_indvs_T = np.asarray(percs_indvs_T)

        for i in range(self.n_T):
            jk_sampleT = percs_indvs_T[self.indexT != i]
            summed_jkT = np.sum(jk_sampleT, axis=0)
            summed_jkT = np.ndarray.tolist(summed_jkT)
            summed_jkT = [float(i) for i in summed_jkT]

            [xfitT, pfitT, thresholdT, slopeT, sd_thT, sd_slT] = eng.nonParamAnalysis(
                self.ratesLf, summed_jkT, repeats, nargout=6
            )

            self.xfit_jkT.append(xfitT)
            self.pfit_jkT.append(pfitT)
            self.threshold_jkT.append(thresholdT)
            self.slopes_jkT.append(slopeT)
            self.sd_th_jkT.append(sd_thT)
            self.sd_sl_jkT.append(sd_slT)

    def plotJKs(
        self,
        color_data,
        color_nonPar,
        title=None,
        alpha=0.05,
        save="Y",
        path=None,
        name=None,
    ):
        fig, ax = plt.subplots(1, 1)
        self.meaned_nonParametric = np.mean(self.pfit_jkT, axis=0)
        ax.plot(self.rates, self.perCorrect / 100, "-{}".format(color_data))
        ax.plot(self.xfit_jkT[0], self.meaned_nonParametric, "-{}".format(color_nonPar))

        for i in np.arange(len(self.pfit_jkT)):
            ax.plot(self.xfit_jkT[i], self.pfit_jkT[i], "--", alpha=alpha)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([0.5, 1])
        plt.xlim([0.100, 0.333])

        plt.ylabel("% correct")
        plt.xlabel("Hz")
        plt.xticks(self.rates)

        plt.legend(["Original data", "Mean jack-knife", "Jack-knife samples"])
        plt.title(title)
        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)


################################################################################
################################ Functions ######################################
################################################################################


def cdfProbPlot(x, dist, sparams=()):
    x = np.asarray(x)

    osm_uniform = st.morestats._calc_uniform_order_statistic_medians(len(x))
    dist = st.morestats._parse_dist_kw(dist, enforce_subclass=False)
    if sparams is None:
        sparams = ()
    if isscalar(sparams):
        sparams = (sparams,)
    if not isinstance(sparams, tuple):
        sparams = tuple(sparams)

    osm = dist.ppf(osm_uniform, *sparams)
    osr = sort(x)

    # perform a linear least squares fit.
    slope, intercept, r, prob, sterrest = stats.linregress(osm, osr)

    return (osm, osr), (slope, intercept, r)


def cdfplot(theor, data, path_qq, name_qq, range, distribution):

    fig, ax = plt.subplots(1, 1)
    plt.plot(theor[0], theor[1], "bo", theor[0], data[0] * theor[0] + data[1], "r")
    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Data quantiles")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    fig.legend(["Fit", "Perfect fit"])
    plt.title("Distribution of {}: {}".format(range, distribution))
    plt.subplots_adjust(top=2)
    plt.ylim([50, 100])
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig("./{}/{}.svg".format(path_qq, name_qq), transparent=True)

    return


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


class ploTTT:
    def __init__(self, file, subject):
        self.RawData = pd.read_csv(file)
        # print(len(self.RawData))
        self.RawData = self.RawData.dropna()
        self.Nsample = str(len(self.RawData["correct"]))

        if subject == "all":
            self.subject = subject
            pass
        else:
            self.RawData = self.RawData.loc[self.RawData["n_subject"] == subject]
            self.subject = str(subject)

    def exclude(self, who_out):
        for i in who_out:
            # print(i)
            self.RawData = self.RawData[self.RawData.n_subject != i]

        self.who_out = who_out

    def correctTGO(self):
        self.iso_phase = self.RawData.loc[self.RawData["phase"] == 0]
        self.aniso_phase = self.RawData.loc[self.RawData["phase"] > 3]

        self.iso_grade = pd.value_counts(self.iso_phase["grade"].values, sort=False)
        self.iso_trials = len(self.iso_phase)
        self.iso_correct = self.iso_grade[1] / self.iso_trials

        self.aniso_grade = pd.value_counts(self.aniso_phase["grade"].values, sort=False)
        self.aniso_trials = len(self.aniso_phase)
        self.aniso_correct = self.aniso_grade[1] / self.aniso_trials

        self.perCorrect = np.array([self.iso_correct, self.aniso_correct]) * 100

        if self.subject == "all":
            self.participants = self.RawData["n_subject"].unique()
            self.perPartIso = []
            self.perPartAniso = []

            for i in self.participants:

                self.RawPart = self.RawData.loc[self.RawData["n_subject"] == i]

                self.iso_phasePart = self.RawPart.loc[self.RawPart["phase"] == 0]
                self.aniso_phasePart = self.RawPart.loc[self.RawPart["phase"] > 3]

                self.iso_gradePart = pd.value_counts(
                    self.iso_phasePart["grade"].values, sort=False
                )
                self.iso_trialsPart = len(self.iso_phasePart)
                self.iso_correctPart = self.iso_gradePart[1] / self.iso_trialsPart

                self.aniso_gradePart = pd.value_counts(
                    self.aniso_phasePart["grade"].values, sort=False
                )
                self.aniso_trialsPart = len(self.aniso_phasePart)
                self.aniso_correctPart = self.aniso_gradePart[1] / self.aniso_trialsPart

                self.perPartIso.append(self.iso_correctPart * 100)
                self.perPartAniso.append(self.aniso_correctPart * 100)

    def correctRate(self):
        # Subcharts of rates

        self.rate_100 = self.RawData.loc[self.RawData["freq"] == 0.100]
        self.rate_133 = self.RawData.loc[self.RawData["freq"] == 0.133]
        self.rate_166 = self.RawData.loc[self.RawData["freq"] == 0.166]
        self.rate_200 = self.RawData.loc[self.RawData["freq"] == 0.200]
        self.rate_233 = self.RawData.loc[self.RawData["freq"] == 0.233]
        self.rate_266 = self.RawData.loc[self.RawData["freq"] == 0.266]
        self.rate_300 = self.RawData.loc[self.RawData["freq"] == 0.300]
        self.rate_333 = self.RawData.loc[self.RawData["freq"] == 0.33299999999999996]

        self.up_phase = self.RawData.loc[self.RawData["phase"] == 0]
        self.down_phase = self.RawData.loc[self.RawData["phase"] != 0]

        # Repeats of each rate

        self.n_rate = pd.value_counts(self.RawData["freq"].values, sort=True)
        self.rate_100_n = pd.value_counts(self.rate_100["grade"].values, sort=False)
        self.rate_133_n = pd.value_counts(self.rate_133["grade"].values, sort=False)
        self.rate_166_n = pd.value_counts(self.rate_166["grade"].values, sort=False)
        self.rate_200_n = pd.value_counts(self.rate_200["grade"].values, sort=False)
        self.rate_233_n = pd.value_counts(self.rate_233["grade"].values, sort=False)
        self.rate_266_n = pd.value_counts(self.rate_266["grade"].values, sort=False)
        self.rate_300_n = pd.value_counts(self.rate_300["grade"].values, sort=False)
        self.rate_333_n = pd.value_counts(self.rate_333["grade"].values, sort=False)

        self.s = [
            self.rate_100_n[1],
            self.rate_133_n[1],
            self.rate_166_n[1],
            self.rate_200_n[1],
            self.rate_233_n[1],
            self.rate_266_n[1],
            self.rate_300_n[1],
            self.rate_333_n[1],
        ]
        self.sf = [float(i) for i in self.s]

        try:
            self.correct_100 = self.rate_100_n[1] / self.n_rate[0.100]
        except:
            self.correct_100 = 0

        try:
            self.correct_133 = self.rate_133_n[1] / self.n_rate[0.133]
        except:
            self.correct_133 = 0

        try:
            self.correct_166 = self.rate_166_n[1] / self.n_rate[0.166]
        except:
            self.correct_166 = 3

        try:
            self.correct_200 = self.rate_200_n[1] / self.n_rate[0.200]
        except:
            self.correct_200 = 0

        try:
            self.correct_233 = self.rate_233_n[1] / self.n_rate[0.233]
        except:
            self.correct_233 = 0

        try:
            self.correct_266 = self.rate_266_n[1] / self.n_rate[0.266]
        except:
            self.correct_266 = 0

        try:
            self.correct_300 = self.rate_300_n[1] / self.n_rate[0.300]
        except:
            self.correct_300 = 0

        try:
            self.correct_333 = self.rate_333_n[1] / self.n_rate[0.33299999999999996]
        except:
            self.correct_333 = 0

        self.perCorrect = (
            np.array(
                [
                    self.correct_100,
                    self.correct_133,
                    self.correct_166,
                    self.correct_200,
                    self.correct_233,
                    self.correct_266,
                    self.correct_300,
                    self.correct_333,
                ]
            )
            * 100
        )
        try:
            self.total_perc = self.RawData["grade"].value_counts()[1] / (
                self.RawData["grade"].value_counts()[1]
                + self.RawData["grade"].value_counts()[0]
            )
        except:
            self.total_perc = 100

        rates = np.array([100, 133, 166, 200, 233, 266, 300, 333])
        self.rates = rates / 1000
        self.ratesL = np.ndarray.tolist(self.rates)
        self.ratesLf = [float(i) for i in self.ratesL]

    def propCorrect(self):
        self.RawData["correct"].value_counts().sort_index().plot.bar()

    def propInput(self):
        self.RawData["input"].value_counts().sort_index().plot.bar()

    def propPhase(self):
        self.RawData["phase"].value_counts().sort_index().plot.bar()

    def propUp(self):
        self.up_phase["grade"].value_counts().sort_index().plot.bar()

    def propDown(self):
        self.down_phase["phase"].value_counts().sort_index().plot.bar()

    def propGrade(self):
        self.RawData["grade"].value_counts().plot.bar()

    def propRates(self, folder, temp):
        self.perRates = self.RawData["freq"].value_counts()
        self.perRates.sort_index().plot.bar()
        plt.title("Frequency of frequencies")
        plt.text(1, 3, "n = " + self.Nsample)
        plt.text(1, 2.5, temp)
        plt.savefig(
            "./data/{}/figure_analysis/rates_cold_{}_N_{}_{}.svg".format(
                folder, temp, self.Nsample, self.subject
            ),
            transparent=True,
        )

    def TuningCurve(self, folder, temp):

        fig, ax = plt.subplots(1, 1)
        if int(temp.split("_")[0]) < 33:
            plt.plot(self.rates, self.perCorrect, color="b")
            plt.xticks(self.rates)
            plt.ylabel("% correct")
            # plt.title('Cold range (28.5-29.5 degrees Celsius)')
            plt.ylim([50, 100])
            plt.xlim([0.1, 0.333])
            plt.xlabel("Hz")
            # plt.text(0.300, 60, 'Total correct: ' + str(self.total_perc))
            # plt.text(0.200, 55, 'n = ' + str(len(self.RawData)))
            plt.hlines(y=50, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
            plt.hlines(y=75, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            plt.savefig(
                "./data/{}/figure_analysis/cold_{}_N_{}_{}.svg".format(
                    folder, temp, self.Nsample, self.subject
                ),
                transparent=True,
            )
        else:

            plt.plot(self.rates, self.perCorrect, color="r")
            plt.xticks(self.rates)
            plt.ylabel("% correct")
            # plt.title('Warm range (36.5-37.5 degrees Celsius)')
            plt.ylim([50, 100])
            plt.xlim([0.1, 0.333])
            plt.xlabel("Hz")
            # plt.text(0.300, 60, 'Total correct: ' + str(self.total_perc))
            # plt.text(0.200, 55, 'n = ' + str(len((self.RawData))))
            plt.hlines(y=50, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
            plt.hlines(y=75, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            plt.savefig(
                "./data/{}/figure_analysis/hot_{}_N_{}_{}.svg".format(
                    folder, temp, self.Nsample, self.subject
                ),
                transparent=True,
            )

    def ThroughoutTime(self, folder, temp=None, save="N"):
        if self.subject == "all":
            self.hits_time = []
            for i in np.arange(max(self.RawData["n_subject"])):
                if i == 4:
                    pass
                else:
                    temp_subset = self.RawData.loc[self.RawData["n_subject"] == i + 1]
                    # print(temp_subset)
                    self.hits_time.append(temp_subset["grade"])
                    self.grade_t = np.mean(np.asarray(self.hits_time), axis=0)
        else:
            self.grade_t = self.RawData["grade"]
            pass

        fig, ax = plt.subplots(1, 1)
        if int(temp.split("_")[0]) < 33:

            plt.plot(np.arange(len(self.grade_t)), self.grade_t, color="b")

            plt.yticks(np.arange(0, 1.01, step=1), ["Miss", "Hit"])
            plt.ylim([0, 1])
            plt.xlabel("Trials")
            plt.xticks(np.arange(0, 48.01, step=5))

            plt.vlines(x=12, ymin=0, ymax=1.01, color="k", linestyles="dashed")
            plt.vlines(x=24, ymin=0, ymax=1.01, color="k", linestyles="dashed")
            plt.vlines(x=36, ymin=0, ymax=1.01, color="k", linestyles="dashed")

            plt.xlim([0, 48])
            # plt.title('Cold range (28.5-29.5) Hits or Misses across time')
            for i in np.arange(8):
                ax.plot(
                    np.arange(len(self.grade_t)),
                    self.hits_time[i],
                    color="k",
                    alpha=0.1,
                )

            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            if save in ("Y"):
                plt.savefig(
                    "./data/{}/figure_analysis/cold_across_time_{}_N_{}_{}.svg".format(
                        folder, temp, self.Nsample, self.subject
                    ),
                    transparent=True,
                )

        else:

            plt.plot(np.arange(len(self.grade_t)), self.grade_t, color="r")

            plt.yticks(np.arange(0, 1.01, step=1), ["Miss", "Hit"])
            plt.xlabel("Trials")
            plt.ylim([0, 1])
            plt.xticks(np.arange(0, 48.01, step=4))

            plt.vlines(x=12, ymin=0, ymax=1.01, color="k", linestyles="dashed")
            plt.vlines(x=24, ymin=0, ymax=1.01, color="k", linestyles="dashed")
            plt.vlines(x=36, ymin=0, ymax=1.01, color="k", linestyles="dashed")

            plt.xlim([0, 48])
            # plt.title('Warm range (36.5-37.5) Hits or Misses across time')

            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            for i in np.arange(8):
                ax.plot(
                    np.arange(len(self.grade_t)),
                    self.hits_time[i],
                    color="k",
                    alpha=0.1,
                )

            if save in ("Y"):
                plt.savefig(
                    "./data/{}/figure_analysis/warm_across_time_{}_N_{}_{}.svg".format(
                        folder, temp, self.Nsample, self.subject
                    ),
                    transparent=True,
                )

    def ThroughoutTimeALL(self, temp):
        self.hits_time = []
        fig, ax = plt.subplots(1, 1)
        for i in np.arange(max(self.RawData["n_subject"])):
            temp_subset = self.RawData.loc[self.RawData["n_subject"] == i + 1]
            self.hits_time.append(temp_subset["grade"])
            self.tt = np.mean(np.asarray(self.hits_time), axis=0)

        if int(temp.split("_")[0]) < 33:
            plt.plot(np.arange(len(self.tt)), self.tt, color="b")

            plt.yticks(np.arange(0, 1.01, step=1), ["Miss", "Hit"])
            plt.xlabel("Trials")
            plt.title("Cold range (28.5-29.5) Hits or Misses across time")

            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            plt.savefig(
                "./data/{}/figure_analysis/cold_across_time_{}_N_{}_{}.svg".format(
                    folder, temp, self.Nsample, self.subject
                ),
                transparent=True,
            )

        else:

            plt.plot(np.arange(len(self.tt)), self.tt, color="r")

            plt.yticks(np.arange(0, 1.01, step=1), ["Miss", "Hit"])
            plt.xlabel("Trials")
            plt.title("Warm range (28.5-29.5) Hits or Misses across time")

            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

            plt.savefig(
                "./data/{}/figure_analysis/warm_across_time_{}_N_{}_{}.svg".format(
                    folder, temp, self.Nsample, self.subject
                ),
                transparent=True,
            )

    def ThroughoutTimeTGO(self, folder, title=None, save="N"):
        if self.subject == "all":
            self.hits_time = []

            label_participant = self.RawData["n_subject"].unique()

            for i in label_participant:
                # print(i)
                # for j in self.who_out:
                #     # print(j)
                #     if i + 1 == j:
                #         print('it works')
                #         pass
                #     else:
                temp_subset = self.RawData.loc[self.RawData["n_subject"] == i]
                # print(temp_subset)
                self.hits_time.append(temp_subset["grade"])
                # print(len(self.hits_time))
                self.grade_t = np.mean(np.asarray(self.hits_time), axis=0)
                # print(self.grade_t)

        else:
            self.grade_t = self.RawData["grade"]
            pass

        fig, ax = plt.subplots(1, 1)
        plt.plot(np.arange(len(self.grade_t)), self.grade_t, color="#4D4B50")

        # plt.xticks(np.arange(0, 46, step = 5))

        plt.vlines(x=23, ymin=0, ymax=1.01, color="k", linestyles="dashed")
        # plt.vlines(x = 24, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
        # plt.vlines(x = 36, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')

        plt.xticks(np.arange(0, 46.01, step=2))

        if self.subject == "all":
            for i in self.hits_time:
                ax.plot(np.arange(len(self.grade_t)), i, color="k", alpha=0.1)

        plt.yticks(np.arange(0, 1.01, step=1), ["Miss", "Hit"])
        plt.ylim([0, 1])
        plt.xlim([0, 46])
        plt.xlabel("Trials")
        # plt.title(title)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        if save in ("Y"):
            plt.savefig(
                "./data/{}/figure_analysis/tgo_across_time_{}.svg".format(
                    folder, self.subject
                ),
                transparent=True,
            )

    def BarIsoAniso(self, title=None, folder=None, all="N", save="N"):

        fig, ax = plt.subplots(1, figsize=(10, 10))
        x = [1, 2]
        widthB = 3
        plt.bar(
            x,
            self.perCorrect,
            color="None",
            edgecolor=["#7D5D99", "#A32857"],
            linewidth=widthB,
        )
        plt.rcParams.update({"font.size": 25})
        plt.xticks([1, 2])

        labels = [item.get_text() for item in ax.get_xticklabels()]
        labels[0] = "In-phase"
        labels[1] = "Out-phase"
        ax.set_xticklabels(labels)

        # plt.title(title)
        plt.xlabel("Phase")
        plt.ylabel("% correct responses")
        plt.ylim([0, 100])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        ax.xaxis.set_tick_params(width=widthB)
        ax.yaxis.set_tick_params(width=widthB)

        for axis in ["bottom", "left"]:
            ax.spines[axis].set_linewidth(3)

        plt.rcParams.update({"font.size": 25})

        if all == "Y":
            for i, j in zip(self.perPartIso, self.perPartAniso):
                ax.plot(x, [i, j], color="k", lw=widthB)
                ax.scatter(x, [i, j], color=["#7D5D99", "#A32857"])

        if save in ("Y"):
            plt.savefig(
                "./data/{}/figure_analysis/tgo_Bar_IvsA_{}.svg".format(
                    folder, self.subject
                ),
                transparent=True,
            )


class analyseTTT(ploTTT):
    # def __init__(self):
    #     ploTTT.__init__(self, file, subject)

    @staticmethod
    def QQplot(file, distribution, parameters, path_qq, name_qq, range):
        percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs.append(sub_data.perCorrect)

        theor = []
        dataD = []

        for i in np.arange(len(percs_indvs)):
            theor.append(
                cdfProbPlot(percs_indvs[i], dist=distribution, sparams=parameters)[0]
            )
            dataD.append(
                cdfProbPlot(percs_indvs[i], dist=distribution, sparams=parameters)[1]
            )

        subs = 1

        fig = plt.figure(figsize=(10, 10), facecolor="w")

        for i in np.arange(len(percs_indvs)):
            ax = fig.add_subplot(4, 2, subs)
            ax.plot(
                theor[i][0],
                theor[i][1],
                "bo",
                theor[i][0],
                dataD[i][0] * theor[i][0] + dataD[i][1],
                "r",
            )
            ax.set_xlabel("Theoretical quantiles")
            ax.set_ylabel("Data quantiles")
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            subs += 1

        fig.legend(["Fit", "Perfect fit"])
        plt.suptitle("Distribution of {}: {}".format(range, distribution))
        plt.subplots_adjust(top=2)
        plt.ylim([50, 100])
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        plt.savefig("./{}/{}.svg".format(path_qq, name_qq), transparent=True)

        return [percs_indvs, theor, dataD]

    def linearFit(self):
        self.s, self.i = np.polyfit(self.rates, self.perCorrect, 1)
        self.y_line = self.s * self.rates + self.i

    def plotLinearFit(self, color, title, path_fit, name_fit, save="Y"):
        fig, ax = plt.subplots(1, 1)
        plt.plot(
            self.rates,
            self.perCorrect,
            "-{}".format(color),
            self.rates,
            self.y_line,
            "--{}".format(color),
        )

        plt.ylim([50, 100])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.hlines(y=75, xmin=0.100, xmax=0.333, linestyles="dashed", lw=0.4)
        plt.xticks(self.rates)
        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.text(0.2, 55, "Slope:  " + str(round(self.s)))
        plt.text(0.2, 51, "Intercept: " + str(round(self.i)))
        plt.title(title)

        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path_fit, name_fit), transparent=True)

    def bootstrapping(self, file, function, revolts, bootedObvs):
        self.revolts = revolts
        self.percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                self.percs_indvs.append(sub_data.bootedObvs)

        self.BS_samples = []

        for i in np.arange(revolts):
            bootstrapped_sample = skl.utils.resample(self.percs_indvs, n_samples=8)
            BS_array = np.asarray(bootstrapped_sample)
            BS_mean = function(bootstrapped_sample, axis=0)
            self.BS_samples.append(BS_mean)

        self.funced_BS = np.mean(self.BS_samples, axis=0)

    def plotBoot(
        self,
        title,
        path,
        name,
        color_funced,
        color_parent,
        functionApplied,
        alpha=0.03,
        save="Y",
    ):

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, "-{}".format(color_funced))
        ax.plot(self.rates, self.perCorrect, "-{}".format(color_parent))

        for L in self.BS_samples:
            ax.plot(self.rates, L, color="#4D4B50", alpha=alpha)

        plt.legend(
            [
                "Bootstrapped {}".format(functionApplied),
                "Parent data",
                "Bootstrapped samples",
            ]
        )
        plt.ylim([50, 100])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.title(title)
        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.xticks(self.rates)

        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    # Here we get the slopes of all bootstrapped samples
    def slopBoot(self):

        self.s_indvs = []
        self.i_indvs = []

        for i in np.arange(len(self.BS_samples)):
            s_dummy, i_dummy = np.polyfit(self.rates, self.BS_samples[i], 1)
            self.s_indvs.append(s_dummy)
            self.i_indvs.append(i_dummy)

    # Here we plot the linear fit to all our bootstrapped samples
    def plotSlop(
        self,
        title,
        path,
        name,
        color_funced,
        color_parent,
        functionApplied,
        alpha=0.03,
        save="Y",
    ):

        self.y_line_indvs = []

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, "-{}".format(color_funced))
        ax.plot(self.rates, self.perCorrect, "-{}".format(color_parent))

        for i in np.arange(len(self.s_indvs)):
            self.y_line_indvs.append(self.s_indvs[i] * self.rates + self.i_indvs[i])
            ax.plot(self.rates, self.y_line_indvs[i], "--", alpha=alpha)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([50, 100])

        plt.ylabel("% correct")
        plt.xlabel("Frequencies")
        plt.xticks(self.rates)

        plt.legend(
            [
                "Bootstrapped {}".format(functionApplied),
                "Parent data",
                "Bootstrapped samples",
            ]
        )
        plt.title(title)
        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    def CIBoot(self, data, lowBound, highBound):
        self.sorted_data = np.sort(data)

        self.lowCI = self.sorted_data[
            np.round(self.revolts * (lowBound / 100) / 2).astype(int)
        ]
        self.highCI = self.sorted_data[
            np.round(self.revolts * (highBound / 100) / 2).astype(int)
        ]

    @staticmethod
    def CIdifff(data1, data2, lowBound, highBound, revolts):
        data1 = np.asarray(data1)
        data2 = np.asarray(data2)
        bootdiff = np.subtract(data1, data2)
        sorted_bootdiff = np.sort(bootdiff)

        ci_diff = (
            sorted_bootdiff[np.round(revolts * (lowBound / 100) / 2).astype(int)],
            sorted_bootdiff[np.round(revolts * (highBound / 100) / 2).astype(int)],
        )

        return ci_diff, bootdiff

    @staticmethod
    def pValueBoots(
        data1, data2, obvs_value, revolts, round_place, function, args=None, x=[]
    ):
        eng = me.start_matlab()

        pooled = np.append(data1, data2)
        bs_samples = []

        for i in np.arange(10000):
            bootstrapped_sample = skl.utils.resample(
                pooled, n_samples=(len(data1) + len(data2))
            )
            BS_array = np.asarray(bootstrapped_sample)
            bs_1 = BS_array[0 : len(data1)]
            bs_2 = BS_array[len(data1) : (len(data1) + len(data1))]

            if function == np.polyfit:
                s_1, i_1 = function(x, bs_1, args)
                s_2, i_2 = function(x, bs_2, args)

            if function == eng.nonParamAnalysis:

                [xfit, pfit, threshold, s_1, sd_th, sd_sl] = eng.nonParamAnalysis(
                    x, nargout=6
                )
                [xfit, pfit, threshold, s_2, sd_th, sd_sl] = eng.nonParamAnalysis(
                    x, nargout=6
                )

            bs_s = s_1 - s_2
            bs_samples.append(bs_s)

        thres_values = [i for i in bs_samples if i >= obvs_value]

        p_value = round((len(thres_values) + 1) / (revolts + 1), round_place)

        return p_value

    @staticmethod
    def poolST(data1, data2):
        pooled = []
        for i, j in zip((data1, data2)):
            temp = np.array([i, j])
            pooled.append(temp)

    def timePerformance(self, exclude=None):

        self.hits_time = []
        for i in np.arange(max(self.RawData["n_subject"])):
            if i == exclude:
                pass
            else:
                temp_subset = self.RawData.loc[self.RawData["n_subject"] == i + 1]
                # print(temp_subset)
                self.hits_time.append(temp_subset["grade"])
                self.grade_t = np.mean(np.asarray(self.hits_time), axis=0)

    def AUCPerformance(self, n_chunks):
        self.AUC_chunks = []
        self.n_chunks = n_chunks
        self.chunks = np.split(self.grade_t, n_chunks)
        self.AUCS = np.empty(n_chunks)

        for i in np.arange(n_chunks):
            self.AUCS[i] = np.trapz(self.chunks[i])

        for i in np.arange(len(self.hits_time)):
            dummy_chunk = np.split(self.hits_time[i], n_chunks)
            dummy_AUCs = np.empty(n_chunks)

            for i in np.arange(len(dummy_chunk)):
                dummy_AUCs[i] = np.trapz(dummy_chunk[i])

            self.AUC_chunks.append(dummy_AUCs)

    def AUCPlot(self, path, name, color, min_y, max_y, title=None):

        fig, ax = plt.subplots(1, 1)
        ax.plot(
            np.arange(1, len(self.AUCS) + 0.1, step=1), self.AUCS, "-{}".format(color)
        )

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([min_y, max_y])
        plt.xlim([1, self.n_chunks])

        for i in np.arange(len(self.hits_time)):
            ax.plot(
                np.arange(1, len(self.AUCS) + 0.1, step=1),
                self.AUC_chunks[i],
                color="k",
                alpha=0.1,
            )

        plt.xticks(np.arange(1, self.n_chunks + 0.1, step=1))
        plt.xlabel("Periods")
        plt.ylabel("AUC")

        # plt.title(title)
        plt.savefig("./{}/{}.svg".format(path, name), transparent=True)

    def jackKnifeNonParametric(self, file, repeats):
        percs_indvs_T = []
        eng = me.start_matlab()

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs_T.append(sub_data.sf)

        self.n_T = len(percs_indvs_T)
        self.indexT = np.arange(self.n_T)

        self.xfit_jkT = []
        self.pfit_jkT = []
        self.threshold_jkT = []
        self.slopes_jkT = []
        self.sd_th_jkT = []
        self.sd_sl_jkT = []

        percs_indvs_T = np.asarray(percs_indvs_T)

        for i in range(self.n_T):
            jk_sampleT = percs_indvs_T[self.indexT != i]
            summed_jkT = np.sum(jk_sampleT, axis=0)
            summed_jkT = np.ndarray.tolist(summed_jkT)
            summed_jkT = [float(i) for i in summed_jkT]

            [xfitT, pfitT, thresholdT, slopeT, sd_thT, sd_slT] = eng.nonParamAnalysis(
                self.ratesLf, summed_jkT, repeats, nargout=6
            )

            self.xfit_jkT.append(xfitT)
            self.pfit_jkT.append(pfitT)
            self.threshold_jkT.append(thresholdT)
            self.slopes_jkT.append(slopeT)
            self.sd_th_jkT.append(sd_thT)
            self.sd_sl_jkT.append(sd_slT)

    def plotJKs(
        self,
        color_data,
        color_nonPar,
        title=None,
        alpha=0.05,
        save="Y",
        path=None,
        name=None,
    ):
        fig, ax = plt.subplots(1, 1)
        self.meaned_nonParametric = np.mean(self.pfit_jkT, axis=0)
        ax.plot(self.rates, self.perCorrect / 100, "-{}".format(color_data))
        ax.plot(self.xfit_jkT[0], self.meaned_nonParametric, "-{}".format(color_nonPar))

        for i in np.arange(len(self.pfit_jkT)):
            ax.plot(self.xfit_jkT[i], self.pfit_jkT[i], "--", alpha=alpha)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.ylim([0.5, 1])
        plt.xlim([0.100, 0.333])

        plt.ylabel("% correct")
        plt.xlabel("Hz")
        plt.xticks(self.rates)

        plt.legend(["Original data", "Mean jack-knife", "Jack-knife samples"])
        plt.title(title)
        if save == "Y":
            plt.savefig("./{}/{}.svg".format(path, name), transparent=True)


################################################################################
################################ Functions ######################################
################################################################################


def cdfProbPlot(x, dist, sparams=()):
    x = np.asarray(x)

    osm_uniform = stats.stats._calc_uniform_order_statistic_medians(len(x))
    dist = stats.stats._parse_dist_kw(dist, enforce_subclass=False)
    if sparams is None:
        sparams = ()
    if isscalar(sparams):
        sparams = (sparams,)
    if not isinstance(sparams, tuple):
        sparams = tuple(sparams)

    osm = dist.ppf(osm_uniform, *sparams)
    osr = sort(x)

    # perform a linear least squares fit.
    slope, intercept, r, prob, sterrest = stats.linregress(osm, osr)

    return (osm, osr), (slope, intercept, r)


def cdfplot(theor, data, path_qq, name_qq, range, distribution):

    fig, ax = plt.subplots(1, 1)
    plt.plot(theor[0], theor[1], "bo", theor[0], data[0] * theor[0] + data[1], "r")
    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Data quantiles")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    fig.legend(["Fit", "Perfect fit"])
    plt.title("Distribution of {}: {}".format(range, distribution))
    plt.subplots_adjust(top=2)
    plt.ylim([50, 100])
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig("./{}/{}.svg".format(path_qq, name_qq), transparent=True)

    return
