import threading
import random
import time

NUM_TELLERS = 3
NUM_CUSTOMERS = 50


# Semaphores 
# at most 2 customers 
door = threading.Semaphore(2)     
# at most 2 tellers in the safe (used in session 4)
safe = threading.Semaphore(2)     
# one teller at a time with the manager (session 4)
manager = threading.Semaphore(1)     
# protects shared variables
mutex = threading.Semaphore(1)       
# starts closed, opened by the last teller to be ready
bank_open = threading.Semaphore(0)   
# keeps output lines from mixing together
print_lock = threading.Semaphore(1)  
 # counts free tellers; customers block here = the line
ready_tellers = threading.Semaphore(0)  
# one per teller
customer_arrived = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]  

# Shared variables
tellers_ready = 0
# ids of tellers waiting for a customer
free_tellers = []                   
# which customer is at each teller       
current_customer = [None] * NUM_TELLERS    

# TEMPORARY (session 2 only, will replace later in session 5)
customers_served = 0
all_served = threading.Semaphore(0)

def say(kind, ident, partner, msg):
  print_lock.acquire()
  print(f"{kind} {ident} [{partner}]: {msg}")
  print_lock.release()

def teller(tid):
  global tellers_ready, customers_served
  first_time = True

  while True:
    say("Teller", tid, "", "ready to serve")

    if first_time:
      mutex.acquire()
      tellers_ready += 1
      if tellers_ready == NUM_TELLERS:
        bank_open.release()         
      mutex.release()
      first_time = False

    # announce that I am free: list entry FIRST, then the semaphore
    mutex.acquire()
    free_tellers.append(tid)
    mutex.release()
    ready_tellers.release()

    say("Teller", tid, "", "waiting for a customer")
    # sleep until a customer introduces itself
    customer_arrived[tid].acquire()          

    cid = current_customer[tid]
    say("Teller", tid, f"Customer {cid}", "serving a customer")

    # TEMPORARY: count the customer and let main know when all 50 were matched
    mutex.acquire()
    customers_served += 1
    last = (customers_served == NUM_CUSTOMERS)
    mutex.release()
    if last:
      all_served.release()

def customer(cid):
  kind = random.choice(["deposit", "withdrawal"])
  say("Customer", cid, "", f"wants to perform a {kind} transaction")

  time.sleep(random.randint(0, 100) / 1000)    
  say("Customer", cid, "", "going to bank.")

  # Turnstile: wait for the bank to open, then let the next customer through
  bank_open.acquire()
  bank_open.release()

  door.acquire()
  say("Customer", cid, "", "entering bank.")
  say("Customer", cid, "", "getting in line.")
  door.release()

  # The line: blocks here if no teller is free
  ready_tellers.acquire()
  say("Customer", cid, "", "selecting a teller.")

  mutex.acquire()
  tid = free_tellers.pop(0)
  mutex.release()

  say("Customer", cid, f"Teller {tid}", "selects teller")
  # tell the teller who I am
  current_customer[tid] = cid                  
  say("Customer", cid, f"Teller {tid}", "introduces itself")
   # wake the teller up
  customer_arrived[tid].release()             
  # Placeholder: transaction handshake is added in session 3

def main():
  # TEMPORARY: tellers are daemons so the program can end while they wait
  for i in range(NUM_TELLERS):
    threading.Thread(target=teller, args=(i,), daemon=True).start()

  customers = []
  for i in range(NUM_CUSTOMERS):
    t = threading.Thread(target=customer, args=(i,))
    customers.append(t)
    t.start()

  for t in customers:
    t.join()
  # wait until every customer reached a teller
  all_served.acquire()     


if __name__ == "__main__":
  main()
