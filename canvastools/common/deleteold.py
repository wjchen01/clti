"""
Delete old photo authorizations from database
Angus Grieve-Smith for Columbia University IT
"""
import os
import json
import cx_Oracle

CONFIGPATH = '/var/www/html/tlaservice-web/instance'


def deleteold():
    """
    Delete old photo authorizations from database
    """
    result = "Error: unable to open config file " + CONFIGPATH
    with open(os.path.join(CONFIGPATH, 'app.json')) as json_data_file:
        config = json.load(json_data_file)
        print("Working with database " + config['dbserver'])

    with open(
        os.path.join(CONFIGPATH, config['dbserver'] + '.json')
                     ) as json_data_file:
        dbconfig = json.load(json_data_file)
        conn = cx_Oracle.connect(
            dbconfig['cx']['user'],
            dbconfig['cx']['passwd'],
            dbconfig['cx']['db']
            )
        curr = conn.cursor()
        delq = "delete from photoauth where time < sysdate - interval '15' minute"
        try:
            curr.execute(delq)
            result = "Deleted " + str(curr.rowcount) + " rows from photoauth."
        except cx_Oracle.DatabaseError as exc:
            result = "Database error: " + exc.args[0].message
        conn.commit()
        curr.close()
        conn.close()
    print(result)

if __name__ == "__main__":
    deleteold()
