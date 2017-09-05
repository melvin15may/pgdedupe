import pymssql
import collections
import unicodecsv as csv
import sys

PYTHON_VERSION = sys.version_info[0]


def unicode_to_str(data):
    if data == "":
        data = None
    if PYTHON_VERSION < 3:
        if isinstance(data, basestring):
            return data.encode('utf8')
        elif isinstance(data, collections.Mapping):
            return dict(map(unicode_to_str, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(unicode_to_str, data))
        else:
            return data
    else:
        if isinstance(data, str):
            return data
        elif isinstance(data, collections.Mapping):
            return dict(map(unicode_to_str, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(unicode_to_str, data))
        else:
            return data


def load_config(db={"database": "DATANEXUS_test", "host": "calv-sc-ctsidb.med.usc.edu", "password": "987654321spoj", "user": "MED\melvinm"}, table_name='test', config_table_name='config'):
    """
    Load configuration from a table
    db: database credentials
    table_name: name of table to be deduplicated
    config_table_name : name of configuration table (default: 'config')
    """
    con = pymssql.connect(**db)
    cursor = con.cursor(as_dict=True)

    config = {}

    """
    Get basic details from table
	START
	"""

    cursor.execute("""SELECT 
    						"schema",
							"table",
							"key",
							filter_condition,
							prompt_for_labels,
							recall,
							training_file,
							seed
		 				FROM {config_table_name}
		 				WHERE "table" = '{table_name}' AND "key" is not null""".format(config_table_name=config_table_name, table_name=table_name))

    row = cursor.fetchone()
    if row is not None:
        row = unicode_to_str(row)
        if row['filter_condition'] is None or row['filter_condition'] == '':
            del row['filter_condition']
        if row['seed'] is None or row['seed'] == '':
            row['seed'] = 0
        config = row
    else:
        raise Exception("'{table_name}' not found in configuration table".format(
            table_name=table_name))

    """
    END
    """

    """
    Get all fields
	START
	"""
    cursor.execute("""
    	SELECT 
    		field,
    		field_type,
    		field_has_missing,
    		categories
    	FROM {config_table_name}
    	WHERE "table"= '{table_name}' AND "field" is not null
    """.format(config_table_name=config_table_name, table_name=table_name))

    fields = []
    categorical_fields = {}
    for row in cursor:
        row = unicode_to_str(row)
        if row['field_has_missing'] is None or row['field_has_missing'] == '':
            row['field_has_missing'] = False
        row['type'] = row['field_type']
        row['has_missing'] = row['field_has_missing']
        del row['field_type']
        del row['field_has_missing']
        if row['type'] != 'Categorical':
            fields.append(row)
        else:
            if row['field'] in categorical_fields:
                categorical_fields[row['field']]['categories'].append(row['categories'])
            else:
                row['categories'] = [row['categories']]
                categorical_fields[row['field']] = row

    config['fields'] = fields + list(categorical_fields.values())
    """
    END
    """

    """
    Get all interactions
    START
    """
    cursor.execute("""
    	SELECT
    		interactions,
    		set_number
    	FROM {config_table_name}
    	WHERE "table"= '{table_name}' AND interactions is not null
    	ORDER BY set_number ASC
    	""".format(config_table_name=config_table_name, table_name=table_name))

    interactions = []
    prev_set = -1
    for row in cursor:
        row = unicode_to_str(row)
        if prev_set != row['set_number']:
            interactions.append([row['interactions']])
            prev_set = row['set_number']
        else:
            interactions[-1].append(row['interactions'])

    if len(interactions) > 0:
        config['interactions'] = interactions

    """
    END
    """

    """
    Get all merge_exacts
    START
    """
    cursor.execute("""
    	SELECT
    		merge_exact,
    		set_number
    	FROM {config_table_name}
    	WHERE "table"= '{table_name}' AND merge_exact is not null
    	ORDER BY set_number ASC
    	""".format(config_table_name=config_table_name, table_name=table_name))

    merge_exact = []
    prev_set = -1
    for row in cursor:
        row = unicode_to_str(row)
        if prev_set != row['set_number']:
            merge_exact.append([row['merge_exact']])
            prev_set = row['set_number']
        else:
            merge_exact[-1].append(row['merge_exact'])

    if len(merge_exact) > 0:
        config['merge_exact'] = merge_exact

    """
    END
    """

    print(config)

    cursor.close()


load_config(table_name='PROJECT')
