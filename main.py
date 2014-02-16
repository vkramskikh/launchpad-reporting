#import httplib2
import requests, json, flask
from launchpad.release_chart import ReleaseChart
from launchpad.lpdata import LaunchpadData

#httplib2.debuglevel = 1

app = flask.Flask(__name__)
lpdata = LaunchpadData()

@app.route('/project/<project_name>/bug_table/<bug_type>/<milestone_name>')
def bug_table(project_name, bug_type, milestone_name):
    project = lpdata.get_project(project_name)
    bugs = lpdata.get_bugs(project_name, LaunchpadData.BUG_STATUSES[bug_type], milestone_name)
    return flask.render_template("bug_table.html", project=project, bugs=bugs, bug_type=bug_type, milestone_name=milestone_name, selected_bug_table=True)

@app.route('/project/<project_name>')
def project_overview(project_name):
    project = lpdata.get_project(project_name)
    return flask.render_template("project.html", project=project, selected_overview=True)

@app.route('/project/<project_name>/bug_trends/<milestone_name>')
def bug_trends(project_name, milestone_name):
    project = lpdata.get_project(project_name)
    return flask.render_template("bug_trends.html", project=project, milestone_name=milestone_name, selected_bug_trends=True)

@app.route('/project/<project_name>/api/release_chart/<milestone_name>/get_data')
def bug_report_get_data(project_name, milestone_name):
    data = ReleaseChart(lpdata, project_name, milestone_name).get_data()
    return flask.json.dumps(data)

@app.route('/')
def main_page():
    return flask.redirect(flask.url_for("project_overview", project_name="fuel"))

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 4444, threaded = True, debug = True)
