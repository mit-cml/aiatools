
import json


with open('appinventor-project-data.json') as f:
    data = json.load(f)
    print("projects\t%d" % data['projects'])
    for category in data['blocks']:
        print("blocks\t%s\t%d" % (category, sum(data['blocks'][category].values())))
    for component in data['designer']['components']:
        print("components\t%s\t%d" % (component, data['designer']['components'][component]['count']))
