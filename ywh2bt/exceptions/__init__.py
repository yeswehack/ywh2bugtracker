"""
Specific Exceptions
"""


class BugTrackerNotFound(Exception):
    """
    Exceptions for non exitsing Bugtracker
    """

    pass


class MultipleBugTrackerMacth(Exception):
    """
    Exception for multiple Bugtracker having the same type identifier.
    """

    pass
