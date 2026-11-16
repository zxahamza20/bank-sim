# Project 2: Bank Simulation

A simulation of a bank with 3 tellers and 50 customers, written in Python.
Every teller and every customer is a thread (`threading.Thread`), they
communicate through shared variables, and all synchronization is done with
`threading.Semaphore`.

## How to run

    python3 bank.py

Python 3 only, no extra libraries. The program ends by itself and prints
"The bank closes for the day." as its last line. A run takes about one second.
To save the output: `python3 bank.py > output.txt`.

## What it does

- The bank opens when all 3 tellers are ready.
- Each customer picks deposit or withdrawal, waits 0-100 ms, and enters
  through a door that lets 2 customers in at a time.
- A customer goes to a free teller, or waits in line until one is free.
- The customer introduces itself, the teller asks for the transaction, and the
  customer answers.
- A withdrawal needs the manager's permission (one teller at a time, 5-30 ms).
- Every transaction goes through the safe (two tellers at a time, 10-50 ms).
- The teller tells the customer the transaction is done and waits for them to leave.
- After the 50th customer leaves its teller, that teller sets `closing` and
  wakes all tellers so they can go home. `main()` waits for every customer and
  teller thread to finish before printing the bank's closing message.

Thread actions print lines as `THREAD_TYPE ID [PARTNER]: MSG`. The partner is
`Customer ID` or `Teller ID` during a conversation, and is empty (`[]`) for
actions without a partner. The final line is a plain
`The bank closes for the day.` with no thread prefix.

## Semaphores

| Semaphore                 | Value | Purpose                                                                       |
| ------------------------- | ----- | ----------------------------------------------------------------------------- |
| `door`                  | 2     | at most 2 customers entering at once                                          |
| `safe`                  | 2     | at most 2 tellers in the safe                                                 |
| `manager`               | 1     | one teller at a time with the manager                                         |
| `mutex`                 | 1     | protects the free-teller list, counters, and updates to `closing`              |
| `print_lock`            | 1     | keeps output lines from mixing                                                |
| `bank_open`             | 0     | signal that all tellers are ready (a turnstile for customers)                 |
| `ready_tellers`         | 0     | counts free tellers; blocking on it is waiting in line                        |
| `customer_arrived[t]`   | 0     | customer tells teller t it has arrived (also used to wake tellers at closing) |
| `teller_asked[t]`       | 0     | teller t asks the customer for the transaction                                |
|  `customer_answered[t]` | 0     | customer tells teller t the transaction                                       |
| `transaction_done[t]`   | 0     | teller t tells the customer it is finished                                    |
| `customer_left[t]`      | 0     | customer tells teller t it has left                                           |

## Shared memory

`free_tellers` (which tellers are free), `current_customer[t]` and
`current_kind[t]` (who is at teller t and what they want),
`customers_served`, `closing`, and `tellers_ready`.

`customers_served` counts customers after they signal that they have left their
teller. The per-teller semaphores order access to `current_customer[t]` and
`current_kind[t]`, so those slots do not use `mutex`.

## Files

- `bank.py`: the whole simulation
- `devlog.md`: development log
- `README.md`: this file

## Notes

- Thread output has a colon after the bracket, including the
  "introduces itself" lines. The final closing message has no brackets or colon.
- The semaphores are not fair; the order in which waiting threads are woken
  may differ from run to run, so the output is different every time.
