import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import csv
import datetime as dt

pp = PdfPages('strong.pdf')


def get_sets():
    sets = []
    with open('strong.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sets.append(row)
    return sets


def group_sets(sets):
    workouts = {}
    for set in sets:
        date = set['Date']
        date = dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
        exercise_name = set['Exercise Name']
        if date not in workouts:
            workouts[date] = {}
        workout = workouts[date]

        if exercise_name not in workout:
            workout[exercise_name] = []
        weight_str = set['Weight']
        reps_str = set['Reps']
        weight = float(weight_str if len(weight_str) > 0 else 0)
        reps = int(reps_str if len(reps_str) > 0 else 0)
        rm1 = weight / (1.0278 - 0.0278 * reps)
        volume = weight * reps
        if volume > 0:
            workout[exercise_name].append({
                'Weight': weight,
                'Reps': reps,
                'Volume': volume,
                'RM1': rm1,
            })
    return workouts


def get_exercises(workouts):
    exercises = {}

    for date in workouts:
        workout = workouts[date]

        for exercise_name in workout:
            sets = workout[exercise_name]
            if exercise_name not in exercises:
                exercises[exercise_name] = []

            volume = 0
            max_rm1 = 0
            for set in sets:
                volume += set['Volume']
                rm1 = set['RM1']
                if rm1 > max_rm1:
                    max_rm1 = rm1

            exercises[exercise_name].append({
                'Date': date,
                'Sets': sets,
                'Volume': volume,
                'RM1': max_rm1,
            })

    return exercises


def create_plot(title, x, y, color):
    if len(x) < 5 or len(y) < 5:
        return
    plt.clf()
    plt.figure(figsize=(10, 5))
    plt.title(title)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.ylabel('kg')
    plt.plot(x, y, color=color)
    plt.gcf().autofmt_xdate()
    plt.savefig(pp, format='pdf')


def exercise_to_pdf(exercise_name, exercise):
    x = [e['Date'] for e in exercise]
    y_rm1 = [e['RM1'] for e in exercise]
    y_volume = [e['Volume'] for e in exercise]

    create_plot(exercise_name + ' estimated 1rm (best set)', x, y_rm1, 'blue')
    create_plot(exercise_name + ' volume', x, y_volume, 'orange')


def overall_volume(workouts):
    x = [w for w in workouts]
    y = []

    for date in x:
        volume = 0
        workout = workouts[date]

        for exercise_name in workout:
            exercises = workout[exercise_name]
            volume += sum([e['Volume'] for e in exercises])
        y.append(volume)

    create_plot('Total volume per training day', x, y, 'green')


def weekly_volume(workouts):
    y = []

    index_map = {}

    weekly_workouts = {}
    for date in workouts:
        week = date.isocalendar()
        index = week.year * 52 + week.week
        if index not in index_map:
            index_map[index] = date
            weekly_workouts[date] = []
        date_index = index_map[index]
        weekly_workouts[date_index].append(workouts[date])

    for date in weekly_workouts:
        workouts = weekly_workouts[date]
        volume = 0
        for workout in workouts:
            for exercise_name in workout:
                exercises = workout[exercise_name]
                volume += sum([e['Volume'] for e in exercises])
        y.append(volume)
    x = [date for date in weekly_workouts]

    create_plot('Weekly volume', x, y, 'purple')


def create_pdf(workouts, exercise_names, exercises):
    overall_volume(workouts)
    weekly_volume(workouts)
    for exercise_name in exercise_names:
        exercise_to_pdf(exercise_name, exercises[exercise_name])
    pp.close()


sets = get_sets()
workouts = group_sets(sets)
exercises = get_exercises(workouts)
exercise_names = sorted(exercises, key=lambda k: len(exercises[k]), reverse=True)
create_pdf(workouts, exercise_names, exercises)
