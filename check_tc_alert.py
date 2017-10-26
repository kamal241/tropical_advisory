import json
import os
from math import cos, sin, asin, sqrt, radians
from trpcl_adv_fpath import *
import glob
import datetime

def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

         # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        dinkm = c * r
        return dinkm

def adjust_time(tin,cyear,tzo):
	tindt = datetime.datetime.strptime(tin,"%d/%H%MZ")
	tindt.replace(year=cyear)
	td = datetime.timedelta(hours=tzo)
	ndt = tindt + td
	sdt = ndt.strftime("%d/%H%MZ")
	return sdt
	

def get_ta_text(f,**kwargs):
	tzo = 0
	if 'tzo' in kwargs:
		tzo = kwargs['tzo']
	cdt = datetime.datetime.now()
	cyear = int(cdt.strftime("%Y"))
	
	if os.path.exists(f):
		with open(f,'r') as taf:
			ta_json = json.load(taf)
#			pr = ta_json["properties"]
			pr = ta_json
			if ta_json["type"]!="":
				hrst_fname = "%s %s %s" % (pr["type"], pr["cy_or_st"], pr["name"])
			else:
				hrst_fname = "%s %s" % (pr["cy_or_st"], pr["name"])
			advnum = pr["adv_num"]
			cloc = pr["location"]
			cmov = pr["movement"]
			loc_coord = "%.1f%s/%.1f%s" % (cloc["lat"], cloc["latd"], cloc["lon"], cloc["lond"])
			ftime = adjust_time(pr["time"],cyear,tzo)
#			ta_name_center = "%s. Center located near %s at %s. " % (hrst_fname, loc_coord, pr["time"])
			ta_name_center = "%s. Center located near %s at %s. " % (hrst_fname, loc_coord, ftime)
			ta_mov = "Present movement toward %s at %dKT Max winds %d/%dKT. " % (cmov["dirn"], cmov["speed"], cmov["msw"], cmov["gusts"])
			tropical_adv = ta_name_center + ta_mov
			fvalids = pr['forecast']['features']
			ovalids = pr['outlook']['features']

			if fvalids:
				fv = fvalids[len(fvalids)-1]
				fvp = fv["properties"]
				floc = "%.1f%s/%.1f%s" % (fvp["lat"], fvp["latd"], fvp["lon"], fvp["lond"])
				fwg = "%d/%dKT" % (fvp["maxwinds"], fvp["gusts"])
				fvmtime = adjust_time(fvp["time"],cyear,tzo)
				#ta_forecast = "Forecast %s %s Max winds %s. " % (fvp["time"], floc, fwg)
				ta_forecast = "Forecast %s %s Max winds %s. " % (fvmtime, floc, fwg)
				tropical_adv = tropical_adv + ta_forecast
			if ovalids:
				ov = ovalids[0]
				ta_outlook = ""
				ovp = ov["properties"]
				oloc = "%.1f%s/%.1f%s" % (ovp["lat"], ovp["latd"], ovp["lon"], ovp["lond"])
				owg = "%d/%dKT" % (ovp["maxwinds"], ovp["gusts"])
				ovmtime = adjust_time(ovp["time"],cyear,tzo)
				#ta_outlook = "Outlook %s %s Max winds %s. " % (ovp["time"], oloc, owg)
				ta_outlook = "Outlook %s %s Max winds %s. " % (ovmtime, oloc, owg)
				tropical_adv = tropical_adv + ta_outlook

			return advnum, tropical_adv



def get_tc_alerts(fn):
	"""Read GeoJSON file containing Latest Advisory report and return dictionary"""
	fa_data = None
	with open(fn,'r') as faf:
		fa_data = json.load(faf)
	return fa_data

def check_tc_alert(loc):
#	trpadv_path = '/syndata/trpcl_adv'
        fpath = os.path.join(trpadv_path,'ALERTS','*.json')
#               print fpath
        files = glob.glob(fpath)
#	print files
	hs_effective = {}
	for file in files:
	        jsonf_path = file #os.path.join(trpadv_path,'ALERTS',"%s.json" % 'AL172017')
		is_within_tc =  False
	 	if os.path.exists(jsonf_path):
			fa_raw = get_tc_alerts(jsonf_path)
			for idx,ft in enumerate(fa_raw['forecast']['features']):
				fa_loc = ft['geometry']['coordinates']
				fa_dist = haversine(loc[0],loc[1],fa_loc[0],fa_loc[1])
				is_within_tc =  is_within_tc or fa_dist<=1500.00
				if is_within_tc:
					hs_effective[int(fa_dist)] = file #.append(file)
					break

			if not is_within_tc:
				for idx,ft in enumerate(fa_raw['outlook']['features']):
					fa_loc = ft['geometry']['coordinates']
					fa_dist = haversine(loc[0],loc[1],fa_loc[0],fa_loc[1])
					is_within_tc =  is_within_tc or fa_dist<=1500.00
		#			if fa_dist<=1500.00:
		#				is_within_tc = True
		#			print idx,":",loc,fa_loc,fa_dist, is_within_tc, fa_dist<=1500.00
					if is_within_tc:
						hs_effective[int(fa_dist)] = file #.append(file)
 						break
	return hs_effective

def sendFAEmail(fas):
	"""
        server= smtplib.SMTP('smtp.domain.com',587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login("dev.test@synergy-wave.com", "Test-Now2017")
	"""
        for fa in fas:
		etext = "*"*50 + "\n"
		etext = etext +  "%s\t#%d\n" % (fa['tc_id'],fa['adv_num'])
		etext = etext + "*"*50 + "\n"
		etext = etext + fa['ta_text'] + "\n"
		etext = etext + "$"*50 + "\n"
		print etext
        #server.quit()

if __name__ == "__main__":
	tzo = 8.0
	loc = [335.0,35.0]
#	loc = [96.15205111,14.239496]
	tas = []
	effective_hs = check_tc_alert(loc)
	#print effective_hs
	for d,ehsf in effective_hs.items():
		fn = os.path.basename(ehsf)
		tc_id = fn.split('.')[0]
		an, tt = get_ta_text(ehsf,tzo=tzo)
		dta = {}
		dta['adv_num']=an
		dta['distance']=d
		dta['tc_id']=tc_id
		dta['ta_text']=tt
		tas.append(dta)
	print tas
	sendFAEmail(tas)

	"""
	ta_texts = {}
	for d,ehsf in effective_hs.items():
		tt = get_ta_text(ehsf)
	"""


