# Simple evaluation of tracing ability of LLMs
- We generate a simple test of LLM's ability 
#(.venv) name@name llm_tracing_test % python3 evaluate.py
Running 300 evaluations (100 each for normal, reversed, randomized)...
Progress: 300/300 evaluations completed
All evaluations completed!

===== EVALUATION RESULTS =====
Parameters: N=50, M=2, 100 evaluations per order type

Success Rates:
  Normal: 88/100 (88.0%) | Errors: 0 (0.0%) | Incorrect: 12 (12.0%)
  Reversed: 87/100 (87.0%) | Errors: 0 (0.0%) | Incorrect: 13 (13.0%)
  Randomized: 54/100 (54.0%) | Errors: 0 (0.0%) | Incorrect: 46 (46.0%)

Overall: 229/300 (76.3%) | Errors: 0 (0.0%) | Incorrect: 71 (23.7%)

# This was after adding 4k whitespaces to the prompt
(.venv) name@name llm_tracing_test % python3 evaluate.py
Running 300 evaluations (100 each for normal, reversed, randomized)...
Progress: 300/300 evaluations completed
All evaluations completed!

===== EVALUATION RESULTS =====
Parameters: N=50, M=2, 100 evaluations per order type

Success Rates:
  Normal: 90/100 (90.0%) | Errors: 0 (0.0%) | Incorrect: 10 (10.0%)
  Reversed: 87/100 (87.0%) | Errors: 0 (0.0%) | Incorrect: 13 (13.0%)
  Randomized: 54/100 (54.0%) | Errors: 0 (0.0%) | Incorrect: 46 (46.0%)

Overall: 231/300 (77.0%) | Errors: 0 (0.0%) | Incorrect: 69 (23.0%)