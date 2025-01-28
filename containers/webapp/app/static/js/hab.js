function nextWeekly() {
    i++;
    if (i == img.length) {
        i = img.length - 1;
    }
    document.getElementById("WeeklyTitle").innerText = "Weekly " +
	                     "composite from " + Mon[i] + " to " + Sun[i]
    document.getElementById("WeeklyImg").src = img[i];
}

function prevWeekly() {
    i--;
    if (i == -1) {
        i = 0;
    }
    document.getElementById("WeeklyTitle").innerText = "Weekly " +
	                     "composite from " + Mon[i] + " to " + Sun[i]
    document.getElementById("WeeklyImg").src = img[i];
}

function firstWeek() {
    i = 0;
    document.getElementById("WeeklyTitle").innerText = "Weekly " +
	                     "composite from " + Mon[i] + " to " + Sun[i]
    document.getElementById("WeeklyImg").src = img[i];
}

function lastWeek() {
    i = img.length - 1
    document.getElementById("WeeklyTitle").innerText = "Weekly " +
	                     "composite from " + Mon[i] + " to " + Sun[i]
    document.getElementById("WeeklyImg").src = img[i];
}

function nextDaily() {
    j++;
    if (j == day.length) {
        j = day.length - 1;
    }
    document.getElementById("DailyTitle").innerText = dates[j]
    document.getElementById("DailyImg").src = day[j];
}

function prevDaily() {
    j--;
    if (j == -1) {
        j = 0;
    }
    document.getElementById("DailyTitle").innerText = dates[j]
    document.getElementById("DailyImg").src = day[j];
}

function firstDay() {
    j = 0;
    document.getElementById("DailyTitle").innerText = dates[j]
    document.getElementById("DailyImg").src = day[j];
}

function lastDay() {
    j = day.length - 1
    document.getElementById("DailyTitle").innerText = dates[j]
    document.getElementById("DailyImg").src = day[j];
}

function init() {

	lastDay()
	lastWeek()

}
