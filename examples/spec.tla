----------------------------- MODULE spec -------------------
EXTENDS Integers, Sequences, FiniteSets, TLC


VARIABLES pc, msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc


Send(self, content, dest, msgQ) ==
    /\ msgQueue' = [proc \in process |->
           
           IF   proc \in dest
           THEN Append(msgQ[proc], << "sent", << clock[self], self, proc >>, content >>)
           ELSE msgQ[proc]]

P_mutex_label_0(self) ==
    /\ pc[self] = "P_mutex_label_0"
    /\ 
       LET P_mutex_c_0 ==
               clock[self]
       IN  /\ P_mutex_c' = [P_mutex_c EXCEPT ![self] = P_mutex_c_0]
           /\ Send(self, << "request", P_mutex_c_0, self >>, P_s[self], msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "P_mutex_await_0"]
    /\ UNCHANGED << clock, atomic_barrier, rcvd, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_mutex_await_0(self) ==
    /\ pc[self] = "P_mutex_await_0"
    /\ P_yield_ret_pc' = [P_yield_ret_pc EXCEPT ![self] = "P_mutex_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "P_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s >>

P_mutex_await_0_1(self) ==
    /\ pc[self] = "P_mutex_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   /\ \A _value_1 \in {_value_1 \in rcvd[self]:
                     /\ Len(_value_1) = 3
                     /\ Len(_value_1[2]) = 3
                     /\ Len(_value_1[3]) = 3
                     /\ _value_1[3][1] = "request"}:
                   
                   LET P_mutex_c2_1 ==
                           _value_1[3][2]
                       P_mutex_p_1 ==
                           _value_1[3][3]
                   IN  \/ \E _value_2 \in {_value_2 \in rcvd[self]:
                                /\ Len(_value_2) = 3
                                /\ Len(_value_2[2]) = 3
                                /\ Len(_value_2[3]) = 3
                                /\ _value_2[3][1] = "release"
                                /\ _value_2[3][2] = P_mutex_c2_1
                                /\ _value_2[3][3] = P_mutex_p_1}:
                              TRUE
                       \/ << P_mutex_c[self], self >> < << P_mutex_c2_1, P_mutex_p_1 >>
            /\ \A _value_3 \in {_value_3 \in P_s[self]:
                     TRUE}:
                   
                   LET P_mutex_p_2 ==
                           _value_3
                   IN  \E _value_4 \in {_value_4 \in rcvd[self]:
                             /\ Len(_value_4) = 3
                             /\ Len(_value_4[2]) = 3
                             /\ Len(_value_4[3]) = 3
                             /\ _value_4[3][1] = "ack"
                             /\ _value_4[3][2] = P_mutex_c[self]
                             /\ _value_4[3][3] = P_mutex_p_2}:
                           TRUE
       THEN "P_mutex_await_end_0"
       ELSE "P_mutex_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_mutex_await_end_0(self) ==
    /\ pc[self] = "P_mutex_await_end_0"
    /\ Send(self, << "release", P_mutex_c[self], self >>, P_s[self], msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "P_mutex_end"]
    /\ UNCHANGED << clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_mutex_end(self) ==
    /\ pc[self] = "P_mutex_end"
    /\ pc' = [pc EXCEPT ![self] = P_mutex_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_while_0(self) ==
    /\ pc[self] = "P_run_while_0"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   P_nrequests[self] > 0
       THEN "P_run_while_body_0"
       ELSE "P_run_while_end_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_while_body_0(self) ==
    /\ pc[self] = "P_run_while_body_0"
    /\ P_mutex_ret_pc' = [P_mutex_ret_pc EXCEPT ![self] = "P_run_while_body_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "P_mutex_label_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_while_body_0_1(self) ==
    /\ pc[self] = "P_run_while_body_0_1"
    /\ 
       LET P_nrequests_0 ==
               P_nrequests[self] - 1
       IN  /\ P_nrequests' = [P_nrequests EXCEPT ![self] = P_nrequests_0]
    /\ pc' = [pc EXCEPT ![self] = "P_run_while_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_while_end_0(self) ==
    /\ pc[self] = "P_run_while_end_0"
    /\ Send(self, << "done", self >>, P_s[self], msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "P_run_await_0"]
    /\ UNCHANGED << clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_await_0(self) ==
    /\ pc[self] = "P_run_await_0"
    /\ P_yield_ret_pc' = [P_yield_ret_pc EXCEPT ![self] = "P_run_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "P_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s >>

P_run_await_0_1(self) ==
    /\ pc[self] = "P_run_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \A _value_5 \in {_value_5 \in P_s[self]:
                  TRUE}:
                
                LET P_run_p_1 ==
                        _value_5
                IN  \E _value_6 \in {_value_6 \in rcvd[self]:
                          /\ Len(_value_6) = 3
                          /\ Len(_value_6[2]) = 3
                          /\ Len(_value_6[3]) = 2
                          /\ _value_6[3][1] = "done"
                          /\ _value_6[3][2] = P_run_p_1}:
                        TRUE
       THEN "P_run_end"
       ELSE "P_run_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_run_end(self) ==
    /\ pc[self] = "P_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>

P_yield(self) ==
    /\ pc[self] = "P_yield"
    /\ atomic_barrier = -1
    /\ 
       LET msg ==
               Head(msgQueue[self])
       IN  
           IF   msgQueue[self] # <<  >>
           THEN /\ clock' = [clock EXCEPT ![self] = 1 + 
                   IF   msg[2][1] > @
                   THEN msg[2][1]
                   ELSE @]
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", msg[1], msg[2] >>}]
                /\ /\ 
                      IF   /\ Len(msg) = 3
                           /\ Len(msg[2]) = 3
                           /\ Len(msg[3]) = 3
                           /\ msg[3][1] = "request"
                      THEN 
                           LET P__P_handler_276_c_1 ==
                                   msg[3][2]
                               P__P_handler_276_p_1 ==
                                   msg[3][3]
                           IN  /\ Send(self, << "ack", P__P_handler_276_c_1, self >>, {P__P_handler_276_p_1}, [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                               /\ UNCHANGED << pc, atomic_barrier, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>
                      ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                           /\ UNCHANGED << pc, atomic_barrier, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = P_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>


==============================================================
