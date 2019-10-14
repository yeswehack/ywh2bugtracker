
import getpass

def read_input(text, secret=False):
    print(text, flush=True, end="")
    if secret:
        return getpass.getpass(prompt='')
    return input()


def get_all_subclasses(cls, ret=None, cls_attr_filter={}):
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
