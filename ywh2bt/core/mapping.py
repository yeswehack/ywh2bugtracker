"""Synchronizer mapping between tracker configurations and tracker clients."""
from types import MappingProxyType
from typing import Any, Mapping, Type

from ywh2bt.core.api.tracker import TrackerClient
from ywh2bt.core.api.trackers.github.tracker import GitHubTrackerClient
from ywh2bt.core.api.trackers.gitlab import GitLabTrackerClient
from ywh2bt.core.api.trackers.jira.tracker import JiraTrackerClient
from ywh2bt.core.configuration.tracker import TrackerConfiguration
from ywh2bt.core.configuration.trackers.github import GitHubConfiguration
from ywh2bt.core.configuration.trackers.gitlab import GitLabConfiguration
from ywh2bt.core.configuration.trackers.jira import JiraConfiguration

TrackerClientClassesType = Mapping[
    Type[TrackerConfiguration],
    Type[TrackerClient[Any]],
]
TRACKER_CLIENT_CLASSES: TrackerClientClassesType = MappingProxyType({
    GitHubConfiguration: GitHubTrackerClient,
    GitLabConfiguration: GitLabTrackerClient,
    JiraConfiguration: JiraTrackerClient,
})
