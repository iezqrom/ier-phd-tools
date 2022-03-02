import numpy as np


def default_pars(duration, dt=1, **kwargs):
    pars = {}

    # typical neuron parameters#
    pars["V_th"] = -55.0  # spike threshold [mV]
    pars["V_reset"] = -75.0  # reset potential [mV]
    pars["tau_m"] = 10.0  # membrane time constant [ms]
    pars["g_L"] = 10.0  # leak conductance [nS]
    pars["V_init"] = -75.0  # initial potential [mV]
    pars["E_L"] = -75.0  # leak reversal potential [mV]
    pars["tref"] = 2.0  # refractory time (ms)

    # simulation parameters #
    pars["T"] = duration  # Total duration of simulation [ms]
    pars["dt"] = dt  # Simulation time step [ms]

    pars["range_t"] = np.arange(
        0, pars["T"], pars["dt"]
    )  # Vector of discretized time points [ms]

    # external parameters if any #
    for k in kwargs:
        pars[k] = kwargs[k]

    return pars


def run_LIF(pars, Iinj, stop=False):
    """
    Simulate the LIF dynamics with external input current

    Args:
      pars       : parameter dictionary
      Iinj       : input current [pA]. The injected current here can be a value
                   or an array
      stop       : boolean. If True, use a current pulse

    Returns:
      rec_v      : membrane potential
      rec_sp     : spike times
    """
    # Set parameters
    V_th, V_reset = pars["V_th"], pars["V_reset"]
    tau_m, g_L = pars["tau_m"], pars["g_L"]
    V_init, E_L = pars["V_init"], pars["E_L"]
    dt, range_t = pars["dt"], pars["range_t"]

    tref = pars["tref"]

    # Initialize voltage and current
    v = np.zeros(len(Iinj))
    len(v)
    v[0] = V_init
    tr = 0.0  # the count for refractory duration

    # Simulate the LIF dynamics
    rec_spikes = []  # record spike times
    for it in range(len(Iinj) - 1):
        if tr > 0:  # check for refractoriness
            v[it] = V_reset
            tr = tr - 1
        elif v[it] >= V_th:  # reset voltage and record spike event
            rec_spikes.append(it)
            v[it] = V_reset
            tr = tref / dt

        # calculate the increment of the membrane potential
        dv = (-(v[it] - E_L) + Iinj[it] / g_L) * (dt / tau_m)

        # update the membrane potential
        # print(it)
        v[it + 1] = v[it] + dv

    rec_spikes = np.array(rec_spikes) * dt

    return v, rec_spikes
