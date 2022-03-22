import yaml
with open('.taskcat.yml', 'r') as f:
    config = yaml.safe_load(f)
for v in config['project']['tests'].values():
    print(v['template'], end='')
    break
