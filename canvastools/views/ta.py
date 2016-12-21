from flask import Blueprint
from flask import render_template
from flask import request
from app import app
import json
import cx_Oracle

TA = Blueprint('ta',__name__)

# display page
@TA.route('/ta')
def ta():
    user = {'nickname':'Akshay'} #fake user
    return render_template('ta.html',title = 'Teaching Assistants',user=user)


# return database result 
@TA.route('/ta',methods=['POST'])
def getFromDB():
    user = {'nickname': 'Akshay'}  # fake user
    school = request.form['school']
    dept = request.form['dept']
    role = request.form['role']
    term = request.form['term']
    csvName = ''

    with open('/home/vagrant/coldfusion-python/app/config.json') as json_data_file:
        CONFIG = json.load(json_data_file)

    conn = cx_Oracle.connect(CONFIG['cx']['user'], CONFIG['cx']['passwd'], CONFIG['cx']['db'])
    curr = conn.cursor()
    
    # database query begin

    query = """  SELECT s.SITE_ID, ro.ROLE_NAME, m.eid as UNI, u.FIRST_NAME, u.LAST_NAME, c.SIS_SCHOOL, c.SIS_DEPARTMENT, c.SIS_TERM
               FROM sakai_user_id_map m
               INNER JOIN sakai_site_user su   ON m.user_id = su.user_id
               INNER JOIN sakai_site s         ON su.site_id = s.SITE_ID
               INNER JOIN sakai_realm r        ON r.realm_id like '%/site/' || s.SITE_ID
               INNER JOIN sakai_user u         ON u.user_id = m.user_id
               INNER JOIN sakai_realm_rl_gr g  ON g.realm_key = r.realm_key AND g.user_id = su.user_id
               INNER JOIN sakai_realm_role ro  ON ro.role_key = g.role_key
               INNER JOIN cu_realm_rl_gr cr    ON cr.realm_id = r.realm_id AND cr.user_id = su.user_id
               INNER JOIN cu_course_site c     ON s.SITE_ID = c.site_id
               WHERE ro.ROLE_NAME IN (\'Teaching Assistant\', \'Enhanced TA\', \'Staff Assistant\')"""
    if len(school)>0:
        query += 'AND c.SIS_SCHOOL =\'%s\'' % str(school)
        csvName += str(school)+'_'
    if len(dept)>0:
        query += 'AND c.SIS_DEPARTMENT =\'%s\'' % str(dept)
        csvName += str(dept)+'_'
    if len(role)>0:
        query += 'AND ro.ROLE_NAME =\'%s\'' % str(role)
        csvName += str(role)+'_'
    if len(term)>0:
        query += 'AND c.SIS_TERM =\'%s\'' % str(term)
        csvName += str(term)

    query += 'ORDER BY s.SITE_ID, UNI, u.LAST_NAME, u.FIRST_NAME, ro.ROLE_NAME, c.SIS_SCHOOL, c.SIS_DEPARTMENT, c.SIS_TERM'
    
    # database query end
    
    curr.execute(query)
    query_result = curr.fetchall()
    num_rows = len(query_result)
    # print(str(num_rows)+' rows fetched successfully')
    # print('end of result')
    if(num_rows>0):
        return_table = ("\"<table class ='table' id='exportTable'>"
        "<tr>"
        " <th>S.No.</th>"
        " <th>Site</th>"
        " <th>UNI</th>"
        " <th>Last</th>"
        " <th>First</th>"
        " <th>Role</th>"
        " <th>School</th>"
        " <th>Department</th>"
        " <th>Team</th>"
        "</tr>"
        )
        i = 0
        semester_word = ""
        for row in query_result:
            i += 1
            semester_code = row[7]
            
            # handling conversion of 1 to Spring, 2 to Summer and 3 to Fall
            
            if(semester_code[-1:]=='1'):
                semester_word = 'Spring '+semester_code[0:-1]
            elif(semester_code[-1:]=='2'):
                semester_word = 'Summer '+semester_code[0:-1]
            else:
                semester_word = 'Fall '+semester_code[0:-1]

            return_table +=  ("<tr>"
                "<td>"+str(i)+"</td>"
                "<td>"+row[0]+"</td>"
                "<td>"+row[2]+"</td>"
                "<td>"+row[3]+"</td>"
                "<td>"+row[4]+"</td>"
                "<td>"+row[1]+"</td>"
                "<td>"+row[5]+"</td>"
                "<td>"+row[6]+"</td>"
                "<td>"+semester_word+"</td>"
               "</tr>"
            )
        return_table +='</table>\"'
    else:
        return_table = "\'<h3> no records found for the selected parameters.</h3>\'"
    return render_template('ta.html',title = 'Teaching Assistants',user=user,tablehtml = return_table.strip(),csvName = csvName)

