# Development checks (before frozen stochastic audit)

The first focused test invocation returned 25 PASS / 2 FAIL. The two failures
were the newly written iid quadratic variance assertion: it incorrectly used
(T+1)/(2T^2). Independent normal sample mean and sample variance give
[1+(T-1)]/(2T^2)=1/(2T). The quadratic-form implementation already returned
the correct values (.5 for T=1, .015625 for T=32); only this incorrect test
expectation and its derivation comment were corrected. No historical code or
results changed. The final focused/full test receipts are stored separately.

The initial independent A proposal also mixed half squared training loss with
full squared terminal loss. The new protocol uses half loss consistently and
preserves the original proposal plus an append-only reviewer clarification.
