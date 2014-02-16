import datetime
import pytz
from launchpad.lpdata import LaunchpadData
from bisect import bisect_left
from operator import itemgetter

class ReleaseChart():

    def __init__(self, lpdata, project_name, milestone_name):
        self.bugs = []
        for status in LaunchpadData.BUG_STATUSES:
            self.bugs += lpdata.get_bugs(project_name, LaunchpadData.BUG_STATUSES[status], milestone_name);

    def get_data(self):

        # the chart will span until tomorrow
        window_end = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)

        # chart series
        data = {
            "Open": [],
            "Incomplete": [],
            "Resolved": [],
            "Verified": []
        }

        # all dates
        all_dates = set()

        # process each bug and its events
        for b in self.bugs:
            events = b.get_status_changes()
            events.append( {"date": window_end, "type": "N/A"} )
            for i in range(0, len(events) - 1):
                e1 = events[i]
                e2 = events[i + 1]

                t = e1["type"]
                d1 = e1["date"]
                d2 = e2["date"]

                if d1 <= d2:
                    data[t].append( {"date" : d1, "num": 1} )
                    data[t].append( {"date" : d2, "num": -1} )
                    all_dates.add(d1)
                    all_dates.add(d2)

        all_dates_sorted = sorted(all_dates)
        n = len(all_dates_sorted)

        # process each data item and construct chart
        d3_start = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc)

        chart = []
        for t in data:
            events = sorted(data[t], key=lambda d: (d['date'], -d['num']))

            # for each date, mark result in global list with dates
            all_dates_values = [None] * n
            bug_count = 0
            for e in events:
                bug_count += e["num"]
                idx = bisect_left(all_dates_sorted, e["date"])
                if not all_dates_sorted[idx] == e["date"]:
                    raise ValueError("Date not found in array using binary search")
                all_dates_values[idx] = bug_count

            # process all global dates
            prev = 0
            for idx in range(0, n):
                if all_dates_values[idx] is not None:
                    prev = all_dates_values[idx]
                    break

            for idx in range(0, n):
                if all_dates_values[idx] is None:
                    all_dates_values[idx] = prev
                else:
                    prev = all_dates_values[idx]

            # create series for the chart (except for the last point, which has all zeroes)
            values = []
            for idx in range(0, n - 1):
                chart_seconds = (all_dates_sorted[idx] - d3_start).total_seconds() * 1000.0
                values.append( [int(chart_seconds), all_dates_values[idx]] )
            chart.append( {'key': t, 'values': values})

        '''
        data = []

        d = datetime.datetime(2000, 10, 21)
        values = []
        fp = 1.0
        for i in range(0, 60):
            sp = (d-datetime.datetime(1970,1,1)).total_seconds() * 1000.0
            values.append( [int(sp), fp] )
            d = d + datetime.timedelta(days=1)
            fp = fp + .2

        data.append( {'key': "test", 'values': values})

        d = datetime.datetime(2000, 10, 21, 6, 5, 4)
        values = []
        fp = 10.0
        for i in range(0, 60):
            sp = (d-datetime.datetime(1970,1,1)).total_seconds() * 1000.0
            values.append( [int(sp), fp] )
            d = d + datetime.timedelta(days=1)
            fp = fp - 0.1


        data.append( {'key': "test2", 'values': values})
        '''

        return chart
