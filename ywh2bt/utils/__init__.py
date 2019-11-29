import getpass
from .html2jira import html2jira

__all__ = ["read_input", "get_all_subclasses", "html2jira", "unescape_text"]


"""
Utils Module, define simply fonction.
"""


def unescape_text(text):
    for tag, value in {"&amp;": "&", "&lt;": "<", "&gt;": ">"}.items():
        text = text.replace(tag, value)
    return text


def read_input(text, secret=False):
    """
    Wrapper for input and getpass with color print text.
    :param text: text to  show before read input.
    :param bool secret: User input is invisible or not.
    """

    print(text, flush=True, end="")
    if secret:
        return getpass.getpass(prompt="")
    return input()


def get_all_subclasses(cls, ret=None, cls_attr_filter={}):
    """
    get subclasses from an ancestor recurively.
    You can use on attribute value filter.

    :param class cls: input class
    :param list ret: return list
    :param dict cls_attr_filter: filter for subclasse attribute on value.
    """
    for sub in cls.__subclasses__():
        keep = True
        for key, item in cls_attr_filter.items():
            if sub.__dict__.get(key, None) != item:
                keep = False
                break
        if keep:
            if ret is None or not isinstance(ret, list):
                ret = []
            ret.append(sub)
        get_all_subclasses(sub, ret=ret, cls_attr_filter=cls_attr_filter)
    return ret if ret is not None else []
