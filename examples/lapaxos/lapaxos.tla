----------------------------- MODULE lapaxos -------------------
EXTENDS Integers, Sequences, FiniteSets, DistAlgoHelper, TLC

CONSTANTS N, P, M

VARIABLES pc, msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc, Proposer_to_consent_v

vars == << pc, msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc , Proposer_to_consent_v>>

Proposer == 1..N
Learner == N+1..N+P
Acceptor == N+P+1..N+P+M
process == Proposer \cup Learner \cup Acceptor

Init ==
    /\ pc = [ p \in process |-> IF p \in Proposer
                                THEN "Proposer_run_while_0"
                                ELSE IF p \in Learner
                                     THEN "Learner_learn_await_0"
                                     ELSE "Acceptor_run_await_0" ] 
    /\ msgQueue = [p \in process |-> << >> ]
    /\ clock = [p \in process |-> 0]
    /\ Proposer_majority = [ p \in Proposer |-> Acceptor ]
    /\ Proposer_n = [ p \in Proposer |-> <<  >> ]
    /\ Learner_learn_ret_pc = [ p \in Learner |-> "" ]
    /\ Proposer_yield_ret_pc = [ p \in Proposer |-> "" ]
    /\ Learner_yield_ret_pc = [ p \in Learner |-> "" ]
    /\ Acceptor_yield_ret_pc = [ p \in Acceptor |-> "" ]
    /\ Proposer_acceptors = [ p \in Proposer |-> Acceptor ]
    /\ Proposer_to_consent_ret_pc = [ p \in Proposer |-> "" ]
    /\ Proposer_to_consent_v = [ p \in Proposer |-> <<>> ]
    /\ rcvd = [ p \in process |-> { } ]
    /\ sent = [ p \in process |-> { } ]
    /\ Proposer_run_ret_pc = [ p \in Proposer |-> "" ]
    /\ Acceptor_run_ret_pc = [ p \in Acceptor |-> "" ]
    /\ Learner_run_ret_pc = [ p \in Learner |-> "" ]
    /\ Learner_acceptors = [ p \in Learner |-> Acceptor ]
    /\ atomic_barrier = -1
    /\ Proposer_anyof_s = 0
    /\ Acceptor_anyof_s = 0
    /\ Proposer_anyof_ret_pc = 0
    /\ Acceptor_anyof_ret_pc = 0
    /\ Acceptor_learners = [ p \in Acceptor |-> Learner ]
                                          
                                        

Send(self, content, dest, msgQ) ==
    /\ msgQueue' = [proc \in process |->
           
           IF   proc \in dest
           THEN Append(msgQ[proc], << "sent", << clock[self], self, proc >>, content >>)
           ELSE msgQ[proc]]
    /\ sent' = [sent EXCEPT ![self] = sent[self] \cup {<< "sent", << clock[self], proc, self >>, content >>: proc \in dest}]

Proposer_to_consent_endif_0(self) ==
    /\ pc[self] = "Proposer_to_consent_endif_0"
    /\ 
       LET Proposer_n_0 ==
               
               IF   Proposer_n[self] = <<>>
               THEN << 0, self >>
               ELSE << Proposer_n[self][1 + 0] + 1, self >>
       IN  /\ Proposer_n' = [Proposer_n EXCEPT ![self] = Proposer_n_0]
           /\ Send(self, << "prepare", Proposer_n_0 >>, Proposer_majority[self], msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "Proposer_to_consent_await_0"]
    /\ UNCHANGED << clock, atomic_barrier, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_to_consent_await_0(self) ==
    /\ pc[self] = "Proposer_to_consent_await_0"
    /\ Proposer_yield_ret_pc' = [Proposer_yield_ret_pc EXCEPT ![self] = "Proposer_to_consent_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Proposer_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v >>

Proposer_to_consent_await_0_1(self) ==
    /\ pc[self] = "Proposer_to_consent_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   Cardinality({
            LET Proposer_to_consent_a_2 ==
                    _value_2[2][3]
            IN  Proposer_to_consent_a_2: _value_2 \in {_value_2 \in rcvd[self]:
                    /\ Len(_value_2) = 3
                    /\ Len(_value_2[2]) = 3
                    /\ Len(_value_2[3]) = 3
                    /\ _value_2[3][1] = "respond"
                    /\ _value_2[3][2] = Proposer_n[self]}}) > Cardinality(Proposer_acceptors[self]) \div 2
       THEN "Proposer_to_consent_await_end_0"
       ELSE "Proposer_to_consent_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_to_consent_await_end_0(self) ==
    /\ pc[self] = "Proposer_to_consent_await_end_0"
    /\ 
       LET Proposer_to_consent_v_0 ==
               
               IF   Cardinality(SetOr(<< {
                    LET Proposer_to_consent_n2_4 ==
                            _value_6[3][3][1]
                    IN  Proposer_to_consent_v[self]: _value_6 \in {_value_6 \in rcvd[self]:
                            /\ /\ Len(_value_6) = 3
                               /\ Len(_value_6[2]) = 3
                               /\ Len(_value_6[3]) = 3
                               /\ _value_6[3][1] = "respond"
                               /\ _value_6[3][2] = Proposer_n[self]
                               /\ Len(_value_6[3][3]) = 2
                               /\ _value_6[3][3][2] = Proposer_to_consent_v[self]
                            /\ _value_6[3][3][1] = MaxTuple({
                               LET Proposer_to_consent_n2_6 ==
                                       _value_8[3][3][1]
                               IN  Proposer_to_consent_n2_6: _value_8 \in {_value_8 \in rcvd[self]:
                                       /\ Len(_value_8) = 3
                                       /\ Len(_value_8[2]) = 3
                                       /\ Len(_value_8[3]) = 3
                                       /\ _value_8[3][1] = "respond"
                                       /\ _value_8[3][2] = Proposer_n[self]
                                       /\ Len(_value_8[3][3]) = 2}})}}, {CHOOSE _random_2 \in 1..100 : TRUE} >>)) > 0
               THEN CHOOSE _random_3 \in SetOr(<< {
                    LET Proposer_to_consent_n2_7 ==
                            _value_9[3][3][1]
                    IN  Proposer_to_consent_v[self]: _value_9 \in {_value_9 \in rcvd[self]:
                            /\ /\ Len(_value_9) = 3
                               /\ Len(_value_9[2]) = 3
                               /\ Len(_value_9[3]) = 3
                               /\ _value_9[3][1] = "respond"
                               /\ _value_9[3][2] = Proposer_n[self]
                               /\ Len(_value_9[3][3]) = 2
                               /\ _value_9[3][3][2] = Proposer_to_consent_v[self]
                            /\ _value_9[3][3][1] = MaxTuple({
                               LET Proposer_to_consent_n2_9 ==
                                       _value_11[3][3][1]
                               IN  Proposer_to_consent_n2_9: _value_11 \in {_value_11 \in rcvd[self]:
                                       /\ Len(_value_11) = 3
                                       /\ Len(_value_11[2]) = 3
                                       /\ Len(_value_11[3]) = 3
                                       /\ _value_11[3][1] = "respond"
                                       /\ _value_11[3][2] = Proposer_n[self]
                                       /\ Len(_value_11[3][3]) = 2}})}}, {CHOOSE _random_4 \in 1..100 : TRUE} >>) : TRUE
               ELSE <<>>
       IN  /\ Proposer_to_consent_v' = [Proposer_to_consent_v EXCEPT ![self] = Proposer_to_consent_v_0]
           /\ Send(self, << "accept", Proposer_n[self], Proposer_to_consent_v_0 >>, {
              LET Proposer_to_consent_a_3 ==
                      _value_12[2][3]
              IN  Proposer_to_consent_a_3: _value_12 \in {_value_12 \in rcvd[self]:
                      /\ Len(_value_12) = 3
                      /\ Len(_value_12[2]) = 3
                      /\ Len(_value_12[3]) = 3
                      /\ _value_12[3][1] = "respond"
                      /\ _value_12[3][2] = Proposer_n[self]}}, msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "Proposer_to_consent_end"]
    /\ UNCHANGED << clock, atomic_barrier, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_to_consent_end(self) ==
    /\ pc[self] = "Proposer_to_consent_end"
    /\ pc' = [pc EXCEPT ![self] = Proposer_to_consent_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_run_while_0(self) ==
    /\ pc[self] = "Proposer_run_while_0"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \neg \E _value_13 \in {_value_13 \in rcvd[self]:
                       /\ Len(_value_13) = 3
                       /\ Len(_value_13[2]) = 3
                       /\ Len(_value_13[3]) = 1
                       /\ _value_13[3][1] = "done"}:
                     TRUE
       THEN "Proposer_run_while_body_0"
       ELSE "Proposer_run_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_run_while_body_0(self) ==
    /\ pc[self] = "Proposer_run_while_body_0"
    /\ Proposer_to_consent_ret_pc' = [Proposer_to_consent_ret_pc EXCEPT ![self] = "Proposer_run_while_body_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Proposer_to_consent_endif_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_run_while_body_0_1(self) ==
    /\ pc[self] = "Proposer_run_while_body_0_1"
    /\ pc' = [pc EXCEPT ![self] = "Proposer_run_while_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_run_end(self) ==
    /\ pc[self] = "Proposer_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_anyof_endif_0(self) ==
    /\ pc[self] = "Proposer_anyof_endif_0"
    /\ pc' = [pc EXCEPT ![self] = "Proposer_anyof_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_anyof_end(self) ==
    /\ pc[self] = "Proposer_anyof_end"
    /\ pc' = [pc EXCEPT ![self] = Proposer_anyof_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Proposer_yield(self) ==
    /\ pc[self] = "Proposer_yield"
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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", << msg[2][1], msg[2][3], msg[2][2] >>, msg[3] >>}]
                /\ /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Proposer_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_run_await_0(self) ==
    /\ pc[self] = "Acceptor_run_await_0"
    /\ Acceptor_yield_ret_pc' = [Acceptor_yield_ret_pc EXCEPT ![self] = "Acceptor_run_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Acceptor_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_run_await_0_1(self) ==
    /\ pc[self] = "Acceptor_run_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \E _value_14 \in {_value_14 \in rcvd[self]:
                  /\ Len(_value_14) = 3
                  /\ Len(_value_14[2]) = 3
                  /\ Len(_value_14[3]) = 1
                  /\ _value_14[3][1] = "done"}:
                TRUE
       THEN "Acceptor_run_end"
       ELSE "Acceptor_run_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_run_end(self) ==
    /\ pc[self] = "Acceptor_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_anyof_endif_0(self) ==
    /\ pc[self] = "Acceptor_anyof_endif_0"
    /\ pc' = [pc EXCEPT ![self] = "Acceptor_anyof_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_anyof_end(self) ==
    /\ pc[self] = "Acceptor_anyof_end"
    /\ pc' = [pc EXCEPT ![self] = Acceptor_anyof_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Acceptor_yield(self) ==
    /\ pc[self] = "Acceptor_yield"
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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", << msg[2][1], msg[2][3], msg[2][2] >>, msg[3] >>}]
                /\ /\ 
                      IF   /\ Len(msg) = 3
                           /\ Len(msg[2]) = 3
                           /\ Len(msg[3]) = 2
                           /\ msg[3][1] = "prepare"
                      THEN 
                           LET Acceptor__Acceptor_handler_413_p_1 ==
                                   msg[2][2]
                               Acceptor__Acceptor_handler_413_n_1 ==
                                   msg[3][2]
                           IN  /\ 
                                  IF   \A _value_15 \in {_value_15 \in sent[self]:
                                             /\ Len(_value_15) = 3
                                             /\ Len(_value_15[2]) = 3
                                             /\ Len(_value_15[3]) = 3
                                             /\ _value_15[3][1] = "respond"}:
                                           
                                           LET Acceptor__Acceptor_handler_413_n2_1 ==
                                                   _value_15[3][2]
                                           IN  Acceptor__Acceptor_handler_413_n_1 \succ Acceptor__Acceptor_handler_413_n2_1
                                  THEN /\ Send(self, << "respond", Acceptor__Acceptor_handler_413_n_1, 
                                          IF   Cardinality({
                                               LET Acceptor__Acceptor_handler_413_n_5 ==
                                                       _value_19[3][2]
                                                   Acceptor__Acceptor_handler_413_v_2 ==
                                                       _value_19[3][3]
                                               IN  << Acceptor__Acceptor_handler_413_n_5, Acceptor__Acceptor_handler_413_v_2 >>: _value_19 \in {_value_19 \in sent[self]:
                                                       /\ /\ Len(_value_19) = 3
                                                          /\ Len(_value_19[2]) = 3
                                                          /\ Len(_value_19[3]) = 3
                                                          /\ _value_19[3][1] = "accepted"
                                                       /\ _value_19[3][2] = MaxTuple({
                                                          LET Acceptor__Acceptor_handler_413_n_7 ==
                                                                  _value_21[3][2]
                                                          IN  Acceptor__Acceptor_handler_413_n_7: _value_21 \in {_value_21 \in sent[self]:
                                                                  /\ Len(_value_21) = 3
                                                                  /\ Len(_value_21[2]) = 3
                                                                  /\ Len(_value_21[3]) = 3
                                                                  /\ _value_21[3][1] = "accepted"}})}}) > 0
                                          THEN CHOOSE _random_5 \in {
                                               LET Acceptor__Acceptor_handler_413_n_8 ==
                                                       _value_22[3][2]
                                                   Acceptor__Acceptor_handler_413_v_3 ==
                                                       _value_22[3][3]
                                               IN  << Acceptor__Acceptor_handler_413_n_8, Acceptor__Acceptor_handler_413_v_3 >>: _value_22 \in {_value_22 \in sent[self]:
                                                       /\ /\ Len(_value_22) = 3
                                                          /\ Len(_value_22[2]) = 3
                                                          /\ Len(_value_22[3]) = 3
                                                          /\ _value_22[3][1] = "accepted"
                                                       /\ _value_22[3][2] = MaxTuple({
                                                          LET Acceptor__Acceptor_handler_413_n_10 ==
                                                                  _value_24[3][2]
                                                          IN  Acceptor__Acceptor_handler_413_n_10: _value_24 \in {_value_24 \in sent[self]:
                                                                  /\ Len(_value_24) = 3
                                                                  /\ Len(_value_24[2]) = 3
                                                                  /\ Len(_value_24[3]) = 3
                                                                  /\ _value_24[3][1] = "accepted"}})}} : TRUE
                                          ELSE <<>> >>, {Acceptor__Acceptor_handler_413_p_1}, [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                                       /\ UNCHANGED << pc, atomic_barrier, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
                                  ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                       /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
                      ELSE /\ 
                              IF   /\ Len(msg) = 3
                                   /\ Len(msg[2]) = 3
                                   /\ Len(msg[3]) = 3
                                   /\ msg[3][1] = "accept"
                              THEN 
                                   LET Acceptor__Acceptor_handler_517_n_1 ==
                                           msg[3][2]
                                       Acceptor__Acceptor_handler_517_v_1 ==
                                           msg[3][3]
                                   IN  /\ 
                                          IF   \neg \E _value_25 \in {_value_25 \in sent[self]:
                                                          /\ Len(_value_25) = 3
                                                          /\ Len(_value_25[2]) = 3
                                                          /\ Len(_value_25[3]) = 3
                                                          /\ _value_25[3][1] = "respond"}:
                                                        
                                                        LET Acceptor__Acceptor_handler_517_n2_1 ==
                                                                _value_25[3][2]
                                                        IN  Acceptor__Acceptor_handler_517_n2_1 \succ Acceptor__Acceptor_handler_517_n_1
                                          THEN /\ Send(self, << "accepted", Acceptor__Acceptor_handler_517_n_1, Acceptor__Acceptor_handler_517_v_1 >>, Acceptor_learners[self], [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                                               /\ UNCHANGED << pc, atomic_barrier, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
                                          ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                               /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
                              ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                   /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Acceptor_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_learn_await_0(self) ==
    /\ pc[self] = "Learner_learn_await_0"
    /\ Learner_yield_ret_pc' = [Learner_yield_ret_pc EXCEPT ![self] = "Learner_learn_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Learner_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_learn_await_0_1(self) ==
    /\ pc[self] = "Learner_learn_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \E _value_26 \in {_value_26 \in rcvd[self]:
                  /\ Len(_value_26) = 3
                  /\ Len(_value_26[2]) = 3
                  /\ Len(_value_26[3]) = 3
                  /\ _value_26[3][1] = "accepted"}:
                
                LET Learner_learn_n_1 ==
                        _value_26[3][2]
                    Learner_learn_v_1 ==
                        _value_26[3][3]
                IN  Cardinality({
                    LET Learner_learn_a_2 ==
                            _value_28[2][3]
                    IN  Learner_learn_a_2: _value_28 \in {_value_28 \in rcvd[self]:
                            /\ Len(_value_28) = 3
                            /\ Len(_value_28[2]) = 3
                            /\ Len(_value_28[3]) = 3
                            /\ _value_28[3][1] = "accepted"
                            /\ _value_28[3][2] = Learner_learn_n_1
                            /\ _value_28[3][3] = Learner_learn_v_1}}) > Cardinality(Learner_acceptors[self]) \div 2
       THEN "Learner_learn_end"
       ELSE "Learner_learn_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_learn_end(self) ==
    /\ pc[self] = "Learner_learn_end"
    /\ pc' = [pc EXCEPT ![self] = Learner_learn_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_run_label_0(self) ==
    /\ pc[self] = "Learner_run_label_0"
    /\ Learner_learn_ret_pc' = [Learner_learn_ret_pc EXCEPT ![self] = "Learner_run_end"]
    /\ pc' = [pc EXCEPT ![self] = "Learner_learn_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_run_end(self) ==
    /\ pc[self] = "Learner_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Learner_yield(self) ==
    /\ pc[self] = "Learner_yield"
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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", << msg[2][1], msg[2][3], msg[2][2] >>, msg[3] >>}]
                /\ /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Learner_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_to_consent_v, Proposer_yield_ret_pc >>

Next == \/ \E self \in process :
            \/ Proposer_to_consent_endif_0(self)
            \/ Proposer_to_consent_await_0(self)
            \/ Proposer_to_consent_await_0_1(self)
            \/ Proposer_to_consent_await_end_0(self)
            \/ Proposer_to_consent_end(self)
            \/ Proposer_run_while_0(self)
            \/ Proposer_run_while_body_0(self)
            \/ Proposer_run_while_body_0_1(self)
            \/ Proposer_run_end(self)
            \/ Proposer_anyof_endif_0(self)
            \/ Proposer_anyof_end(self)
            \/ Proposer_yield(self)
            \/ Acceptor_run_await_0(self)
            \/ Acceptor_run_await_0_1(self)
            \/ Acceptor_run_end(self)
            \/ Acceptor_anyof_endif_0(self)
            \/ Acceptor_anyof_end(self)
            \/ Acceptor_yield(self)
            \/ Learner_learn_await_0(self)
            \/ Learner_learn_await_0_1(self)
            \/ Learner_learn_end(self)
            \/ Learner_run_label_0(self)
            \/ Learner_run_end(self)
            \/ Learner_yield(self)


Spec == Init /\ [][Next]_vars

==============================================================
