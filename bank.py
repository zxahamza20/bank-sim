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

def say(kind, ident, partner, msg):
  print_lock.acquire()
  print(f"{kind} {ident} [{partner}]: {msg}")
  print_lock.release()

def teller(tid):
  global tellers_ready

  say("Teller", tid, "", "ready to serve")

  mutex.acquire()
  tellers_ready += 1
  if tellers_ready == NUM_TELLERS:
      bank_open.release()          
  mutex.release()

  say("Teller", tid, "", "waiting for a customer")
  # Placeholder: serving customers is added in later sessions

def customer(cid):
  kind = random.choice(["deposit", "withdrawal"])
  say("Customer", cid, "", f"wants to perform a {kind} transaction")

  time.sleep(random.randint(0, 100) / 1000)    
  say("Customer", cid, "", "going to bank.")

  bank_open.acquire()
  bank_open.release()

  door.acquire()
  say("Customer", cid, "", "entering bank.")
  say("Customer", cid, "", "getting in line.")
  door.release()
  # Placeholder: line and teller selection are added in session 2

def main():
    threads = []
    for i in range(NUM_TELLERS):
        threads.append(threading.Thread(target=teller, args=(i,)))
    for i in range(NUM_CUSTOMERS):
        threads.append(threading.Thread(target=customer, args=(i,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
