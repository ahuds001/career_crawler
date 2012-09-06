# Set of instructions to log into fake account and log out at the end. Need to know what the handles do

import mechanize
import cookielib
from bs4 import BeautifulSoup
import time
import nltk
import re
import itertools
from multiprocessing import Process,Queue

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
  # time.sleep(5)
  page=br.open(link)
  Job_sections=[str(br.title())]
  Job_sections.append(nltk.clean_html(page.get_data()))
  Job_sections.append(link)
  return br,cj,Job_sections

def get_jobs_to_queue(br,cj,page):
  links=get_all_urls(page)
  for link in links[:-1]:
    br,cj,Job_sections=Open_Link(br,cj,link)
    q.put(Job_sections)  
  return br,cj,links

def move_to_next_jobs_page(br,cj,links):
  time.sleep(30)
  result=br.open(links[-1])
  page=result.get_data()
  return br,cj,page

def place_jobs_in_queue(url,keywords,location):
  # start = time.clock()
  br,cj=Browser_Setup()
  br,cj,page=Job_Search(br,cj,url,keywords,location)
  while True:
    br,cj,links,=get_jobs_to_queue(br,cj,page)
    if links[-1]==None:
	    break
    br,cj,page=move_to_next_jobs_page(br,cj,links)
  # elapsed = (time.clock() - start)
  return # elapsed

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
                        for m in re.finditer('[,.!?\n\t\r]',Job_sections[1])
                      ]
  Experience_Tuples = [
                        (Sentence_Location[bisect_right(Sentence_Location,m)-1],Sentence_Location[bisect_right(Sentence_Location,m)])
                        for m in Experience_Location
                      ]
  words=['doctorate','phd','master', 'masters','mba','ma', 'advanced degree','bachelor','bachelors','ba','bs','4 year','four year','undergraduate']
  exactMatch = re.compile(r'\b%s\b' % '\\b|\\b'.join(words), flags=re.IGNORECASE)
  degrees = [
              exactMatch.findall(Job_sections[1])
            ]
  expyears = [
               re.findall(r'\d+', Job_sections[1][m[0]:m[1]])
               for m in Experience_Tuples
             ]
  expyears=list(itertools.chain(*expyears))
  degrees=list(itertools.chain(*degrees))
  return expyears,degrees

def search_job_for_years_exp(Experience):
  Options = [
              int(i)
              for i in xrange(1,21,1)
            ]
  IntExp = [
             int(i)
             for i in Experience
           ]
  if IntExp:
    try:
      MinYears=(min(x for x in IntExp if x in Options))
      MaxYears=(max(x for x in IntExp if x in Options))
    except:
      MinYears=100       
      MaxYears=100
  else:
    MinYears=100			
    MaxYears=100
  return MinYears,MaxYears

def search_job_for_degree(Degree):
  words=['doctorate phd','master masters mba ma advanced degree','bachelor bachelors ba bs 4 year four year undergraduate']
  if not Degree:
      Required_Degree=0
  else:
    exactMatch = re.compile(r'\b%s\b' % '\\b|\\b'.join(Degree), flags=re.IGNORECASE)
    if len(exactMatch.findall(words[0]))>0:			
      Required_Degree=3
    elif len(exactMatch.findall(words[1]))>0:
      Required_Degree=2
    elif len(exactMatch.findall(words[2]))>0:
      Required_Degree=1
  return Required_Degree

def search_a_job_for_years_and_degrees():
  job_urls_with_results=[]
  while q.empty()==False:
    job=q.get()
    Experience,Degree=DegreeAndExperience(job)
    MinYears,MaxYears=search_job_for_years_exp(Experience)
    Required_Degree=search_job_for_degree(Degree)
    job_urls_with_results.append([job[0],job[2],MinYears,Required_Degree])
  return job_urls_with_results

def jobs_that_meet_criteria(job_urls_with_results,SearchType,YearsExp,DegreeNumber):
  Result_urls=[]
  if SearchType==1:
    for job in job_urls_with_results:
      if (YearsExp>job[2] or job[2]==100) and job[3]<=DegreeNumber:
        print job[2], job[3]
	Result_urls.append([job[0],job[1]] )
  if SearchType==2:
    for job in job_urls_with_results:
      if YearsExp>=job[2]  and job[3]<=DegreeNumber and job[3]!=0:
        print job[2], job[3]
        Result_urls.append([job[0],job[1]])
  return Result_urls

def job_urls_with_results_that_meet_criteria(SearchType,YearsExp,DegreeNumber):
  job_urls_with_results=search_a_job_for_years_and_degrees()
  if SearchType==1:
    for job in job_urls_with_results:
      if (YearsExp>job[2] or job[2]==100) and job[3]<=DegreeNumber:
        print job[2], job[3]
	Result_urls.append([job[0],job[1]] )
  if SearchType==2:
    for job in job_urls_with_results:
      if YearsExp>=job[2]  and job[3]<=DegreeNumber and job[3]!=0:
        print job[2], job[3]
        Result_urls.append([job[0],job[1]])

'''if __name__=='__main__':
  q=Queue()
  place_jobs_in_queue('http://www.careerbuilder.com','statistics data analyst','Chicago, IL')
  job_urls_with_results=search_a_job_for_years_and_degrees()
  SearchType=1
  YearsExp=2
  DegreeNumber=1
  result_jobs=jobs_that_meet_criteria(job_urls_with_results,SearchType,YearsExp,DegreeNumber)
  print len(result_jobs), "out of", len(job_urls_with_results), "jobs"
  print "these are the jobs available:",result_jobs'''
  
  # Need two queues, one giving input and one grabbing output. Also need to create workers. 
  # See Multiprocessing example.
if __name__=='__main__':
  q=Queue()
  start=time.clock()
  SearchType=1
  YearsExp=2
  DegreeNumber=1
  Result_jobs=[]
  p1=Process(target=place_jobs_in_queue,args=('http://www.careerbuilder.com','statistics data analyst','Chicago, IL'))
  # p2=Process(target=job_urls_with_results_that_meet_criteria, args=(SearchType,YearsExp,DegreeNumber))
  p1.start()
  # if (time.clock()-start)>30:
    # p2.start()
  p1.join()
  
