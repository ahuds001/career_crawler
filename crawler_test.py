# Set of instructions to log into fake account and log out at the end. Need to know what the handles do

import mechanize
import cookielib
from bs4 import BeautifulSoup
import time
import nltk
import re
import itertools
import multiprocessing

# Browser
def Browser_Setup():
  br = mechanize.Browser()
  # Cookie Jar
  cj = cookielib.LWPCookieJar()
  br.set_cookiejar(cj)
  # Browser options
  br.set_handle_equiv(True)	# handle http headers embedded in HTML
  br.set_handle_gzip(True)	# handle compressed pages and media over the wire
  br.set_handle_redirect(True)	# handle pages with redirects (follow the redirect)
  br.set_handle_referer(True)   # handle referrer information in request (send)
  br.set_handle_robots(True)	# see robots.txt in wikipedia

# Follows refresh 0 but not hangs on refresh > 0
  br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
# User-Agent (this is cheating, ok?)
  br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
  return br,cj


# 'http://www.careerbuilder.com', 'statistics R', 'Chicago, Il'
def Job_Search(br,cj,url, keywords,location):
  br.open(url)
  br.select_form(nr=0)
  br.form['_ctl0:NavBar1:ucQuickBar:s_rawwords']=keywords
  br.form['_ctl0:NavBar1:ucQuickBar:s_freeloc']=location
  result=br.submit()
  page=result.get_data()
  return br,cj,page


# Finds the next url within the search page
# Note to self, for careerbuilder, it is class="jt prefTitle" 
def get_next_url(page):
  start_link=page.find('class="jt prefTitle"')
  if start_link==-1:
    return None, 0
  start_quote=page.find('<a',start_link-40)
  end_quote=page.find('</a>',start_quote+1)
  urlSoup=BeautifulSoup(page[(start_quote):(end_quote)])
  url=urlSoup.a
  url=url.get('href')
  return url, end_quote


# Uses get_next_url to get all the links in the page
def get_all_urls(page):
    links = []
    while True:
      url, endpos = get_next_url(page)
      if url:
        links.append(url)
        page = page[endpos:]
      else:
        break
    links.append(next_page_of_urls(page))
    return links


# Move to next page
def next_page_of_urls(page):
  start_link=page.find('class="nav_btm_cell"')
  start_quote=page.find('<a',start_link)
  end_quote=page.find('</a>',start_quote+1)
  if page[(end_quote-13):end_quote]=='Previous Page':  
    start_quote=page.find('<a',end_quote)
    end_quote=page.find('</a>',start_quote+1)
  if page[(end_quote-9):end_quote]!='Next Page':
    return None
  urlSoup=BeautifulSoup(page[(start_quote):(end_quote)])
  url=urlSoup.a
  url=url.get('href')
  return url


# used to travel to any other page once other urls found using other code and gets all data from this new page.
def Open_Link(br,cj,link):
  page=br.open(link)
  Job_sections=[str(br.title())]
  Job_sections.append(nltk.clean_html(page.get_data()))
  # Job_sections.append(page.get_data())
  Job_sections.append(link)
  return Job_sections


def Open_All_Links(br,cj,page):
  start=time.clock()
  Jobs=[]
  times=[]
  links=get_all_urls(page)
  while links[-1]!=None:
    result=br.open(links[-1])
    del links[-1]
    page=result.get_data()
    links2=get_all_urls(page)
    links=links+links2
  times.append(time.clock()-start)
  return links,times

def get_a_job(sleeper,link,jobs):
  br,cj=Browser_Setup()
  job_sections=Open_Link(br,cj,link)
  jobs.append(job_sections)
  time.sleep(2+sleeper[0])



def search_jobs_for_years_and_degrees(Jobs,SearchType):
  Experience,Degree=DegreeAndExperienceLists(Jobs)
  MinYears,MaxYears=SearchExp(Experience)
  Required_Degree=SearchDeg(Degree)
  if SearchType==1:
    Result_urls=Search1(Jobs,MinYears,Required_Degree,YearsExp,DegreeNumber)
  else:
    Result_urls=Search2(Jobs,MinYears,Required_Degree,YearsExp,DegreeNumber)
  return Result_urls


"""def DegreeAndExperience(Job_sections):
	Experience_Location=[
	m.start() 
	for m in re.finditer('years',Job_sections[1])
	]
	Degree_Location=[
	m.start() 
	for m in re.finditer('degree',Job_sections[1])
	]
	Sentence_Location=[
	m.start()
	for m in re.finditer('[.!?\n\t\r]',Job_sections[1])
	]
	Experience_Tuples=[
	(Sentence_Location[bisect_right(Sentence_Location,m)-1],Sentence_Location[bisect_right(Sentence_Location,m)])
	for m in Experience_Location
	]
	Degree_Tuples=[
	(Sentence_Location[bisect_right(Sentence_Location,m)-1],Sentence_Location[bisect_right(Sentence_Location,m)])
	for m in Degree_Location
	]
	words=['doctorate','phd','master','mba','ma','ms',,'bachelor','bs.','ba','bs','4 year','four year']
	exactMatch = re.compile(r'\b%s\b' % '\\b|\\b'.join(words))
	degrees=[
	exactMatch.findall(Job_sections[1][m[0]:m[1]])
	for m in Degree_Tuples
	]
	expyears=[
	re.findall(r'\d+', Job_sections[1][m[0]:m[1]])
	for m in Experience_Tuples
	]
	return expyears,degrees
"""

def bisect_right(a, x, lo=0, hi=None):
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)/2
        if x < a[mid]: hi = mid
        else: lo = mid+1
    return lo

def DegreeAndExperience(Job_sections):	
  Experience_Location = [
                          m.start()
                          for m in re.finditer('years',Job_sections[1], flags=re.IGNORECASE)
                        ]
  Sentence_Location = [
                        m.start()
                        for m in re.finditer('[.,!?\n\t\r]',Job_sections[1])
                      ]
  Experience_Tuples = [
                        (Sentence_Location[bisect_right(Sentence_Location,m)-1],Sentence_Location[bisect_right(Sentence_Location,m)])
                        for m in Experience_Location
                      ]
  words=['doctorate','phd','master','mba','ma','bachelor','ba','bs','4 year','four year','undergraduate']
  exactMatch = re.compile(r'\b%s\b' % '\\b|\\b'.join(words), flags=re.IGNORECASE)
  degrees = [
              exactMatch.findall(Job_sections[1])
            ]
  expyears = [
               re.findall(r'\d+', Job_sections[1][m[0]:m[1]])
               for m in Experience_Tuples
             ]
  return (expyears,degrees)

"""def Stuff(Jobs):
	start = time.clock()
	Results=[
		DegreeAndExperience(m)
		for m in Jobs]
	elapsed=(time.clock()-start)
	return Results,elapsed
"""
# Stuff is better than Stuff2 bu a factor of .05 in a 117 data set. in a 1000 data set it would be by .5 approximately?

def DegreeAndExperienceLists(Jobs):
  Results = [
              DegreeAndExperience(m)
              for m in Jobs
            ]
  Experience=[]
  Degree=[]
  for i in Results:
    Experience.append(list(itertools.chain(*i[0])))
    Degree.append(list(itertools.chain(*i[1])))
  return Experience,Degree

def SearchExp(Experience):
  Options = [
              int(i)
              for i in xrange(1,21,1)
            ]
  MinYears=[]
  MaxYears=[]
  for exp in range(0,len(Experience),1):
    IntExp = [
               int(i)
               for i in Experience[exp]
             ]
    if IntExp:
      try:
        MinYears.append(min(x for x in IntExp if x in Options))
        MaxYears.append(max(x for x in IntExp if x in Options))
      except:
        MinYears.append(100)
        MaxYears.append(100)
    else:
      MinYears.append(100)			
      MaxYears.append(100)
  return MinYears,MaxYears

def SearchDeg(Degree):
  words=['doctorate phd','master mba ma','bachelor ba bs 4 year four year undergraduate']
  Required_Degree=[]
  for deglist in Degree:
    if not deglist:
      Required_Degree.append(0)
    else:
      exactMatch = re.compile(r'\b%s\b' % '\\b|\\b'.join(deglist), flags=re.IGNORECASE)
      if len(exactMatch.findall(words[0]))>0:			
        Required_Degree.append(3)
        continue
      if len(exactMatch.findall(words[1]))>0:
        Required_Degree.append(2)
        continue
      if len(exactMatch.findall(words[2]))>0:
        Required_Degree.append(1)
        continue
  return Required_Degree

def Search1(Jobs,MinYears,Required_Degree,YearsWanted,DegWanted):
  Result_urls = [
                  (Jobs[i][0],Jobs[i][2])
                  for i in xrange(0,len(MinYears),1)
                  if (YearsWanted>MinYears[i] or MinYears[i]==100) and Required_Degree[i]<=DegWanted
                ]
  return Result_urls

def Search2(Jobs,MinYears,Required_Degree,YearsWanted,DegWanted):	
  Result_urls = [
                  (Jobs[i][0],Jobs[i][2])
                  for i in xrange(0,len(MinYears),1)
                  if YearsWanted>=MinYears[i]  and Required_Degree[i]<=DegWanted and Required_Degree[i]!=0
                ]
  return Result_urls

# Result_urls,elapsed=FullCombinedFunction('http://www.careerbuilder.com','statistics','Chicago, Il',2,1,'1 or 2')
# DegreeNumber: 1 = BS, 2=MS, 3=PHD, 0=None

def FullCombinedFunction(url,keywords,location,YearsExp,DegreeNumber,SearchType):  
  start = time.clock()
  br,cj=Browser_Setup()
  br,cj,page=Job_Search(br,cj,url,keywords,location)
  br,cj,Jobs=Open_All_Links(br,cj,page)
  Experience,Degree=DegreeAndExperienceLists(Jobs)
  MinYears,MaxYears=SearchExp(Experience)
  Required_Degree=SearchDeg(Degree)
  if SearchType==1:
    Result_urls=Search1(Jobs,MinYears,Required_Degree,YearsExp,DegreeNumber)
  else:
    Result_urls=Search2(Jobs,MinYears,Required_Degree,YearsExp,DegreeNumber)
  elapsed = (time.clock() - start)
  return Result_urls,elapsed, len(Jobs)

# Jobs,elapsed=TestCombinedFunction('http://www.careerbuilder.com','statistics data analyst','Chicago, Il')
def TestCombinedFunction(url,keywords,location):
  br,cj=Browser_Setup()
  br,cj,page=Job_Search(br,cj,url,keywords,location)
  links,times=Open_All_Links(br,cj,page)
  return br,cj,links,times

if __name__=='__main__':
  start = time.clock()	
  mgr=multiprocessing.Manager()
  jobs=mgr.list()
  sleeper=mgr.list()
  br,cj,links,times = TestCombinedFunction('http://www.careerbuilder.com','statistics data analyst','Chicago, IL')
  sleeper.append((len(links)/25)*30.0/len(links))
  results = [multiprocessing.Process(target=get_a_job, args=(sleeper, links[i],jobs))
           for i in range((len(links)-1)) 
           ]
  for j in results:
    j.start()
  for j in results:
    j.join()
  elapsed = (time.clock() - start)  
  print "there are:", len(jobs), "jobs"
  print "This search took:", elapsed, "hundred thousands of a second"
  print "the set of jobs is:", (len(links)-1), "jobs long"
  print jobs[0][0]

'''
if __name__=='__main__':
  Results_urls,elapsed, Jobs=FullCombinedFunction('http://www.careerbuilder.com','statistics data analyst','Chicago, IL',2,1,2)
  print 'There are', len(Results_urls), 'urls' 
  print 'The search took:', elapsed, 'seconds'
  print Jobs, 'jobs were searched' 
'''
'''
if __name__=='__main__':
  q=Queue()
  Jobs,elapsed = test_jobs_in_sets_of_25('http://www.careerbuilder.com','statistics data analyst','Chicago, IL')
  print "This search took:", elapsed, "hundred thousands of a second"
  print "the last set of jobs was:", len(Jobs), "jobs long"
  print "the queue is:", q.qsize(), "jobs long"
'''
