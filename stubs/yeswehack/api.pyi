from typing import Any, Dict, List, Optional, Union

import requests


class YesWeHack:
    token: str
    api_url: str
    username: str
    password: str
    lazy: bool
    verify: bool
    oauth_mode: bool
    oauth_args: Dict[str, str]
    session: object
    apps_headers: object
    managed_pgms: List[Any]

    def __init__(
        self,
        **kwargs: Any,
    ) -> None: ...

    def login(
        self,
    ) -> bool: ...

    def get_reports(
        self,
        program: str,
        filters: Optional[Dict[str, Any]],
        lazy: bool = False,
    ) -> List[Report]: ...

    def get_report(
        self,
        report: Union[str, int],
        lazy: bool = False,
    ) -> Report: ...

    def post_comment(
        self,
        report_id: Union[str, int],
        comment: str,
        private: bool = False,
    ) -> Log: ...


class Priority:
    name: str
    slug: str
    level: int
    color: str


class Category:
    name: str


class Attachment:
    ywh_api: YesWeHack
    id: int
    name: str
    original_name: str
    mime_type: str
    size: int
    url: str
    data: bytes

    def load_data(self) -> None: ...


class BugType:
    category: Category
    description: str
    link: str
    name: str
    remediation_link: str
    slug: str


class Author:
    ywh_api: YesWeHack
    username: str
    slug: str
    hunter_profile: Dict[str, Any]
    avatar: Attachment


class CVSS:
    criticity: str
    score: float
    vector: str


class Log:
    ywh_api: YesWeHack
    created_at: str
    duplicate_of: Dict[str, Any]
    id: int
    type: str
    points: int
    private: bool
    author: Author
    canceled: bool
    cvss_bonus: int
    old_status: Optional[Dict[Any, Any]]
    status: Optional[Dict[Any, Any]]
    message_html: str
    attachments: List[Attachment]
    old_cvss: CVSS
    new_cvss: CVSS
    priority: Priority
    old_bug_type: BugType
    new_bug_type: BugType
    old_tags: List[Any]
    new_tags: List[Any]
    reward_type: str
    bounty_reward_amount: int
    marked_as: str
    rights: List[Any]
    old_details: Optional[Dict[str, Any]]
    new_details: Optional[Dict[str, Any]]
    tracker_name: Optional[str]
    tracker_url: Optional[str]
    tracker_id: Optional[str]
    tracker_token: Optional[str]


class Report:
    ywh_api: YesWeHack
    id: int
    application_finger_print: str
    attachments: List[Attachment]
    bonus: int
    bug_type: BugType
    chainable: bool
    chainable_exploit_description_html: str
    chainable_report: Dict[str, Any]
    created_at: str
    cvss: CVSS
    cvss_bonus: int
    description_html: str
    duplicate_of: Dict[str, Any]
    end_point: str
    hunter: Dict[Any, Any]
    local_id: str
    logs: List[Log]
    marked_as: str
    part_name: str
    payload_sample: str
    priority: Priority
    program: Dict[Any, Any]
    reward: int
    rights: List[Any]
    scope: str
    source_ips: List[str]
    status: Dict[Any, Any]
    tags: List[Any]
    technical_information: str
    technical_information_html: str
    title: str
    tracking_status: str
    vulnerable_part: str

    def put_tracking_status(
        self,
        tracking_status: str,
        tracker_name: str,
        tracker_url: str,
        tracker_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> requests.Response: ...

    def post_tracker_update(
        self,
        tracker_name: str,
        tracker_url: str,
        tracker_id: Optional[str]=None,
        token: Optional[str]=None,
        message: Optional[str]=None,
    ) -> requests.Response: ...

    def post_comment(
        self,
        comment: str,
        private: bool = False,
    ) -> Log: ...


class Program:
    ywh_api: YesWeHack
    reports: List[Report]
    disabled: bool
    managed: bool
    bounty_reward_max: int
    reports_count: int
    status: str
    title: str
    slug: str
    banner: Dict[Any, Any]
    rules: str
    rules_html: str
    public: bool
    hall_of_fame: bool
    scopes: List[Any]
    out_of_scope: List[Any]
    qualifying_vulnerability: List[Any]
    non_qualifying_vulnerability: List[Any]
    bounty: bool
    gift: bool
    bounty_reward_min: int
    disclose_bounty_min_reward: bool
    disclose_bounty_average_reward: bool
    disclose_bounty_max_reward: bool
    reward_grid_default: Dict[Any, Any]
    reward_grid_low: Dict[Any, Any]
    reward_grid_medium: Dict[Any, Any]
    reward_grid_high: Dict[Any, Any]
    tags: List[Any]
    business_unit: Dict[Any, Any]
    restricted_ips: List[str]
    vpn_active: bool
    vpn_ips: List[str]
    account_access: str
    disable_message: str
    user_agent: str
    stats: Dict[Any, Any]
    event: Dict[Any, Any]
    token: str
    rights: List[Any]
