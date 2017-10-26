# -*- coding: utf-8 -*-
import bs4
from bs4 import BeautifulSoup
import requests
import re
import datetime
from rangedict import RangeDict
import os
import sys
import json
from trpcl_adv_fpath import *
from jtwc_parser import *

def parse_ta(fn):
	jtwc_fa = JTWCForecastAdvisoryParser(filename=fn)
	jtwc_fa.set_paras()
	jtwc_ta = jtwc_fa.get_adv()
	jtwc_fc = jtwc_fa.get_current_state()

def get_jtwc_rss():
	__jtwc_updatef_re = re.compile(re.compile('(?P<tc_id>.*)web.txt'))
	jtwc_rss_url = 'http://www.usno.navy.mil/NOOC/nmfc-ph/RSS/jtwc/warnings/'
	result = requests.get(jtwc_rss_url)
	jtwc_content = result.content
	jtwc_rss_bs = BeautifulSoup(jtwc_content,'html.parser')
	jtwc_feeds_table = jtwc_rss_bs.find('table')
	allfs = jtwc_feeds_table.findAll('a',text=re.compile('(.*)web.txt',flags=re.DOTALL))
	jtwc_updates = {}

	for fs in allfs:
		jtwc_up_m = __jtwc_updatef_re.match(fs['href'])
		if jtwc_up_m:
			jtwc_updates[jtwc_up_m.groupdict()['tc_id']] = jtwc_rss_url + fs['href']
	return jtwc_updates


def get_jtwc_raw_file(url):
	result = requests.get(url)
	#print result.status_code
	fa_content = result.content
	return fa_content

def get_fa_fnames(dt,rssups):
	#WTPN31 PGTW 160300
	#trpadv_dt_path = os.path.join(trpadv_path,'data',dt)
	#dt= '20171016'
	#trpadv_dt_path = os.path.join('.','FAs','data',dt)
	trpadv_dt_path = os.path.join(trpadv_path,'data',dt)
	__id_re = re.compile("(?P<tc_id>.*)\s+(?P<id_type>.*)\s+(?P<issue_time>.*)\r")
	__jtwc_start_re = re.compile("(?P<seq_num>\d*)\.\s*(?P<type>.*\s)?(?P<kind>HURRICANE|CYCLONE|STORM|DEPRESSION|DISTURBANCE|TYPHOON|REMNANTS)\s+(?P<name>.*)\s+(WARNING)\s+NR\s+(?P<number>.*)\r")
	for key,url in rssups.items():
		try:
			fcontent = get_jtwc_raw_file(url)
			flines = fcontent.split('\n')
			total_lines = len(flines)
			found_header =False
			is_eof = False
			id_m = __id_re.match(flines[0])
			if id_m:
				ids_d = id_m.groupdict()
				#print ids_d
				lindex = 1
				while (not found_header) and (not is_eof):
					jtwc_m = __jtwc_start_re.match(flines[lindex])
					if jtwc_m:
						found_header = True
						jtwc_header = jtwc_m.groupdict()
						#print jtwc_header
					lindex = lindex + 1
					if lindex >= total_lines:
						is_eof = True


				#nfn = "%s_%s.txt" % (ids_d['tc_id'], ids_d['issue_time'])
				nfn = "%s_%s_%03d.txt" % (ids_d['tc_id'], ids_d['issue_time'],int(jtwc_header['number'].strip()))
				adv_raw_file = os.path.join(trpadv_dt_path,nfn)
				if os.path.exists(adv_raw_file):
					print "No Latest Advisories"
					print "Advisory %s for %s already exists" % (ids_d['tc_id'], ids_d['issue_time'])
					parse_ta(adv_raw_file)
				else:
					with open(adv_raw_file, "w") as uff:
						uff.write(fcontent)
					if os.path.exists(adv_raw_file):
						print "%s created successfully" % adv_raw_file
						parse_ta(adv_raw_file)
		except Exception as ex:
			print ex


if __name__ == "__main__":
        dt = sys.argv[1]
	rss_updates = get_jtwc_rss()
	get_fa_fnames(dt,rss_updates)
