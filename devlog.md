# 11-06-2026 01:52am

Session 1:
Start Entry:
This is my first entry for Project 2. The project is a bank simulation in a single program. 3 teller threads and 50 customer threads are involved that coordinate using semaphores. The bank opens only when all three tellers are ready, customers enter through the door two at a time, tellers enter the safe two at a time, and only one teller at a time can talk to the manager (for withdrawals). The bank closes once all 50 customers have been served and have left.

The big difference from Project 1 is that threads share memory. In Project 1 every program had its own memory, so I needed pipes to send anything between them. Here every thread can see the same variables, so I don't need to pass messages, but I do need to stop threads from interfering with each other. My understanding of a semaphore is that it is a counter with acquire (wait, which blocks if the value is 0) and release (signal). I can see three uses here, where value 1 as a mutex, value N to limit how many threads can use something at once (door 2, safe 2, manager 1), and value 0 as a signal where one thread waits until another says something happened.

The biggest risks I see are race conditions and deadlock. A race condition is when two threads change a shared variable at once, since something like tellers_ready += 1 is not a single step. A deadlock is when a thread waits on a semaphore that nobody will ever release. In Project 1 my deadlock came from a missing flush, and here it will come from a missing release.

I am using Python again because the spec allows threading.Semaphore, I understand it more than C or Java, it is easy to implement threading in, and the example files from class use the same style.

My overall plan is 6 sessions: (1) skeleton, bank opening and door, (2) line and teller selection, (3) the transaction handshake, (4) manager and safe, (5) finishing the cycle and closing the bank, (6) testing and README.

My plan for this session is to write bank.py with the semaphores, a print helper, the teller and customer threads, the bank-open check, and the door.
The goal is output where all three tellers say they are ready before any customer enters, and all 50 customers get through the door.
