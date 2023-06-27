import yaml

class quoted(str):
    pass

def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
yaml.add_representer(quoted, quoted_presenter)

env_dict = {"version" : quoted("0.3.0")}

print(yaml.dump(env_dict, default_flow_style=False))