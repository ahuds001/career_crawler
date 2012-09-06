import time
from multiprocessing import Process, Pipe


def suma(a,b):
  c=a+b
  return "%s and %s = %s" % (a,b,c)

def mult(a,b):
  c=[]
  c.append(a+b)
  return c

def combined(a,b):
  suma(a,b)
  mult(a,b)

def multiple_combined():
  for i in range(1,100):
    combined(i,2)

def grab_and_smash(fun):
    fun[0]=fun[0]+1
    print fun

def correct_multiple():
  for i in range(1,100):
    c=i+2
    if i==99:
	    print i
    q.put(c)
    c=i*2
    q.put(c)
  return q

def f(conn):
    conn.send(mult(3,4))
    conn.close()

if __name__ == '__main__':
  start=time.clock()
  parent_conn, child_conn = Pipe()
  p = Process(target=f, args=(child_conn,))
  p.start()
  fun= parent_conn.recv()
  p2 = Process(target=grab_and_smash,args=(fun))
  p2.start()
  p.join()
  print p2
  p2.join()

