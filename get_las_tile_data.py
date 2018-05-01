import pandas as pd

h5 = r'I:\NGS_TPU\DATA\FL1604-TB-N\las\OUTPUT\2016_435500e_2866500n_TPU.h5'

df = pd.read_hdf(h5)

print df
