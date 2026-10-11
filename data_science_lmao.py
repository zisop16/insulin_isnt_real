import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from dfply import *
import pandas as pd
import pingouin as pg
from matplotlib.axes import Axes
from scipy.interpolate import CubicSpline

csv_arr = np.loadtxt("./glucose_data.csv", delimiter=",", dtype=str)

dict_keys = csv_arr[0]
glucose_data = {key: [] for key in dict_keys}

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

for student_ind in csv_arr[1:]:
	val: str
	for key, val in zip(dict_keys, student_ind):
		if is_float(val):
			glucose_data[key].append(float(val))
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

plot_all_liquids = False
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
# print(res)



sugar_no_sugar_graph = True
if sugar_no_sugar_graph:

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
		print(contained_sugar, curr_means, curr_stds)

		curr_ax.errorbar(time_indices, curr_means, elinestyle="--", color=colors[ax_ind], elinewidth=1, marker='o', capthick=2, capsize=4, yerr=curr_stds, label="Sugar" if contained_sugar else "No Sugar")

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


density_conversion_data: pd.DataFrame = pd.read_csv("./concentration_density_table.csv")
spline_interpolator = CubicSpline(density_conversion_data["Optical Density"], density_conversion_data["Insulin Concentration"])
max_OD_interp = max(density_conversion_data["Optical Density"])
spline_end_derivative = spline_interpolator.derivative()(max_OD_interp)
def spline_predict(optical_dens: float):
	if optical_dens > max_OD_interp:
		diff = optical_dens - max_OD_interp
		return spline_end_derivative * diff + spline_interpolator(max_OD_interp)
	value = spline_interpolator(optical_dens)
	return max(0, value)

all_glucose_reads = []
all_insulin_reads = []

for student in range(num_students):
	for time_point in time_points:
		OD_label = time_point + " OD"
		curr_OD = glucose_data[OD_label][student]
		if curr_OD == "N/A":
			continue
		curr_gluc = glucose_data[time_point][student]
		all_insulin_reads.append(spline_predict(curr_OD))
		all_glucose_reads.append(curr_gluc)

sm_x = np.array(all_glucose_reads)
all_insulin_reads = np.array(all_insulin_reads)

# print(all_glucose_reads, all_insulin_reads)

import statsmodels.api as sm

plot_ins_gluc_line = False
if plot_ins_gluc_line:
	sm_x = sm.add_constant(sm_x)
	model = sm.OLS(all_insulin_reads, sm_x).fit()
	# print(model.summary())
	def predict(gluc_val):
		return model.params[0] + model.params[1] * gluc_val
	x_range = np.linspace(65, 150, 200)
	y_pred = predict(x_range)
	axis_font = {'size': 15}
	plt.plot(x_range, y_pred, ls="--", c=(1, 0, .6), label="Linear Fit")
	plt.scatter(all_glucose_reads, all_insulin_reads, s=10)
	plt.xlabel("Blood Glucose (mg/dL)", fontdict=axis_font)
	plt.ylabel("Blood Insulin (μIU/mL)", fontdict=axis_font)
	plt.title("Blood Insulin vs Blood Glucose", fontdict=axis_font)
	plt.legend()
	# plt.show()

insulin_datapoints = []

for student in range(num_students):
	initial_OD = "T0 OD"
	final_OD = "T120 OD"

	OD_0 = glucose_data[initial_OD][student]
	OD_f = glucose_data[final_OD][student]

	if OD_0 == "N/A" or OD_f == "N/A":
		continue

	ins_0 = spline_predict(OD_0)
	ins_f = spline_predict(OD_f)
	diff = ins_f - ins_0
	
	had_sugar = (glucose_data["Liquid"][student] in ["Soda", "Orange Juice"])

	curr_dp = (float(had_sugar), -ins_0 + ins_f)
	insulin_datapoints.append(curr_dp)

# print(insulin_datapoints)
insulin_df = pd.DataFrame(insulin_datapoints, columns =['Sugar', 'Insulin Change'])

from sklearn.linear_model import LinearRegression

ins_model = LinearRegression()

ins_x = insulin_df.drop('Insulin Change', axis = 1)
ins_y = insulin_df['Insulin Change']
ins_model.fit(ins_x, ins_y)


# print(insulin_df)
# print(ins_model.predict(np.array(ins_x)))

show_insulinsugar_data = False
if show_insulinsugar_data:
	plt.xticks([0, 1], ["No Sugar", "Sugar"])
	plt.scatter(ins_x, ins_y)
	plt.show()