import time
from multiprocessing import Process, Queue


def suma(a,b):
  c=a+b
  q.put(c)

def mult(a,b):
  c=a+b
  q.put(c)

def combined(a,b):
  suma(a,b)
  mult(a,b)

def multiple_combined():
  for i in range(1,100):
    combined(i,2)

def grab_and_smash(q):
  while q.empty()==FALSE:
    fun=q.get()
    fun=('smash x%s' % fun)
    print fun

def correct_multiple():
  q=Queue()
  for i in range(1,100):
    c=i+2
    if i==99:
	    print i
    q.put(c)
    c=i*2
    q.put(c)
  return q


if __name__=='__main__':
  start=time.clock()
  p1=Process(target=correct_multiple,args=())
  p2=Process(target=grab_and_smash, args=(q))
  p1.start()
  if (time.clock()-start)>30:
   p2.start()
