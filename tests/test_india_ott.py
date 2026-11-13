import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from generate_india_ott import parse, get_day, Release, render, uid

SAMPLE='''<h1>OTT Release Dates</h1><table>
<tr><th>Release date</th><th>Movie / Web series</th><th>Language</th><th>OTT platform</th><th>Details</th></tr>
<tr><td>Sat 14 Nov Confirmed Tomorrow</td><td><a href="/foo/">Crazy Kalyanam</a></td><td>Telugu</td><td>Aha</td><td>Movie page</td></tr>
<tr><td>Fri 20 Nov Expected In 7 days</td><td>Rumour</td><td>Hindi</td><td>Netflix</td><td></td></tr>
<tr><td>Fri 13 Nov Out today Today</td><td>Daayra</td><td>Hindi</td><td>Netflix</td><td></td></tr>
</table>'''
class CalendarTests(unittest.TestCase):
    def test_dated_confirmed(self):
        data=parse(SAMPLE,date(2026,11,13))
        self.assertEqual([x.title for x in data],["Daayra","Crazy Kalyanam"])
        self.assertIn("cinebuds.com/foo/",data[1].url)
    def test_boundary(self):
        self.assertEqual(get_day("Fri 1 Jan Confirmed",date(2026,12,20)),date(2027,1,1))
        self.assertEqual(get_day("Thu 31 Dec Released",date(2027,1,2)),date(2026,12,31))
    def test_time_uid_and_folding(self):
        a=Release("Anbil Avan",date(2026,11,13),"Tamil","SonyLIV")
        b=Release("Anbil Avan",date(2026,11,20),"Tamil","SonyLIV")
        self.assertEqual(uid(a),uid(b))
        ics=render([a])
        self.assertIn("DTSTART;TZID=America/Phoenix:20261113T080000",ics)
        self.assertIn("DTEND;TZID=America/Phoenix:20261113T090000",ics)
        self.assertTrue(all(len(line.encode("utf-8"))<=75 for line in ics.split("\r\n")))
if __name__=="__main__": unittest.main()
