# 11-06-2026 01:52

Session 1:
Start Entry:
This is my first entry for Project 2. The project is a bank simulation in a single program. 3 teller threads and 50 customer threads are involved that coordinate using semaphores. The bank opens only when all three tellers are ready, customers enter through the door two at a time, tellers enter the safe two at a time, and only one teller at a time can talk to the manager (for withdrawals). The bank closes once all 50 customers have been served and have left.

The big difference from Project 1 is that threads share memory. In Project 1 every program had its own memory, so I needed pipes to send anything between them. Here every thread can see the same variables, so I don't need to pass messages, but I do need to stop threads from interfering with each other. My understanding of a semaphore is that it is a counter with acquire (wait, which blocks if the value is 0) and release (signal). I can see three uses here, where value 1 acts as a mutex, value N to limit how many threads can use something at once (door 2, safe 2, manager 1), and value 0 as a signal where one thread waits until another says something happened.

The biggest risks I see are race conditions and deadlock. A race condition is when two threads change a shared variable at once, since something like tellers_ready += 1 is not a single step. A deadlock is when a thread waits on a semaphore that nobody will ever release. In Project 1 my deadlock came from a missing flush, and here it will come from a missing release.

I am using Python again because the spec allows threading.Semaphore, I understand it more than C or Java, it is easy to implement threading in, and the example files from class use the same style.

My overall plan is 6 sessions: (1) skeleton, bank opening and door, (2) line and teller selection, (3) the transaction handshake, (4) manager and safe, (5) finishing the cycle and closing the bank, (6) testing and README.

My plan for this session is to write bank.py with the semaphores, a print helper, the teller and customer threads, the bank-open check, and the door.
The goal is output where all three tellers say they are ready before any customer enters, and all 50 customers get through the door.

# 11-06-2026 02:16
Coding Session starts:
The code I am doing for this session is bank.py. It declares the semaphores, starts 3 teller threads and 50 customer threads, opens the bank when all tellers are ready, and sends customers through the door.

- I picked the semaphore values from the spec, where door 2, safe 2, manager 1, mutex 1, and bank_open 0. The safe and manager are not used until session 4, but I declared them now so all the semaphores are in one place.

- I made one say() helper that builds every line in the THREAD_TYPE ID [PARTNER]: MSG format. This way the format is written once, and an empty partner gives the [] the sample output shows. I put a print_lock semaphore around the print because two threads printing at the same time can mix their text on one line.

- tellers_ready is a shared counter, so it is protected by mutex. tellers_ready += 1 is a read, add, write, so two tellers could both read 1 and both write 2. Then nobody would ever see 3, the bank would never open, and all 50 customers would wait forever.

- The check tellers_ready == NUM_TELLERS is inside the mutex, so exactly one teller (the last) sees 3 and releases bank_open exactly once.

- Each teller prints "ready to serve" before incrementing the counter. That guarantees all three ready lines appear before any customer can possibly enter.

- bank_open starts at 0 and works as a turnstile. A customer does acquire() then release() right away, so one release by the last teller lets all 50 customers through, because each one passes the "open" signal on to the next. I did this instead of releasing 50 times so the teller code doesn't need to know the customer count.

- The customer picks deposit or withdrawal with random.choice and prints it before sleeping 0 to 100 ms. The spec says every wait gets a line before and a line after, so "wants to perform..." is the before line and "going to bank." is the after line.

- The door is Semaphore(2) and is held while the customer prints "entering bank." and "getting in line." so no more than two customers are in the doorway at once. In session 2 the customer releases the door before waiting for a teller.

- main() starts the tellers first, then the customers, and joins every thread so the program doesn't end early. For now the teller and customer functions end after their last print, since serving is added in later sessions.

The concepts I am using are shared memory between threads (no pipes needed), a semaphore as a mutex, a semaphore as a resource limit, and a semaphore as a signal.

# 11-06-2026 03:03
 
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

# 11-06-2026 12:46

Session 2:
Start Entry:

Thoughts since last session in (): 
(Session 1 gave me the skeleton, the bank opening and the door. This session is the first real interaction between a customer and a teller, which is where the project actually starts. The spec says that if a teller is free the customer goes straight to it, and otherwise waits in line until called. My plan is to avoid writing a separate line data structure at all. A semaphore ready_tellers that starts at 0 and counts free tellers does both jobs. If the value is above 0 the customer's acquire() returns immediately, and if it is 0 the customer blocks, which is waiting in line.)

The semaphore only says how many tellers are free, not which one. So I need a list free_tellers that holds the ids of free tellers, protected by mutex. The order matters here though, because the teller appends its id first and releases the semaphore second, so a customer that gets past the semaphore always finds an id in the list. Then the customer needs a way to tell that specific teller it has arrived, so each teller gets its own semaphore customer_arrived[tid] starting at 0, and a slot current_customer[tid] where the customer writes its id.

The risk I see is the same one as last session, a missing release. If a teller forgets to release ready_tellers, every customer behind it waits forever. A second risk is two customers popping from an empty list, which the semaphore ordering should prevent.

The spec says tellers keep working until no customers are left. I don't want to do the full ending logic yet (that is session 5), so for this session the teller will just register itself as free again right after saying it is serving. This is a temporary shortcut so I can test that all 50 customers get matched.

My plan for this session is to add the line and teller selection, customer introductions, and the teller loop to bank.py.

The goal is 50 "selects teller" lines and 50 "serving a customer" lines, with no customer matched to two tellers and no hang.

# 11-06-2026 13:14
Coding session starts:
The code I am doing for this session is the line, the teller selection and the introduction in bank.py. A customer now goes through the door, waits for a free teller, picks one, and introduces itself. The teller wakes up and says it is serving that customer.

- ready_tellers is a semaphore starting at 0 that counts free tellers. I used it as the line because acquire() blocks when the value is 0, which is exactly "wait until a teller is free", and returns immediately when a teller is already free, which is "go straight to a ready teller" from the spec. It means I don't need a separate queue.

- free_tellers is a list of the ids of free tellers. The semaphore only counts, so the list is how a customer learns which teller to go to. It is a shared variable, so every append and pop happens inside mutex.

- The teller appends to the list first and releases the semaphore second. If it were the other way around, a customer could get past the semaphore and pop from an empty list. This order guarantees there is always an entry for every successful acquire. 

- pop(0) takes the teller that has been free the longest. The spec says the semaphores don't need to be fair, so the order doesn't matter as much, but it spreads customers over the tellers.

- customer_arrived is a list of three semaphores, one per teller, starting at 0. A teller waits on its own semaphore, and the customer releases the one for the teller it picked. A single shared semaphore would not work, because the wrong teller could wake up.

- current_customer[tid] is where the customer writes its id before releasing customer_arrived[tid]. I don't protect it with the mutex because only one customer at a time owns a given teller, and the semaphore release/acquire makes sure the teller reads the id after it was written.

- The customer prints "getting in line." before ready_tellers.acquire() and "selecting a teller." after it, like the sample, so the gap between the two lines shows how long the customer waited.

- The teller is now a loop, and the bank-opening count only happens the first time (first_time flag). Otherwise a teller would count itself again every time it becomes free and tellers_ready would go above 3.

- I am adding a TEMPORARY part: after "serving a customer" the teller counts the customer and loops straight back to free. Without this, each teller would only handle one customer and the other 47 would wait forever. A customers_served counter under mutex tells main when all 50 were matched, through the all_served semaphore. The tellers are daemon threads so the program can end while they still wait. Both will be removed in session 5, when the teller learns to stop properly.

The concepts I was aware of here are a semaphore as a counter of available resources (ready_tellers), a semaphore as a signal between two specific threads (customer_arrived), and ordering of operations as a correctness tool (append before release).

# 11-06-2026 14:34

End entry:
I tested the program on 4 lines:
1. python3 -u bank.py > output.txt
2. grep -c "selects teller" output.txt          
3. grep -c "serving a customer" output.txt     
4. grep "serving a customer" output.txt | sort | uniq -d 

At first, line 1 hung up indefinitely and lines 2 and 3 gave an output of 3 and 1 respectively instead of 50. Line 4 printed no duplicates.

Turned out the issue was that the serving logic was inside if first_time, so each teller served only one customer and the rest waited forever, which explained the main file hanging. It caused a deadlock: the remaining customers waited on ready_tellers, but no teller would release it again. The root cause was incorrect indentation.

The fix was simple, I unindented the serving logic so it runs every loop, letting tellers serve all 50 customers.

The line and teller selection work. I ran python3 bank.py > output.txt and grep gave 50 "selects teller" lines and 50 "serving a customer" lines. The uniq -d check printed nothing. I ran the program 30 times with timeout and none hung. With a temporary sleep in the teller I saw several customers stuck after "getting in line." while the tellers were busy, so customers do wait in line.

The only problem I ran into was bad indentation causing deadlock which was fixed by simply unindenting. 

What this shows about threads and semaphores is that a semaphore can stand in for a queue, because blocking on acquire() is waiting in line. But a counter alone doesn't carry information, so I needed the list for "which teller" and the per-teller semaphores for "wake up this teller, not another one".

Next session: I will build the handshake: the teller asks for the transaction, the customer answers with deposit or withdrawal, and the teller learns which one. I need to store each customer's choice somewhere the teller can read it, and add more per-teller semaphores so each step waits for the one before it.

# 11-12-2026 18:10
Session 3:
Start Entry:
Thoughts since last session in (): 
(Session 2 works now. My bug was an indentation error in the teller loop, so the serving logic ended up inside if first_time and the tellers stopped after one customer and my output was much less than needed. That showed me that in this project a hang is usually one missing or misplaced line, and the output only shows where it stopped, not why.)

This session is the conversation between a customer and a teller. In the spec the order is fixed, as in the customer introduces itself, the teller asks for the transaction, the customer answers, and the teller handles it. Each step has to wait for the one before it. A semaphore starting at 0 does that, because the waiting thread blocks on acquire() until the other thread releases. I already have one for the introduction (customer_arrived). I need two more per teller: teller_asked, so the customer waits to be asked before answering, and customer_answered, so the teller waits for the answer before handling it. They have to be per teller, like customer_arrived, because there are three conversations at the same time and a shared semaphore could wake the wrong thread.

The answer carries data (deposit or withdrawal), so I also need a shared variable current_kind[tid]. The ordering is what makes it safe: the customer writes current_kind[tid] first and releases customer_answered[tid] second, and the teller only reads it after acquiring that semaphore. So I do not need the mutex for it, since only the two threads of one conversation ever touch that slot, and the semaphore forces write-before-read.

The risk is the same as before, a missing release. If either side forgets its release, the other waits forever. Another risk is releasing in the wrong order, for example the teller reading current_kind before it was written.

My plan for this session is to add teller_asked, customer_answered and current_kind, then the handshake lines to the teller and the customer in bank.py. The goal is 50 lines each of "asks for transaction" and "handling ... transaction", and every customer's handled kind matching what it said at the start.

# 11-12-2026 18:36
Coding Session starts:
The code I am doing for this session is adding a semaphore handshake between each teller and customer so the teller asks for the transaction type, waits for the customer’s answer, and then handles the chosen deposit or withdrawal.

- I will add two semaphore lists, teller_asked and customer_answered, one semaphore per teller, all starting at 0. Starting at 0 will make the first acquire() block until the other side releases, so each step will wait for the one before it. This will use the same signal pattern as customer_arrived from session 2.

- They will be per teller because there will be three conversations at once. With one shared teller_asked, a customer talking to teller 2 could be woken by a release meant for teller 0's customer, and it would answer the wrong teller.

- current_kind[tid] will be a shared slot where the customer will put "deposit" or "withdrawal". Like current_customer[tid], I will not protect it with the mutex. Only the two threads of one conversation will touch that slot, and the semaphores will force the order: the customer will write it and then release customer_answered, and the teller will only read it after acquire() returns.

- The order of the customer's last two lines will matter. current_kind[tid] = kind will have to come before customer_answered[tid].release(). If I release first, the teller might wake up and read the slot before it is written.

- The teller will release teller_asked[tid] and then immediately block on customer_answered[tid].acquire(). The customer will do the opposite: it will block on teller_asked[tid].acquire() and then release customer_answered[tid]. Each side's release will be matched by the other side's acquire, so neither will be able to skip a step.

- The customer will reuse the kind variable it will pick at the start of customer(), so the answer will be the same deposit or withdrawal it will announce in "wants to perform a ... transaction". I will use that to test the code: every "handling X" line should match its customer's first line.

- I will move the temporary counting to after the "handling" line. This will prevent main() from stopping before the last handshake lines are printed.

- The wording will copy the sample: "asks for transaction" from the teller, "asks for deposit transaction" from the customer, and "handling deposit transaction" from the teller.

The concepts I will use will be semaphores as signals between two specific threads, and using the order of release and acquire to make sure data is written before it is read, so this shared slot will need no lock.

# 11-12-2026 20:10
End entry:
The handshake works. I ran python3 -u bank.py > output.txt and got 50 "handling" lines and 0 lines with None (expected 50 and 0). I checked customer 2 and the first line said deposit and the handling line said deposit. The program was also tested 30 times with a 5-second timeout per run, and none hung.

The issue I ran into was with the test command. grep -c "asks for transaction" output.txt gave 50 instead of the expected 100 because it only matched the teller lines. The customer lines have "deposit" or "withdrawal" between "for" and "transaction", so they did not match. The teller-request count of 50, handling count of 50, and None count of 0 were correct. To count both teller and customer requests, the corrected command is grep -Ec "asks for (deposit |withdrawal )?transaction" output.txt, which should give 100.

What this shows about threads and semaphores is that a conversation between two threads is a chain of signals, and each signal is a semaphore at 0 that one side releases and the other acquires. The semaphores also give the order for passing data, so the shared slot is safe without a mutex.

Next session: I will add the manager and the safe. A withdrawal teller must get the manager's permission (one at a time, 5 to 30 ms) before the safe (two at a time, 10 to 50 ms). I need to decide where to acquire and release manager and safe, and I need to remember that every wait gets a print line before and after it.

# 11-14-2026 20:47
Session 4:
Start Entry:

Thoughts since last session in (): 
(The handshake works, so the teller now knows whether the customer wants a deposit or a withdrawal. This session adds the manager and safe as shared resources protected by semaphores, building on the door limit and mutex from session 1. The manager and the safe were declared in session 1 with values 1 and 2 but never used.)

Before this session, my semaphores were signals (start at 0) and a mutex (value 1). Now I need the third kind, a counting semaphore that limits how many threads can be inside at once. The safe is Semaphore(2): the first two acquire() calls go through, and a third blocks until someone calls release(). The manager is Semaphore(1), which works like a lock. The spec says every wait needs a line before and a line after, and each shared resource needs three lines: going to it, using it, and done with it. The sample output shows what that looks like: "going to the manager", "getting manager's permission", "got manager's permission", and "going to safe", "enter safe", "leaving safe".

The sleeps are the part I have to be careful with. The sleep that represents the work has to happen while the teller holds the semaphore. If I release before sleeping, the limit would be meaningless because the "work" would take place outside the resource. I also do not want to sleep while holding print_lock, because that would freeze every thread that wants to print.

Only withdrawals go to the manager, but every transaction goes to the safe. The manager comes first, because the spec says the teller gets permission and then goes to the safe. One risk is a deadlock from holding one resource while waiting for another. I plan to release the manager before going to the safe, so a teller never holds the manager while waiting for the safe.

My plan for this session is to add the manager section (withdrawals only) and the safe section to the teller in bank.py, each with the three lines and the right sleep. The goal is that no more than two tellers are ever in the safe at once, no more than one is ever with the manager, and every withdrawal (and only withdrawals) goes to the manager.

# 11-14-2026 21:14
Coding Session starts:
The code I am doing for this session is the manager and the safe in bank.py. After the teller learns the transaction type, a withdrawal goes to the manager for permission, and then every transaction goes into the safe.

- Both resources follow the same pattern: print "going to", acquire(), print the "using" line, sleep, print the "done" line, release(). The spec asks for three lines per shared resource, and this pattern gives exactly those, with the going-to line before the wait, the using line after it, and the done line at the end.

- The sleep is between acquire() and release(). Sleeping is how the program represents the work, and it only means anything if the teller holds the resource during that time. If I released first, a third teller could enter the safe while the second was still "working", and the limit of 2 would exist only on paper.

- manager is Semaphore(1), so it works like a lock: only one teller can be with the manager at a time. The sleep is random.randint(5, 30) / 1000, because time.sleep takes seconds and the spec is in milliseconds.

- safe is Semaphore(2), a counting semaphore. The first two tellers acquire it immediately and a third one blocks on acquire() until one of them releases. The sleep is random.randint(10, 50) / 1000.

- Only withdrawals go to the manager (if kind == "withdrawal"), but every transaction goes to the safe. The teller does the manager first and the safe second, as the spec orders them.

- The teller releases the manager before going to the safe. Holding the manager while waiting for the safe would block the other tellers' withdrawals for no reason. It also avoids a deadlock pattern where a thread holds one resource while waiting for another.

- say() holds print_lock only while printing, and the sleeps happen outside it. If a teller slept while holding print_lock, every other thread would freeze until it woke up.

- The message wording copies the sample: "going to the manager", "getting manager's permission", "got manager's permission", "going to safe", "enter safe", "leaving safe".

- The temporary counting moved to after the safe. The teller still loops straight back to free after leaving the safe. Informing the customer and waiting for them to leave is session 5.

The concepts I was aware of were a semaphore as a lock (manager), a semaphore as a counter of how many may be inside (safe), holding a resource while doing work, and avoiding holding one resource while waiting for another.

# 11-14-2026 22:22
End entry:
The manager and safe work. I ran python3 bank.py > output.txt and got 22 "going to the manager" lines and 22 "handling withdrawal" lines, which match. There were 50 each of "going to safe", "enter safe" and "leaving safe". Going down the safe lines with a running count the highest was 2, and for the manager the highest was 1. In the negative test with Semaphore(3) I saw three tellers in the safe at the same time, so the semaphore is what limits the safe. I ran the program 30 times with timeout and none hung.

I did not really run into any problems this time.

What this shows about semaphores: the value of the semaphore is the limit. Value 1 makes a lock, value 2 allows two threads inside, and the thread that cannot get in simply blocks on acquire() until someone releases. The sleep inside the held section is what makes the limit visible in the output.

Next session: I will finish the cycle. The teller will tell the customer the transaction is finished and wait for the customer to leave, then become free again for the next customer. After all 50 customers have left, the tellers go home and the bank closes. That will replace the temporary counting and the daemon threads from session 2.

# 11-15-2026 18:06
Session 5:
Start Entry:
Thoughts since last session in (): 
(The manager and the safe work, and I verified the limits by counting how many tellers were inside at once, and by changing the safe to 3 to see the limit break. What is left from the spec is steps 8 and 9 of the teller (inform the customer and wait for the customer to leave), the customer leaving, and closing the bank after all 50 customers have left. I also have to remove the two temporary hacks from session 2, the all_served semaphore and the daemon threads. This session finishes the code, and then I spend some time testing, writing the README and cleaning up the repo.)

The finish handshake works like the earlier ones. The teller releases transaction_done[tid] and the customer waits on it, so a customer cannot leave before the teller says it is done. Then the customer releases customer_left[tid] and the teller waits on it, so the teller cannot call the next customer before this one has left. Both are semaphores at 0 and per teller, for the same reason as before.

The harder part is closing. Right now a teller loops forever. The tellers that are idle at the end are blocked on customer_arrived[tid], and nobody will ever release it, because there are no more customers. My plan is a shared flag closing plus a wake-up so when the teller that served the last customer sees that customers_served reached 50, it sets closing and releases customer_arrived for every teller. A teller that wakes up checks closing before doing anything else, and if it is set, it leaves its loop and prints that it is leaving for the day. The count and the flag are shared variables, so they are updated inside mutex.

The risks are a teller that never wakes up (a hang at the very end, after all the output looks done) and a teller that wakes up and tries to serve customer None. I will watch for both.

My plan for this session is to finish the remaining coding part and write a check that compares my output with the sample, runs many times to look for hangs, verifies that the limits hold, and then write the README and make sure git status is clean. The goal is that the program ends by itself with "The bank closes for the day." as the last line, every customer leaves, and no run hangs.

# 11-15-2026 18:33
Coding session starts:
The code I will work on for this part of the session will be the end of the cycle in bank.py: the teller will inform the customer, the customer will leave, the teller will wait for them to leave, and the bank will close after the 50th customer.

- I will add two more per-teller semaphores, transaction_done and customer_left, both starting at 0. transaction_done will make the customer wait until the teller says the transaction is finished, and customer_left will make the teller wait until the customer has left. They will be per teller because three conversations will run at the same time, as with the earlier signals.

- The teller will print "finishes X transaction." before it releases transaction_done, and the customer will print "leaves teller" before it releases customer_left. The print will come first in both places so the log will show the cause before the effect. That way a customer's "leaves teller" line will not appear before the teller's "finishes" line.

- The teller will wait for customer_left before it loops back to "ready to serve". Without it, the teller could put itself on the free list while its old customer was still talking, and the next customer could be introduced to a teller that is not ready.

- Closing the bank will be the hard part. An idle teller will be blocked on customer_arrived[tid], and after the last customer nobody will release that again. So customers_served will be counted inside mutex after each customer leaves, and the teller that sees it reach 50 will set the shared flag closing and release customer_arrived for all three tellers, itself included.

- A teller will check closing right after customer_arrived.acquire(). If it is set, there will be no customer, so it will break out of the loop and print "leaving for the day". The flag will be written inside mutex before the releases, and the other tellers will read it only after their acquire() returns, so they will always see it set. The teller that wakes the others will also release its own semaphore, so it will take the same path out instead of needing a special case.

- I will remove the all_served semaphore and the daemon=True threads from session 2. Daemon threads let the program exit while tellers are still blocked, which only hides the problem. main() will join all 50 customers and then all 3 tellers, so the program will only end when every thread has finished by itself. That will make a leftover blocked teller show up as a hang instead of being hidden.

- main() will print "The bank closes for the day." after the joins, because it will be the one place that knows every thread is done. It has no thread prefix in the sample, so it will be a plain print.

- The customer will leave with "goes to door" and "leaves the bank". The sample shows these lines without any door semaphore, and the spec only limits entering to two at a time, so I will not add one for leaving.

The concepts I will use will be semaphores as signals in both directions of one conversation, a shared flag plus a wake-up release to end threads that are blocked, and why a thread will have to be woken to be told that there is nothing left to do.

# 11-15-2026 20:20
End entry:
The whole project works in the checks I ran. I added the finish-and-leave handshake, replaced the temporary all_served semaphore and daemon threads with the closing flag and wake-up signals, and made main() join every customer and teller before printing the closing message. I also cleaned up bank.py and updated the README. I combined the testing and README work originally planned for session 6 into this session.

I ran the program 100 times with a 10-second timeout for each run, and none hung. Every run had 50 "leaves the bank" lines, 50 "finishes" lines and 3 "leaving for the day" lines, as expected. The last line was always "The bank closes for the day.". I checked the safe and the manager by keeping a running count, and the highest was 2 and 1. I also checked every customer's "leaves teller" line came after the teller's "finishes" line. I compared a fresh run with sample-ouput.txt after replacing numbers with N and comparing message types and counts rather than thread order. My run had 23 deposits and 27 withdrawals, while the sample had 19 deposits and 31 withdrawals, so the transaction-specific counts and manager visits differed. My "introduces itself" lines had a colon after the bracket, while the sample omitted it. The sample also had a malformed "wait for customer to leave" line with extra text and only 49 "enter safe" lines; my run had 50 correctly formatted lines for each. The sample had 1152 nonblank lines and my run had 1141. The other message types matched, and the order differed because the threads ran concurrently.

No simulation problems showed up during these checks. The tellers woke up and exited at closing, and no customer left its teller before the transaction finished.

What this shows about threads and semaphores is that the whole project is three patterns combined. A semaphore as a lock (mutex and manager), a semaphore as a counter of available resources (door, safe, and ready_tellers), and a semaphore starting at 0 as a signal, which is how every handshake step is done. The threads share memory, so there are no pipes to pass data through, but I have to control the order in which they read and write it, and the semaphores do that.

Compared to project 1, processes had separate memory and needed pipes, and the hangs came from a missing flush. Threads share memory and need semaphores, and the hangs come from a missing release or a missing wake-up. In both, the program stops with no error and I had to find where by looking at the last line printed.

This is the last session. What I would do differently is write a small checker earlier, because reading 1100 lines by eye is slow.