from launchpadlib.launchpad import Launchpad
from bug import Bug
from project import Project
from ttl_cache import ttl_cache

class LaunchpadData():

    BUG_STATUSES = {"New":        ["New"],
                    "Incomplete": ["Incomplete"],
                    "Open":       ["Triaged", "In Progress", "Confirmed"],
                    "Closed":     ["Fix Committed", "Fix Released", "Won't Fix", "Invalid", "Expired", "Opinion"]}

    BUG_STATUSES_ALL = []
    for k in BUG_STATUSES:
        BUG_STATUSES_ALL.append(BUG_STATUSES[k])

    def __init__(self):
        cachedir = "~/.launchpadlib/cache/"
        self.launchpad = Launchpad.login_anonymously('launchpad-reporting-www', 'production', cachedir)

    def _get_project(self, project_name):
        return self.launchpad.projects[project_name]

    def _get_milestone(self, project_name, milestone_name):
        project = self._get_project(project_name)
        return self.launchpad.load("%s/+milestone/%s" % (project.self_link, milestone_name))

    @ttl_cache(minutes=5)
    def get_project(self, project_name):
        return Project(self._get_project(project_name))

    @ttl_cache(minutes=5)
    def get_bugs(self, project_name, statuses, milestone_name = None, tags = None):
        project = self._get_project(project_name)
        if (milestone_name is None) or (milestone_name == 'None'):
            return [Bug(r) for r in project.searchTasks(status=statuses)]

        milestone = self._get_milestone(project_name, milestone_name)
        if (tags is None) or (tags == 'None'):
            return [Bug(r) for r in project.searchTasks(status=statuses, milestone=milestone)]

        return [Bug(r) for r in project.searchTasks(status=statuses, milestone=milestone, tags=tags)]

    @staticmethod
    def dump_object(object):
        for name in dir(object):
            try:
                value = getattr(object, name)
            except AttributeError:
                value = "n/a"
            try:
                print name + " --- " + str(value)
            except ValueError:
                print name + " --- " + "n/a"
