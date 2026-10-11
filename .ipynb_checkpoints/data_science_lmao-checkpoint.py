import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from dfply import *
import pandas as pd
import pingouin as pg
from matplotlib.axes import Axes

csv_arr = np.loadtxt("./glucose_data.csv", delimiter=",", dtype=str)

dict_keys = csv_arr[0]
glucose_data = {key: [] for key in dict_keys}

for student_ind in csv_arr[1:]:
	val: str
	for key, val in zip(dict_keys, student_ind):
		if val.isdigit():
			glucose_data[key].append(int(val))
		else:
			glucose_data[key].append(val)

liquid_counts = dict()
num_students = len(glucose_data["Liquid"])

for liquid in glucose_data["Liquid"]:
	if liquid in liquid_counts:
		liquid_counts[liquid] += 1
	else:
		liquid_counts[liquid] = 1

liquid_groups = list(liquid_counts.keys())
time_points = ["T0", "T30", "T60", "T120"]
num_times = len(time_points)

t_0 = glucose_data["T0"]
t_30 = glucose_data["T30"]
t_60 = glucose_data["T60"]
t_120 = glucose_data["T120"]
liq_students = glucose_data["Liquid"]

def get_mean_stdev(time_point: str, liquid_group: str):
	curr_n = liquid_counts[liquid_group]
	gluc_measurements = np.zeros(curr_n)
	i: int = 0
	for curr_gluc, liq in zip(glucose_data[time_point], liq_students):
		if liq == liquid_group:
			gluc_measurements[i] = curr_gluc
			i += 1
	curr_mean = np.mean(gluc_measurements)
	# Sample variance
	curr_var = np.var(gluc_measurements, ddof=1)
	curr_stdev = curr_var ** .5
	return curr_n, curr_mean, curr_stdev


liquid_timeseries = {liquid: None for liquid in liquid_groups}
time_indices = [0, 1, 2, 3]
num_liquids = len(liquid_groups)

plot_all_liquids = True
if plot_all_liquids:
	axs: list[Axes]
	fig, axs = plt.subplots(nrows=4, sharex=True, sharey=True)
	colors = [(0, 0, 1), (.9, .5, 0), (1, 0, 0), (.8, .1, .8)]

	for i, liquid in enumerate(liquid_groups):
		curr_ax = axs[i]
		curr_series = np.zeros(num_times)
		curr_errs = np.zeros(num_times)
		liquid_timeseries[liquid] = curr_series
		for j, time_point in enumerate(time_points):
			curr_n, curr_mean, curr_stdev = get_mean_stdev(time_point, liquid)
			curr_series[j] = curr_mean
			curr_errs[j] = curr_stdev
		curr_ax.errorbar(time_indices, curr_series, color=colors[i], elinestyle="--", elinewidth=1, marker='o', capthick=2, capsize=4, yerr=curr_errs, label=liquid)

	axis_font = {'size': 15}
	axs[0].set_title("Mean Measured Blood Glucose vs. Time Since Finished Beverage", fontdict=axis_font)
	axs[-1].set_xticks(time_indices, time_points)
	axs[-1].set_xlabel("Time (minutes)", fontdict=axis_font)
	fig.text(.04, .5, 'Blood Glucose (mg/dL)', va='center', rotation='vertical', fontdict=axis_font)

	lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
	lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
	fig.legend(lines, labels)
	plt.show()


glucose_dataframe = []
columns = ["StudentID", "Liquid", "Time", "Blood Glucose"]
for student_ind in range(num_students):
	student_liquid = glucose_data["Liquid"][student_ind]
	time_point: str
	for time_point in time_points:
		curr_glucose = glucose_data[time_point][student_ind]
		curr_tuple = (student_ind, student_liquid, time_point, curr_glucose)
		glucose_dataframe.append(curr_tuple)

glucose_dataframe = pd.DataFrame(glucose_dataframe, columns=columns)
res = pg.mixed_anova(dv="Blood Glucose", between="Liquid", within="Time", subject="StudentID", data=glucose_dataframe)

sugar_nosugar_df = []
columns = ["StudentID","Sugar", "Time", "Blood Glucose"]
for student_ind in range(num_students):
	student_liquid = glucose_data["Liquid"][student_ind]
	sugar = student_liquid in ["Soda", "Orange Juice"]
	time_point: str
	for time_point in time_points:
		curr_glucose = glucose_data[time_point][student_ind]
		curr_tuple = (student_ind, sugar, time_point, curr_glucose)
		sugar_nosugar_df.append(curr_tuple)

sugar_nosugar_df = pd.DataFrame(sugar_nosugar_df, columns=columns)
res = pg.mixed_anova(dv="Blood Glucose", between="Sugar", within="Time", subject="StudentID", data=sugar_nosugar_df)

fig, axs = plt.subplots(nrows=2, sharex=True, sharey=True)
colors = [(0, 0, 1), (.9, .5, 0)]
for contained_sugar in [False, True]:
	ax_ind = int(contained_sugar)
	curr_ax = axs[ax_ind]
	curr_sugar_data = sugar_nosugar_df[sugar_nosugar_df["Sugar"] == contained_sugar]
	curr_means = []
	curr_stds = []
	for time_point in time_points:
		curr_timesugar_data = curr_sugar_data[curr_sugar_data["Time"] == time_point]
		glucose_vals = curr_timesugar_data["Blood Glucose"]
		curr_mean = np.mean(glucose_vals)
		# Sample variance
		curr_var = np.var(glucose_vals, ddof=1)
		std = curr_var ** .5
		curr_means.append(curr_mean)
		curr_stds.append(std)
	curr_means = np.array(curr_means)
	curr_stds = np.array(curr_stds)

	curr_ax.errorbar(time_indices, curr_means, elinestyle="--", color=colors[ax_ind], elinewidth=1, marker='o', capthick=2, capsize=4, yerr=curr_stds, label="Sugar" if contained_sugar else "No Sugar")

sugar_no_sugar_graph = False
if sugar_no_sugar_graph:
	axs[-1].set_xticks(time_indices, time_points)
	lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
	lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
	fig.legend(lines, labels)

	axis_font = {'size': 15}
	axs[0].set_title("Mean Measured Blood Glucose vs. Time Since Finished Beverage", fontdict=axis_font)
	axs[-1].set_xlabel("Time (minutes)", fontdict=axis_font)
	fig.text(.04, .5, 'Blood Glucose (mg/dL)', va='center', rotation='vertical', fontdict=axis_font)
	plt.show()

for time_point in time_points:
	for liquid_group in liquid_groups:
		_, mean, stdev = get_mean_stdev(time_point, liquid_group)
		# print(liquid_group, time_point, mean, stdev)