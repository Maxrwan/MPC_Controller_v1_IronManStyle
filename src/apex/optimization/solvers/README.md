# Solver adapters

ipopt.py implements the Task 006 CasADi/IPOPT adapter. Construct once from MPCProblem,
then solve numeric NLPRequest instances through the existing Solver protocol. SolverResult
contains success/status/solution/statistics; the neutral base imports neither CasADi nor
IPOPT. Monotonic wall timing encloses the backend call. Failure never supplies an accepted
solution. Options and feasibility policy are documented in docs/NMPC_BASELINE_SPEC.md.

Other solver backends remain unimplemented. Do not scatter backend calls through controller,
plant or simulation code, or interpret solver wall duration as zero physical time by default.
