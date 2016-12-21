import sys
import time
from datetime import datetime
from icalendar import Calendar
import requests

def acfy(year):
    return str(int(year) - 1982)

ACTERM = {
    'Spring': '7',
    'Summer': '8',
    'Fall': '6'
}

SCHOOL = {
    '9': 'Architecture, Planning & Preservation',
    '10': 'Business',
    '11': 'Columbia College',
    '13': 'School of Engineering & Applied Science (Graduate)',
    '14': 'School of Engineering & Applied Science (Undergraduate)',
    '15': 'School of General Studies',
    '16': 'Graduate School of Arts & Sciences',
    '17': 'Journalism',
    '18': 'School of International and Public Affairs',
    '19': 'School of the Arts',
    '20': 'School of Social Work',
    '40': 'Law School',
    '42': 'Medical Center',
    '43': 'School of Professional Studies'
}

WANTED = ['Day of Classes', 'University Holiday']
URL = 'http://registrar.wjchen.org/calendar/{year}+{term}{school}/subscribe.ics'

def getcal(term, year):
    acterm = ACTERM[term]
    acyear = acfy(year)

    event = {}

    for schi in [''] + list(SCHOOL.keys()):
        if len(schi) > 0: schi = '+'+schi

        calurl = URL.format(year=acyear, term=acterm, school=schi)
        cal = Calendar().from_ical(requests.get(calurl).text)

        for ev in cal.subcomponents:
            if ev.name == 'VEVENT' and (ev['summary'][-7:] == 'Holiday' or ev['summary'][-14:] == 'Day of Classes'):
                starttime = time.mktime(ev.decoded('DTSTART').timetuple())
            
                uid = str(ev['UID'])
                if uid not in event:
                    event[uid] = {}
                    event[uid]['summary'] = str(ev['summary'])
                    event[uid]['date'] = datetime.fromtimestamp(starttime)

    return event

if __name__ == '__main__':
    events = getcal(sys.argv[1], sys.argv[2])
    print(events)
