(.venv) name@name llm_tracing_test % python3 evaluate.py --n 50 --m 3 --trackback-depth 3 --num-per-order 30 
Running 90 evaluations (30 each for normal, reversed, randomized)...
Progress: 100.0% | Running: 0 | Success: 89 | Issues: 1                                          
All evaluations completed!
Issues: 1 timeouts, 0 API errors

===== EVALUATION RESULTS =====
Parameters: N=50, M=3, trackback_depth=3, 30 evaluations per order type

Success Rates:
  normal: 8/30 (26.7%) | Errors: 0 (0.0%) | Incorrect: 22 (73.3%)
  reversed: 14/30 (46.7%) | Errors: 1 (3.3%) | Incorrect: 15 (50.0%)
  randomized: 5/30 (16.7%) | Errors: 0 (0.0%) | Incorrect: 25 (83.3%)

Overall: 27/90 (30.0%) | Errors: 1 (1.1%) | Incorrect: 62 (68.9%)

Error Examples:

Error 1: Task timed out after 10.0 seconds
Order: reversed, N=50, M=3