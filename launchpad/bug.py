# This is a wrapper, which converts launchpad bug structure into a internal bug object.
#
# When you get certain properties of the bug (e.g. assignee), it usually does additional query to LP.
# This wrapper avoids doing any calls to Launchpad by going into internal representation of the object and grabbing the info from JSON.

import string
import lpdata

FIELDS_TO_COPY = [
    "date_assigned",
    "date_closed",
    "date_confirmed",
    "date_created",
    "date_fix_committed",
    "date_fix_released",
    "date_in_progress",
    "date_incomplete",
    "date_left_closed",
    "date_left_new",
    "date_triaged",
    "importance",
    "status"
]

FIELDS_TO_COPY_FROM_JSON = [
    "assignee_link",
    "milestone_link",
    "title",
    "web_link"
]

class Bug():

    # I'm too lazy to deal with UTF-8 at this point
    # need this make sure the bugs from Chinese people don't cause exceptions
    def sanitize_string(self, s):
        return filter(lambda x: x in string.printable, s)

    def __init__(self, lpbug):
        
        # straight copy fields from the lpbug object. this do not make any calls to LP
        for name in FIELDS_TO_COPY:
            setattr(self, name, getattr(lpbug, name))

        # copy fields from JSON internals to avoid additional "lazy init" queries to LP (as it would kill performance)
        for name in FIELDS_TO_COPY_FROM_JSON:
            setattr(self, name, lpbug._wadl_resource.representation[name])

        # extract assignee (i.e. https://api.launchpad.net/1.0/~dshulyak -> dshulyak)
        self.assignee = str(self.assignee_link).rsplit('~', 1)[-1]
        self.assignee_link = "https://launchpad.net/~" + self.assignee
        if (self.assignee is None) or (self.assignee == "None"):
            self.assignee = ""
            self.assignee_link = ""

        # extract milestone (i.e. https://api.launchpad.net/1.0/fuel/+milestone/4.1 -> 4.1)
        self.milestone = str(self.milestone_link).rsplit('/', 1)[-1]

        # extract title (i.e. Bug #1247284 in Fuel for OpenStack: "Verify Networks doesn't wait long enough for dhcp response")
        self.title = self.sanitize_string(self.title).split(':', 1)[1].strip(" \"")

        # extract id from web link (i.e. https://bugs.launchpad.net/fuel/+bug/1247284 -> 1247284)
        self.id = str(self.web_link).rsplit('/', 1)[-1]

    def get_status_changes(self):
        # Bug flow:
        # 1. New (not targeted to any release)  ->  date_created
        # 2. Open      -> date_triaged (date_confirmed, date_left_new, date_assigned). if still None, then date_in_progress
        # 3. Resolved  -> date_fix_committed
        # 4. Verified  -> date_fix_released
        # also, may be 5. Incomplete -> date_incomplete

        result = []

        # When the bug was assigned to the release
        date_open = self.date_triaged;
        if date_open is None:
            date_open = self.date_confirmed
        if date_open is None:
            date_open = self.date_left_new
        if date_open is None:
            date_open = self.date_assigned
        if date_open is None:
            date_open = self.date_in_progress

        # When the bug was resolved or closed (e.g. as invalid)
        date_resolved = self.date_fix_committed
        if date_resolved is None:
            date_resolved = self.date_closed    

        # When the bug was verified
        date_verified = self.date_fix_released

        # When the bug was set as incomplete
        date_incomplete = self.date_incomplete

        # if the bug is "New", it should not be displayed on the chart
        if self.status in lpdata.LaunchpadData.BUG_STATUSES["New"]:
            return []

        # if the bug is "Incomplete", then our assumption is "Open" -> "Incomplete"
        if self.status in lpdata.LaunchpadData.BUG_STATUSES["Incomplete"]:
            if date_open > date_incomplete:
                return []
            result.append( {"date": date_open, "type": "Open"} )
            result.append( {"date": date_incomplete, "type": "Incomplete"} )

        # if the bug is "Open", then our assumption is "Open". And it's not currently resolved
        if self.status in lpdata.LaunchpadData.BUG_STATUSES["Open"]:
            result.append( {"date": date_open, "type": "Open"} )

        # if the bug is "Closed" (but not verified), then our assumption is "Open" -> "Resolved" 
        if (self.status in lpdata.LaunchpadData.BUG_STATUSES["Closed"]) and (self.status != "Fix Released"):
            if date_open > date_resolved:
                return []
            result.append( {"date": date_open, "type": "Open"} )
            result.append( {"date": date_resolved, "type": "Resolved"} )

        # if the bug is "Verified", then our assumption is "Open" -> "Resolved" -> "Verified"
        if (self.status in lpdata.LaunchpadData.BUG_STATUSES["Closed"]) and (self.status == "Fix Released"):
            if date_open > date_resolved:
                return []
            result.append( {"date": date_open, "type": "Open"} )
            result.append( {"date": date_resolved, "type": "Resolved"} )

            if date_verified is None:
                date_verified = date_resolved

            result.append( {"date": date_verified, "type": "Verified"} )

        return result
