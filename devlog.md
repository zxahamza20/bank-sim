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

# 11-06-2026 02:16am
Coding Session starts:
The code I am doing for this session is bank.py. It declares the semaphores, starts 3 teller threads and 50 customer threads, opens the bank when all tellers are ready, and sends customers through the door.

- I picked the semaphore values from the spec, where door 2, safe 2, manager 1, mutex 1, and bank_open 0. The safe and manager are not used until session 4, but I declared them now so all the semaphores are in one place.

- I made one say() helper that builds every line in the THREAD_TYPE ID [PARTNER]: MSG format. This way the format is written once, and an empty partner gives the [] the sample output shows. I put a print_lock semaphore around the print because two threads printing at the same time can mix their text on one line.

- tellers_ready is a shared counter, so it is protected by mutex. tellers_ready += 1 is a read, add, write, so two tellers could both read 1 and both write 2. Then nobody would ever see 3, the bank would never open, and all 50 customers would wait forever.

- The check tellers_ready == NUM_TELLERS is inside the mutex, so exactly one teller (the last) sees 3 and releases bank_open exactly once.

- Each teller prints "ready to serve" before incrementing the counter. That guarantees all three ready lines appear before any customer can possibly enter.

- bank_open starts at 0 and works as a turnstile. A customer does acquire() then release() right away, so one release by the last teller lets all 50 customers through, because each one passes the "open" signal on to the next. I did this instead of releasing 50 times so the teller code doesn't need to know the customer count.

- The customer picks deposit or withdrawal with random.choice and prints it before sleeping 0 to 100 ms. The spec says every wait gets a line before and a line after, so "wants to perform..." is the before line and "going to bank." is the after line.

- The door is Semaphore(2) and is held while the customer prints "entering bank." and "getting in line." so no more than two customers are in the doorway at once. In session 2 the line logic goes inside this section.

- main() starts the tellers first, then the customers, and joins every thread so the program doesn't end early. For now the teller and customer functions end after their last print, since serving is added in later sessions.

The concepts I am using are shared memory between threads (no pipes needed), a semaphore as a mutex, a semaphore as a resource limit, and a semaphore as a signal.

# 11-06-2026 03:03am
 
End entry:
I tested the file as of now by doing:  

python3 bank.py > output.txt              
grep -c "entering bank" output.txt
grep -n -E "ready to serve|entering bank" output.txt | head -5

This showed me:
50
1:Teller 0 []: ready to serve
3:Teller 1 []: ready to serve
5:Teller 2 []: ready to serve
58:Customer 0 []: entering bank.
61:Customer 1 []: entering bank.

This verified that the skeleton works. python3 bank.py > output.txt and grep -c "entering bank" gave 50. The first three matches of grep for "ready to serve" or "entering bank" showed no customer enters before all three tellers are ready, and then they did. I also tested the door with a temporary sleep and saw customers enter in bursts of at most two at a time.

What this shows about threads is that they share one memory, so the counter and the semaphores are visible to everyone, and the work is making sure only one thread changes the counter at a time. The turnstile showed me that a semaphore can be a signal as well as a lock.

Next session: I will add the line and teller selection, so customers find a free teller or wait in line, and they introduce themselves. I need to think about how a customer and a teller find each other without two customers picking the same teller.

# 11-06-2026 12:46pm

Session 2:
Start Entry:

Thoughts since last session in (): 
(Session 1 gave me the skeleton, the bank opening and the door. This session is the first real interaction between a customer and a teller, which is where the project actually starts. The spec says that if a teller is free the customer goes straight to it, and otherwise waits in line until called. My plan is to avoid writing a separate line data structure at all. A semaphore ready_tellers that starts at 0 and counts free tellers does both jobs. If the value is above 0 the customer's acquire() returns immediately, and if it is 0 the customer blocks, which is waiting in line.)

The semaphore only says how many tellers are free, not which one. So I need a list free_tellers that holds the ids of free tellers, protected by mutex. The order matters here thouh, cause the teller appends its id first and releases the semaphore second, so a customer that gets past the semaphore always finds an id in the list. Then the customer needs a way to tell that specific teller it has arrived, so each teller gets its own semaphore customer_arrived[tid] starting at 0, and a slot current_customer[tid] where the customer writes its id.

The risk I see is the same one as last session, a missing release. If a teller forgets to release ready_tellers, every customer behind it waits forever. A second risk is two customers popping from an empty list, which the semaphore ordering should prevent.

The spec says tellers keep working until no customers are left. I don't want to do the full ending logic yet (that is session 5), so for this session the teller will just register itself as free again right after saying it is serving. This is a temporary shortcut so I can test that all 50 customers get matched.

My plan for this session is to add the line and teller selection, customer introductions, and the teller loop to bank.py.

The goal is 50 "selects teller" lines and 50 "serving a customer" lines, with no customer matched to two tellers and no hang.

# 11-06-2026 13:14pm
Coding session starts:
The code I am doing for this session is the line, the teller selection and the introduction in bank.py. A customer now goes through the door, waits for a free teller, picks one, and introduces itself. The teller wakes up and says it is serving that customer.

- ready_tellers is a semaphore starting at 0 that counts free tellers. I used it as the line because acquire() blocks when the value is 0, which is exactly "wait until a teller is free", and returns immediately when a teller is already free, which is "go straight to a ready teller" from the spec. It means I don't need a separate queue.

- free_tellers is a list of the ids of free tellers. The semaphore only counts, so the list is how a customer learns which teller to go to. It is a shared variable, so every append and pop happens inside mutex.

- The teller appends to the list first and releases the semaphore second. If it were the other way around, a customer could get past the semaphore and pop from an empty list. This order guarantees there is always an entry for every successful acquire. 
