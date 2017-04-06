----------------------------- MODULE orig -------------------
EXTENDS Integers, Sequences, FiniteSets, TLC


VARIABLES pc, msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc


Send(self, content, dest, msgQ) ==
    /\ msgQueue' = [proc \in process |->
           
           IF   proc \in dest
           THEN Append(msgQ[proc], << "sent", << clock[self], self, proc >>, content >>)
           ELSE msgQ[proc]]
    /\ sent' = [sent EXCEPT ![self] = sent[self] \cup {<< "sent", << clock[self], self, proc >>, content >>: proc \in dest}]

Proposer_to_consent_endif_0(self) ==
    /\ pc[self] = "Proposer_to_consent_endif_0"
    /\ 
       LET Proposer_n_0 ==
               
               IF   Proposer_n[self] = <<>>
               THEN << 0, self >>
               ELSE << Proposer_n[self][0] + 1, self >>
       IN  /\ Proposer_n' = [Proposer_n EXCEPT ![self] = Proposer_n_0]
           /\ Send(self, << "prepare", Proposer_n_0 >>, Proposer_majority[self], msgQueue)
    /\ pc' = [pc EXCEPT ![self] = "Proposer_to_consent_await_0"]

Proposer_to_consent_await_0(self) ==
    /\ pc[self] = "Proposer_to_consent_await_0"
    /\ Proposer_yield_ret_pc' = [Proposer_yield_ret_pc EXCEPT ![self] = "Proposer_to_consent_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Proposer_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc >>

Proposer_to_consent_await_0_1(self) ==
    /\ pc[self] = "Proposer_to_consent_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   Cardinality({
            LET Proposer_to_consent_a_1 ==
                    _value_1[2][3]
            IN  Proposer_to_consent_a_1: _value_1 \in {_value_1 \in rcvd[self]:
                    /\ Len(_value_1) = 3
                    /\ Len(_value_1[2]) = 3
                    /\ Len(_value_1[3]) = 3
                    /\ _value_1[3][1] = "respond"
                    /\ _value_1[3][2] = Proposer_n[self]}}) > Len(Proposer_acceptors[self]) \div 2
       THEN "Proposer_to_consent_end"
       ELSE "Proposer_to_consent_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_to_consent_end(self) ==
    /\ pc[self] = "Proposer_to_consent_end"
    /\ pc' = [pc EXCEPT ![self] = Proposer_to_consent_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_run_while_0(self) ==
    /\ pc[self] = "Proposer_run_while_0"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \neg \E _value_2 \in {_value_2 \in rcvd[self]:
                       /\ Len(_value_2) = 3
                       /\ Len(_value_2[2]) = 3
                       /\ Len(_value_2[3]) = 1
                       /\ _value_2[3][1] = "done"}:
                     TRUE
       THEN "Proposer_run_while_body_0"
       ELSE "Proposer_run_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_run_while_body_0(self) ==
    /\ pc[self] = "Proposer_run_while_body_0"
    /\ Proposer_to_consent_ret_pc' = [Proposer_to_consent_ret_pc EXCEPT ![self] = "Proposer_run_while_body_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Proposer_to_consent_endif_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_yield_ret_pc >>

Proposer_run_while_body_0_1(self) ==
    /\ pc[self] = "Proposer_run_while_body_0_1"
    /\ pc' = [pc EXCEPT ![self] = "Proposer_run_while_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_run_end(self) ==
    /\ pc[self] = "Proposer_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_anyof_endif_0(self) ==
    /\ pc[self] = "Proposer_anyof_endif_0"
    /\ pc' = [pc EXCEPT ![self] = "Proposer_anyof_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Proposer_anyof_end(self) ==
    /\ pc[self] = "Proposer_anyof_end"
    /\ pc' = [pc EXCEPT ![self] = Proposer_anyof_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", msg[1], msg[2] >>}]
                /\ /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Proposer_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Learner_learn_await_0(self) ==
    /\ pc[self] = "Learner_learn_await_0"
    /\ Learner_yield_ret_pc' = [Learner_yield_ret_pc EXCEPT ![self] = "Learner_learn_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Learner_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Learner_learn_await_0_1(self) ==
    /\ pc[self] = "Learner_learn_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \E _value_3 \in {_value_3 \in rcvd[self]:
                  /\ Len(_value_3) = 3
                  /\ Len(_value_3[2]) = 3
                  /\ Len(_value_3[3]) = 3
                  /\ _value_3[3][1] = "accepted"}:
                
                LET Learner_learn_n_1 ==
                        _value_3[3][2]
                    Learner_learn_v_1 ==
                        _value_3[3][3]
                IN  Cardinality({
                    LET Learner_learn_a_1 ==
                            _value_4[2][3]
                    IN  Learner_learn_a_1: _value_4 \in {_value_4 \in rcvd[self]:
                            /\ Len(_value_4) = 3
                            /\ Len(_value_4[2]) = 3
                            /\ Len(_value_4[3]) = 3
                            /\ _value_4[3][1] = "accepted"
                            /\ _value_4[3][2] = Learner_learn_n_1
                            /\ _value_4[3][3] = Learner_learn_v_1}}) > Len(Learner_acceptors[self]) \div 2
       THEN "Learner_learn_end"
       ELSE "Learner_learn_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Learner_learn_end(self) ==
    /\ pc[self] = "Learner_learn_end"
    /\ pc' = [pc EXCEPT ![self] = Learner_learn_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Learner_run_label_0(self) ==
    /\ pc[self] = "Learner_run_label_0"
    /\ Learner_learn_ret_pc' = [Learner_learn_ret_pc EXCEPT ![self] = "Learner_run_end"]
    /\ pc' = [pc EXCEPT ![self] = "Learner_learn_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Learner_run_end(self) ==
    /\ pc[self] = "Learner_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", msg[1], msg[2] >>}]
                /\ /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Learner_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Acceptor_run_await_0(self) ==
    /\ pc[self] = "Acceptor_run_await_0"
    /\ Acceptor_yield_ret_pc' = [Acceptor_yield_ret_pc EXCEPT ![self] = "Acceptor_run_await_0_1"]
    /\ pc' = [pc EXCEPT ![self] = "Acceptor_yield"]
    /\ atomic_barrier' = -1
    /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Acceptor_run_await_0_1(self) ==
    /\ pc[self] = "Acceptor_run_await_0_1"
    /\ pc' = [pc EXCEPT ![self] = 
       IF   \E _value_5 \in {_value_5 \in rcvd[self]:
                  /\ Len(_value_5) = 3
                  /\ Len(_value_5[2]) = 3
                  /\ Len(_value_5[3]) = 1
                  /\ _value_5[3][1] = "done"}:
                TRUE
       THEN "Acceptor_run_end"
       ELSE "Acceptor_run_await_0"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Acceptor_run_end(self) ==
    /\ pc[self] = "Acceptor_run_end"
    /\ atomic_barrier' = -1
    /\ UNCHANGED << pc, msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Acceptor_anyof_endif_0(self) ==
    /\ pc[self] = "Acceptor_anyof_endif_0"
    /\ pc' = [pc EXCEPT ![self] = "Acceptor_anyof_end"]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

Acceptor_anyof_end(self) ==
    /\ pc[self] = "Acceptor_anyof_end"
    /\ pc' = [pc EXCEPT ![self] = Acceptor_anyof_ret_pc[self]]
    /\ UNCHANGED << msgQueue, clock, atomic_barrier, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>

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
                /\ rcvd' = [rcvd EXCEPT ![self] = rcvd[self] \cup {<< "rcvd", msg[1], msg[2] >>}]
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
                                  IF   \A _value_6 \in {_value_6 \in sent[self]:
                                             /\ Len(_value_6) = 3
                                             /\ Len(_value_6[2]) = 3
                                             /\ Len(_value_6[3]) = 3
                                             /\ _value_6[3][1] = "respond"}:
                                           
                                           LET Acceptor__Acceptor_handler_413_n2_1 ==
                                                   _value_6[3][2]
                                           IN  Acceptor__Acceptor_handler_413_n_1 > Acceptor__Acceptor_handler_413_n2_1
                                  THEN /\ Send(self, << "respond", Acceptor__Acceptor_handler_413_n_1, 
                                          IF   Cardinality({
                                               LET Acceptor__Acceptor_handler_413_n_4 ==
                                                       _value_9[3][2]
                                                   Acceptor__Acceptor_handler_413_v_2 ==
                                                       _value_9[3][3]
                                               IN  << Acceptor__Acceptor_handler_413_n_4, Acceptor__Acceptor_handler_413_v_2 >>: _value_9 \in {_value_9 \in sent[self]:
                                                       /\ Len(_value_9) = 3
                                                       /\ Len(_value_9[2]) = 3
                                                       /\ Len(_value_9[3]) = 3
                                                       /\ _value_9[3][1] = "accepted"}}) > 0
                                          THEN CHOOSE _random \in {
                                               LET Acceptor__Acceptor_handler_413_n_6 ==
                                                       _value_11[3][2]
                                                   Acceptor__Acceptor_handler_413_v_3 ==
                                                       _value_11[3][3]
                                               IN  << Acceptor__Acceptor_handler_413_n_6, Acceptor__Acceptor_handler_413_v_3 >>: _value_11 \in {_value_11 \in sent[self]:
                                                       /\ Len(_value_11) = 3
                                                       /\ Len(_value_11[2]) = 3
                                                       /\ Len(_value_11[3]) = 3
                                                       /\ _value_11[3][1] = "accepted"}} : TRUE
                                          ELSE <<>> >>, Acceptor__Acceptor_handler_413_p_1, [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                                       /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
                                  ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                       /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
                      ELSE /\ 
                              IF   /\ Len(msg) = 3
                                   /\ Len(msg[2]) = 3
                                   /\ Len(msg[3]) = 3
                                   /\ msg[3][1] = "accept"
                              THEN 
                                   LET Acceptor__Acceptor_handler_516_n_1 ==
                                           msg[3][2]
                                       Acceptor__Acceptor_handler_516_v_1 ==
                                           msg[3][3]
                                   IN  /\ 
                                          IF   \neg \E _value_13 \in {_value_13 \in sent[self]:
                                                          /\ Len(_value_13) = 3
                                                          /\ Len(_value_13[2]) = 3
                                                          /\ Len(_value_13[3]) = 3
                                                          /\ _value_13[3][1] = "respond"}:
                                                        
                                                        LET Acceptor__Acceptor_handler_516_n2_1 ==
                                                                _value_13[3][2]
                                                        IN  Acceptor__Acceptor_handler_516_n2_1 > Acceptor__Acceptor_handler_516_n_1
                                          THEN /\ Send(self, << "accepted", Acceptor__Acceptor_handler_516_n_1, Acceptor__Acceptor_handler_516_v_1 >>, Acceptor_learners[self], [msgQueue EXCEPT ![self] = Tail(msgQueue[self])])
                                               /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
                                          ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                               /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
                              ELSE /\ msgQueue' = [msgQueue EXCEPT ![self] = Tail(@)]
                                   /\ UNCHANGED << pc, atomic_barrier, sent, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>
           ELSE /\ atomic_barrier' = self
                /\ pc' = [pc EXCEPT ![self] = Acceptor_yield_ret_pc[self]]
                /\ UNCHANGED << msgQueue, clock, sent, rcvd, Acceptor_anyof_ret_pc, Acceptor_anyof_s, Acceptor_learners, Acceptor_run_ret_pc, Acceptor_yield_ret_pc, Learner_acceptors, Learner_learn_ret_pc, Learner_run_ret_pc, Learner_yield_ret_pc, Proposer_acceptors, Proposer_anyof_ret_pc, Proposer_anyof_s, Proposer_majority, Proposer_n, Proposer_run_ret_pc, Proposer_to_consent_ret_pc, Proposer_yield_ret_pc >>


==============================================================
