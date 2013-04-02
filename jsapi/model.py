from bitdeli.model import model

@model
def build(profiles):
    for profile in profiles:
        for tstamp, group, ip, event in profile['events']:
            for key, value in event.iteritems():
                if key != 'id':
                    yield '%s:%s' % (key, value), profile.uid  

