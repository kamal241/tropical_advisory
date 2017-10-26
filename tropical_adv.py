import bs4
from bs4 import BeautifulSoup
import requests
import re
import os
import sys
from fa_parser import *
from trpcl_adv_fpath import *

def get_fa(url):
	result = requests.get(url)
	if result.status_code == 200:
		fa_content = result.content
		fa_bs = BeautifulSoup(fa_content,'html.parser')	
		adv_div = fa_bs.find('div', class_='textproduct')
		adv_text = adv_div.find('pre')
		return adv_text.text


def get_adv():
	result = requests.get("http://www.nhc.noaa.gov/cyclones/?atlc")
	if result.status_code==200:
		return result
	return None
	#if result.status_code==200:

def check_for_adv(rcontent):
	soup = BeautifulSoup(rcontent,'html.parser')
	cyclone_storm_div = soup.find("div", id="cyclones_stormTable")
	fas = cyclone_storm_div.select("a > br")
	return fas

def parse_ta(fn):
	nhc_fa = NHCParser(filename=fn)
	nhc_fa.set_paras()
	nhc_fa.parse_headers()
	nhc_ta = nhc_fa.generate_tropical_adv()
	nhc_fc = nhc_fa.get_current_state()
	print nhc_ta

if __name__ == "__main__":
#	dt = '20171012'
	dt = sys.argv[1]
	print trpadv_path
#	trpadv_path = '/syndata/trpcl_adv'
	trpadv_dt_path = os.path.join(trpadv_path,'data',dt)
	result = get_adv()
	url_re = re.compile('(?P<other>.*)/(?P<cat>.*).+shtml/(?P<uid>.*).shtml')
	if result is not None:
		ta_raw_content = result.content
		#soup = BeautifulSoup(ta_raw_content,'html.parser')
		#cyclone_storm_div = soup.find("div", id="cyclones_stormTable")
		fas_pattern = re.compile(".*ForecastAdvisory.*", flags=re.DOTALL)
		#fas = cyclone_storm_div.select("a > br")
		fas = check_for_adv(ta_raw_content)
		active_alerts = {}
		base_url = 'http://www.nhc.noaa.gov' 
		for fa in fas:
			fa_texti = fa.parent.text
			#print fa_texti
			isMatch = fas_pattern.match(fa_texti)
			if isMatch:
				fau = fa_texti.split('\n')
				fau = [fai for fai in fau if fai.strip() != '' ]
				akey = fau[1]
				aurl = fa.parent['href']
				cat_uid_m = url_re.match(aurl)
				tc_fa = cat_uid_m.groupdict()
				tc_fa['url'] = base_url + aurl
				tc_fa['adv_num'] = akey.lstrip('#')
				active_alerts[tc_fa['uid']] = tc_fa

				#text/refresh/MIATCMAT2+shtml/121432.shtml
#		print active_alerts
		for uid, adv  in active_alerts.items():
			print uid, adv
			fn = '%s_%s.txt' %(uid,adv['adv_num'])
			adv_raw_file = os.path.join(trpadv_dt_path,fn)
			if os.path.exists(adv_raw_file):
				print "No Latest Advisories"
				print "Advisory \#%s for %s already exists" % (adv['adv_num'],uid)
				#parse_ta(adv_raw_file)

			else:
				adv_raw_data = get_fa(adv['url'])
				with open("%s" % adv_raw_file,'w') as faf:
					faf.write(adv_raw_data)
				if os.path.exists(adv_raw_file):
					print "%s created successfully" % adv_raw_file
					parse_ta(adv_raw_file)
	else:
		print "URL Could not be reaced. HTTP STATUS CODE : %d" % result.status_code



