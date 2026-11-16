import threading
import random
import time

NUM_TELLERS = 3
NUM_CUSTOMERS = 50

# ---------- Semaphores ----------
door = threading.Semaphore(2)         # at most 2 customers entering at once
safe = threading.Semaphore(2)         # at most 2 tellers in the safe
manager = threading.Semaphore(1)      # one teller at a time with the manager
mutex = threading.Semaphore(1)        # protects shared variables
bank_open = threading.Semaphore(0)    # starts closed, opened by the last teller to be ready
print_lock = threading.Semaphore(1)   # keeps output lines from mixing together
ready_tellers = threading.Semaphore(0)   # counts free tellers; customers block here = the line

# one set per teller, one signal per step of the conversation
customer_arrived = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]   # customer -> teller: "I am here"
teller_asked = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]       # teller -> customer: "what do you want?"
customer_answered = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]  # customer -> teller: "here is my answer"
transaction_done = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]   # teller -> customer: "all done"
customer_left = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]      # customer -> teller: "I have left"

# ---------- Shared variables ----------
tellers_ready = 0
free_tellers = []                          # ids of tellers waiting for a customer
current_customer = [None] * NUM_TELLERS    # which customer is at each teller
current_kind = [None] * NUM_TELLERS        # "deposit" or "withdrawal" for the customer at each teller
customers_served = 0                       # customers that have finished and left
closing = False                            # set once the last customer has left


def say(kind, ident, partner, msg):
    """Print one line in the format: THREAD_TYPE ID [PARTNER]: MSG"""
    print_lock.acquire()
    print(f"{kind} {ident} [{partner}]: {msg}")
    print_lock.release()


def teller(tid):
    global tellers_ready, customers_served, closing
    first_time = True

    while True:
        say("Teller", tid, "", "ready to serve")

        if first_time:
            mutex.acquire()
            tellers_ready += 1
            if tellers_ready == NUM_TELLERS:
                bank_open.release()          # the last teller opens the bank
            mutex.release()
            first_time = False

        # announce that I am free: list entry FIRST, then the semaphore
        mutex.acquire()
        free_tellers.append(tid)
        mutex.release()
        ready_tellers.release()

        say("Teller", tid, "", "waiting for a customer")
        customer_arrived[tid].acquire()          # a customer arrives, or the bank is closing

        if closing:                              # woken up with no customer: time to go home
            break

        cid = current_customer[tid]
        who = f"Customer {cid}"
        say("Teller", tid, who, "serving a customer")

        # the handshake: ask, then wait for the answer
        say("Teller", tid, who, "asks for transaction")
        teller_asked[tid].release()
        customer_answered[tid].acquire()

        kind = current_kind[tid]
        say("Teller", tid, who, f"handling {kind} transaction")

        # withdrawals need the manager's permission, one teller at a time
        if kind == "withdrawal":
            say("Teller", tid, who, "going to the manager")
            manager.acquire()
            say("Teller", tid, who, "getting manager's permission")
            time.sleep(random.randint(5, 30) / 1000)       # 5 - 30 ms
            say("Teller", tid, who, "got manager's permission")
            manager.release()

        # every transaction goes through the safe, two tellers at a time
        say("Teller", tid, who, "going to safe")
        safe.acquire()
        say("Teller", tid, who, "enter safe")
        time.sleep(random.randint(10, 50) / 1000)          # 10 - 50 ms
        say("Teller", tid, who, "leaving safe")
        safe.release()

        # inform the customer, then wait for them to leave
        say("Teller", tid, who, f"finishes {kind} transaction.")
        transaction_done[tid].release()
        say("Teller", tid, who, "wait for customer to leave.")
        customer_left[tid].acquire()

        # count the customer; the teller who serves the last one closes the bank
        mutex.acquire()
        customers_served += 1
        if customers_served == NUM_CUSTOMERS:
            closing = True
            for t in range(NUM_TELLERS):         # wake every teller, including myself
                customer_arrived[t].release()
        mutex.release()

    say("Teller", tid, "", "leaving for the day")


def customer(cid):
    kind = random.choice(["deposit", "withdrawal"])
    say("Customer", cid, "", f"wants to perform a {kind} transaction")

    time.sleep(random.randint(0, 100) / 1000)     # 0 - 100 ms
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
    current_customer[tid] = cid                  # tell the teller who I am
    say("Customer", cid, f"Teller {tid}", "introduces itself")
    customer_arrived[tid].release()              # wake the teller up

    # the handshake: wait to be asked, then answer
    teller_asked[tid].acquire()
    say("Customer", cid, f"Teller {tid}", f"asks for {kind} transaction")
    current_kind[tid] = kind
    customer_answered[tid].release()

    # wait for the teller to finish, then leave
    transaction_done[tid].acquire()
    say("Customer", cid, f"Teller {tid}", "leaves teller")
    customer_left[tid].release()                 # tell the teller I have left
    say("Customer", cid, "", "goes to door")
    say("Customer", cid, "", "leaves the bank")


def main():
    tellers = [threading.Thread(target=teller, args=(i,)) for i in range(NUM_TELLERS)]
    customers = [threading.Thread(target=customer, args=(i,)) for i in range(NUM_CUSTOMERS)]

    for t in tellers:
        t.start()
    for c in customers:
        c.start()

    for c in customers:
        c.join()
    for t in tellers:
        t.join()

    print("The bank closes for the day.")


if __name__ == "__main__":
    main()
