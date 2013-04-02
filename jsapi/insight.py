from bitdeli.insight import insight
from bitdeli.widgets import Widget, Table, Text
from itertools import starmap

PIVOT = 'initial_prompts_setting'

FILTERS = ['valid_user', 'new_user', 'first', 'geoip',
           'changed_prompts_setting', 'impressions']

METRICS = [('sum', 'impressions'),
           ('sum', '1-day-retention:1'),
           ('sum', '3-day-retention:1'),
           ('sum', '7-day-retention:1'),
           ('sum', '1-week-retention:1'),
           ('avg', '1-day-retention:1'),
           ('avg', '3-day-retention:1'),
           ('avg', '7-day-retention:1'),
           ('avg', 'day1:1'),
           ('avg', '1-week-retention:1')]

COLUMNS = [{'name': 'metric', 'label': 'Metric', 'row_header': True},
           {'name': 'false', 'label': 'FALSE'},
           {'name': 'true', 'label': 'TRUE'},
           {'name': 'total', 'label': 'Total', 'cell': 'markdown'},
           {'name': 'uplift', 'label': 'Uplift'}]

COLOR = {True: lambda x: 'rgba(255, 36, 0, %f)' % min(0.8, x),
         False: lambda x: 'rgba(0, 163, 89, %f)' % min(0.8, x)}

class TokenInput(Widget):
    pass

def prefixes(prefix, model):
    for key in model:
        k, v = key.split(':')
        if k == prefix:
            yield key, v

def num_users(model, query):
    return len(model.query(' & '.join(query)))
            
def metric(prefix, model, query):
    if ':' in prefix:
        total = num_users(model, [prefix] + query)
        num = num_users(model, query)
    else:
        num = total = 0
        for key, value in prefixes(prefix, model):
            n = num_users(model, [key] + query)
            total += n * int(value)
            num += n
    return total, total / float(num) if num else 0.
   

def make_filters(model, params):
    yield Text(data={'text': '**Filters**'}, size=(2, 3))
    for prefix in FILTERS:
        args = {'id': prefix,
                'label': prefix,
                'data': [v for k, v in prefixes(prefix, model)],
                'size': (4, 1)}
        if prefix in params:
            args['value'] = [params[prefix]['value'][0]]
        yield TokenInput(**args)

def make_table(filters, model, label):
    def cells(metric, true, false, total, uplift=None):
        def fmt(x):
            return '%.3f' % x if type(x) == float else x
        
        r = {'metric': {'label': metric.split(':')[0],
                        'background': '#f3f3f3'},
             'true': fmt(true),
             'false': fmt(false),
             'total': '**%s**' % fmt(total)}
        
        if uplift != None:
            r['uplift'] = {'label': '%.2f%%' % (uplift * 100.),
                           'background': COLOR[uplift < 0](abs(uplift))}
        return r

    def row(type, field):    
        true, false = [metric(field, model, filters + ['%s:%s' % (PIVOT, col)])
                       for col in ('TRUE', 'FALSE')]     
        label = '%s - %s' % (type, field)
        if type == 'sum':
            return cells(label, true[0], false[0], true[0] + false[0])
        else:
            total =  (true[1] + false[1]) / 2.
            uplift = true[1] / false[1] - 1. if abs(false[1]) > 0.00001 else 0.
            return cells(label, true[1], false[1], total, uplift)
   
    counts = [num_users(model, ['%s:%s' % (PIVOT, col)] + filters)
              for col in ('TRUE', 'FALSE')]
    rows = [cells('Count - id', counts[0], counts[1], sum(counts))]
                  
    return Table(columns_label=PIVOT,
                 size=(12, 'auto'),
                 label=label,
                 data={'rows': rows + list(starmap(row, METRICS)),
                       'columns': COLUMNS})
    
@insight
def view(model, params):
    filters = ['%s:%s' % (key, value['value'][0]) for key, value in params.items()]
    for filterbox in make_filters(model, params):
        yield filterbox
    yield make_table(filters,
                     model,
                     'Filters: ' + ' & '.join(filters) if filters else 'All data')

