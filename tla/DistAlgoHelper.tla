----------------------------- MODULE DistAlgoHelper -------------------
EXTENDS Integers, Sequences, FiniteSets, TLC

Min(a, b) == IF a < b THEN a ELSE b

a \prec b == LET MinLength == Min(Len(a), Len(b)) IN
                \/ /\ SubSeq(a, 1, MinLength) = SubSeq(b, 1, MinLength)
                   /\ Len(a) < Len(b)
                \/ \E n \in 1..MinLength:
                        /\ a[n] < b[n]
                        /\ \A m \in 1..n-1 : a[m] = b[m]

a \succ b == LET MinLength == Min(Len(a), Len(b)) IN
                \/ /\ SubSeq(a, 1, MinLength) = SubSeq(b, 1, MinLength)
                   /\ Len(a) > Len(b)
                \/ \E n \in 1..MinLength:
                        /\ a[n] > b[n]
                        /\ \A m \in 1..n-1 : a[m] = b[m]

SetOr(S) ==
    S[CHOOSE n \in 1..Len(S): /\ \A m \in 1..n-1: Cardinality(S[m]) = 0
                              /\ (Cardinality(S[n]) > 0 \/ n = Len(S))]

SetAnd(S) ==
    S[CHOOSE n \in 1..Len(S): /\ \A m \in 1..n-1: Cardinality(S[m]) > 0
                              /\ (Cardinality(S[n]) = 0 \/ n = Len(S))]

Max(S) == CHOOSE n \in S: (\A m \in S: n >= m)
MaxTuple(S) == CHOOSE n \in S: (\A m \in S: n \succ m \/ n = m)

==============================================================
