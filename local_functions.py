import pandas as pd
from scipy.stats import norm
import math
Z = norm.ppf

def tableTosdtDoble(table, num_sdt):
    table_single_sdt = table.loc[table['Touch'] == num_sdt]

    table_cold = table_single_sdt.loc[table_single_sdt['Cold'] == 1]
    table_nocold = table_single_sdt.loc[table_single_sdt['Cold'] == 0]

    present_yes = table_cold.loc[table_cold['Responses'] == 1]
    present_no = table_cold.loc[table_cold['Responses'] == 0]
     
    absent_yes = table_nocold.loc[table_nocold['Responses'] == 1]
    absent_no = table_nocold.loc[table_nocold['Responses'] == 0]

    return present_yes, present_no, absent_yes, absent_no


def SDT(hits, misses, fas, crs):
    """ returns a dict with d-prime measures given hits, misses, false alarms, and correct rejections"""
    # Floors an ceilings are replaced by half hits and half FA's
    half_hit = 0.5 / (hits + misses)
    half_fa = 0.5 / (fas + crs)
 
    # Calculate hit_rate and avoid d' infinity
    hit_rate = hits / (hits + misses)
    if hit_rate == 1: 
        hit_rate = 1 - half_hit
    if hit_rate == 0: 
        hit_rate = half_hit
 
    # Calculate false alarm rate and avoid d' infinity
    fa_rate = fas / (fas + crs)
    # print(fa_rate)
    if fa_rate == 1: 
        fa_rate = 1 - half_fa
    if fa_rate == 0: 
        fa_rate = half_fa

    # print(hit_rate)
    # print(fa_rate)
 
    # Return d', beta, c and Ad'
    out = {}
    out['d'] = Z(hit_rate) - Z(fa_rate) # Hint: normalise the centre of each curvey and subtract them (find the distance between the normalised centre
    out['beta'] = math.exp((Z(fa_rate)**2 - Z(hit_rate)**2) / 2)
    out['c'] = (Z(hit_rate) + Z(fa_rate)) / 2 # Hint: like d prime but you add the centres instead, find the negative value and half it
    out['Ad'] = norm.cdf(out['d'] / math.sqrt(2))
    
    return(out)