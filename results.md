.venvname@name llm_tracing_test % python3 evaluate.py --num-symbols 10 --initializations-per-symbol 1 --num-vars 50 --question-padding "" --num-per-mode 10                  
Running 30 evaluations (10 each for normal, inverse, random)...
Progress: [============] 100.0% | Submitted: 30/30 | Running: 0 | Evaluated: 30                  
All evaluations completed!

===== EVALUATION RESULTS =====
Parameters: num_symbols=10, num_vars=50, initializations_per_symbol=1, 10 evaluations per mode

Success Rates:
  normal: 2/10 (20.0%) | Errors: 0 (0.0%) | Incorrect: 8 (80.0%)
  inverse: 4/10 (40.0%) | Errors: 0 (0.0%) | Incorrect: 6 (60.0%)
  random: 3/10 (30.0%) | Errors: 0 (0.0%) | Incorrect: 7 (70.0%)

Overall: 9/30 (30.0%) | Errors: 0 (0.0%) | Incorrect: 21 (70.0%)