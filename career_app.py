#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import crawler

DEBUG= True
app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def main():
  '''
  show the form
  '''
  print "hello"
  return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
  '''
  handles the form values and gets the results to render
  '''
  keyw = loc = ""
  if request.form['keywords'] != "" and request.form['location'] != "":
    # get keywords and location
    keyw = request.form['keywords']
    loc  = request.form['location']
    list_of_jobs, time_elapsed = crawler.TestCombinedFunction('http://www.careerbuilder.com', keyw, loc)
  return render_template('results.html', keyw=keyw, loc=loc, results=list_of_jobs[:10], time_elapsed=time_elapsed)

if __name__=='__main__':
  app.run(host='0.0.0.0', port=5050)
