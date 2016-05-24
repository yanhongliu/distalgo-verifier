----------------------------- MODULE spec -------------------
EXTENDS Integers, Sequences, FiniteSets, TLC


VARIABLES pc, msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_run_ret_pc, P_s, P_yield_ret_pc, P_nrequests
vars == << pc, msgQueue, clock, atomic_barrier, rcvd, P_mutex_c, P_mutex_ret_pc, P_run_ret_pc, P_s, P_yield_ret_pc, P_nrequests >>

CONSTANTS N, NREQ

a \prec b ==  \/ a [ 1 ] < b [ 1 ]
              \/ a [ 1 ] = b [ 1 ] /\ a [ 2 ] < b [ 2 ]


process == 1..N

Init == /\ clock = [ p \in process |-> 0 ]
        /\ pc = [ p \in process |-> "P_yield" ]
        /\ msgQueue = [ p \in process |-> << >> ]
        /\ rcvd = [ p \in process |-> { } ]
        /\ atomic_barrier = -1
        /\ P_mutex_c = [ p \in process |-> 0 ]
        /\ P_mutex_ret_pc = [ p \in process |-> "" ]
        /\ P_run_ret_pc = [ p \in process |-> "" ]
        /\ P_s = [ p \in process |-> process \ {p} ]
        /\ P_yield_ret_pc = [ p \in process |-> "P_run_while_body_0" ]
        /\ P_nrequests = [ p \in process |-> NREQ ]
        

Send(self, content, dest, msgQ) ==
    LET msg ==
            [timestamp |-> clock[self], src |-> self, content |-> content]
    IN  /\ msgQueue' = [proc \in process |->
               
               IF   proc \in dest
               THEN Append(msgQ[proc], msg)
               ELSE msgQ[proc]]

P_mutex_label_0(self) ==
    /\ pc[self] = "P_mutex_label_0"
    /\ LET P_mutex_c_0 ==
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
       IF   /\ \A _value \in {_value \in rcvd[self]:
                     /\ Len(_value) = 3
                     /\ _value[1] = "request"}:
                   LET P_mutex_c2 ==
                           _value[2]
                       P_mutex_p ==
                           _value[3]
                   IN  \/ \E _value_1 \in rcvd[self]:
                              /\ Len(_value_1) = 3
                              /\ _value_1[1] = "release"
                              /\ _value_1[2] = P_mutex_c2
                              /\ _value_1[3] = P_mutex_p
                       \/ << P_mutex_c[self], self >> \prec << P_mutex_c2, P_mutex_p >>
            /\ \A _value \in {_value \in P_s[self]:
                     TRUE}:
                   LET P_mutex_p ==
                           _value
                   IN  \E _value_2 \in rcvd[self]:
                           /\ Len(_value_2) = 3
                           /\ _value_2[1] = "ack"
                           /\ _value_2[2] = P_mutex_c[self]
                           /\ _value_2[3] = P_mutex_p
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
    /\ LET P_nrequests_0 ==
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
       IF   \A _value \in {_value \in P_s[self]:
                  TRUE}:
                LET P_run_p ==
                        _value
                IN  \E _value_3 \in rcvd[self]:
                        /\ Len(_value_3) = 2
                        /\ _value_3[1] = "done"
                        /\ _value_3[2] = P_run_p
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
    /\ LET msg ==
               Head(msgQueue[self])
       IN  
           IF   msgQueue[self] # <<  >>
           THEN /\ clock' = [clock EXCEPT ![self] = 1 + 
                   IF   msg.timestamp > @
                   THEN msg.timestamp
                   ELSE @]
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {msg.content}]
                /\ /\ 
                      IF   /\ Len(msg.content) = 3
                           /\ msg.content[1] = "request"
                      THEN LET P_receive_1_c ==
                                   msg.content[2]
                               P_receive_1_p ==
                                   msg.content[3]
                           IN  /\ Send(self, << "ack", P_receive_1_c, self >>, {P_receive_1_p}, [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                               /\ UNCHANGED << pc, atomic_barrier, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>
                      ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                           /\ UNCHANGED << pc, atomic_barrier, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = P_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, rcvd, P_mutex_c, P_mutex_ret_pc, P_nrequests, P_run_ret_pc, P_s, P_yield_ret_pc >>
        
Next == \E p \in process :
            \/ P_run_while_0(p)
            \/ P_run_while_body_0(p)
            \/ P_run_while_body_0_1(p)
            \/ P_run_while_end_0(p)
            \/ P_run_await_0(p)
            \/ P_run_await_0_1(p)
            \/ P_run_end(p)
            \/ P_mutex_label_0(p)
            \/ P_yield(p)
            \/ P_mutex_await_0(p)
            \/ P_mutex_await_end_0(p)
            \/ P_mutex_await_0_1(p)
            \/ P_mutex_end(p)
            
Fair == \A p \in process :
            /\ WF_vars(P_run_while_0(p))
            /\ WF_vars(P_run_while_body_0(p))
            /\ WF_vars(P_run_while_body_0_1(p))
            /\ WF_vars(P_run_while_end_0(p))
            /\ WF_vars(P_run_await_0(p))
            /\ WF_vars(P_run_await_0_1(p))
            /\ WF_vars(P_run_end(p))
            /\ WF_vars(P_mutex_label_0(p))
            /\ SF_vars(P_yield(p))
            /\ WF_vars(P_mutex_await_0(p))
            /\ WF_vars(P_mutex_await_end_0(p))
            /\ WF_vars(P_mutex_await_0_1(p))
            /\ WF_vars(P_mutex_end(p))
Safety == \A m, n \in process : ( pc[m] = "P_mutex_await_end_0" /\ pc[n] = "P_mutex_await_end_0" => m = n )
Liveness == \A self \in process : pc[self] = "P_mutex_label_0" ~> pc[self] = "P_mutex_await_end_0"

Spec == Init /\ [][Next]_vars /\ Fair

==============================================================
