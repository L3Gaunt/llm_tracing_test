# When talking with an LLM, think about the order in which you present information, and where to put the prompt.

This is a simple eval of LLM ability to follow and resolve references, made to understand the impact of rearranging the information and prompt placement on the LLM's abilities.

Hoping to understand how to make LLMs work better with large codebases.

## Task description
A sample input to the LLM looks like this:
```
V_584 = Zephyr
V_650 = Velvet
V_722 = Waffle
V_527 = Serpent
V_653 = Alloy
V_610 = V_650
V_316 = V_722
V_191 = V_584
V_359 = V_527
V_923 = V_653
V_647 = V_316
V_632 = V_191
V_288 = V_359
V_103 = V_610
V_859 = V_923
V_679 = V_647
V_861 = V_632
V_684 = V_859
V_571 = V_103
V_890 = V_288

Output only the result: What is the value of V_890?
```
note that "Output only the result" prevents explicit chain-of-thought reasoning, which intentionally hobbles the LLM's abilities so we can see how well it does without. See the "Reproduction" section for variants currently supported by the evaluation script.

In this "normal mode", variable definitions only reference variables defined earlier (to be precise, definitions in lines `[5i, 5i+4]` reference something at random from lines `[5i-5, 5i-1]`, so the LLM needs to follow 3 resolution steps). In inverse/random mode, the lines were reversed/randomized. I also evaluated putting the query before or after the question, or both. 


## Results: Success Rates by Mode and Question Placement relative to input data
| Mode | After input only | Before input only | Before and after input |
|------|------------------|-------------------|------------------------|
| Normal | 46 % | 84 % | 94 % |
| Inverse | 39 % | 47 % | 48 % |
| Random | 49 % | 80 % | 69 % |
| **Average** | 45 % | 70 % | 70 % |
| **Commit** | [161381278fc4](https://github.com/L3Gaunt/llm_tracing_test/commit/161381278fc4a9438e5c479d83fc863e21702ece) | [cff30ae0778](https://github.com/L3Gaunt/llm_tracing_test/commit/cff30ae07783647e84319fc616d12424b1b05629) | [fea7ca67a9d](https://github.com/L3Gaunt/llm_tracing_test/commit/fea7ca67a9d55a7f6ceae550fdf0f605dc6d5453) |

(100 attempts per mode and placement, gpt-4o-mini. For some of the entries, 1/100 queries resulted in an API timeout)


The clear result is that asking the question before the input data is better than asking it afterwards, though note that [^1] found the opposite for a needle-in-a-haystack problem and much longer inputs. Another result is that the order in which information is presented does matter for performance.
The explanation that makes sense to me is that without chains of thought, LLMs have a hard time reading backwards: If they get the prompt first, they can spend all the input processing thinking about how to answer the specific question the user is having. If they get it last, they have to guess and keep track of many more things at once.

In contrast to the result I got, I was expecting to see random mode perform worse than inverse mode as well (at least when the question is asked before the input), as for the latter, there is a strategy to keep track of the first reference whenever we see a new token. The advantage of random mode (from the LLM's perspective) may be that there is a chance that the needed reference resolution chain comes in an early part of the query -- making the task easier in those cases -- while in normal+reverse mode, it is guaranteed that the chain spans the entire input.

# Preliminary conclusion
Think about and experiment with where you put your prompts! And about the order in which you present your context code files and similar.

# See also
[^1]
[Here](https://archive.is/cLoNp), [Lars Wijk](https://github.com/LarsChrWiik) actually found that putting the prompt after the input is better for long inputs - but we are not in that regime yet. Inspired by that, I tried to put the query before and after the input as well - but didn't see an across-the-board improvement so far (maybe because the input here is a lot shorter than in Lars' experiments).

[^2]
See also the [RULER](https://github.com/NVIDIA/RULER) benchmark - a more complex needle-in-a-haystack test with more complex tasks, including reference following, but doesn't seem to focus on ordering.

# Reproduction
To reproduce the given commit results log, populate a .env file with an OPENROUTER_KEY (example.env in the commits mentioned here mistakenly asks for an OPENAI_API_KEY) and run `python3 evaluate.py --num-symbols 5 --num-vars 20 --initializations-per-symbol 1 --question-padding "" --num-per-mode 100 --verbose > results.md`. This sets
- 5 different words for direct definitions
- 20 lines/variable definitions in total, including direct definitions
- for each word, 1 variable that is directly defined as that word (>1 would reuse words and randomize the order)
- no padding after the input/question (I wanted to see whether empty "thinking tokens" would improve the result)
- 100 tries per mode (normal/inverse/random). The summary statistics come from `tail -n results.md`

Code is messy/research-grade. Eval result files are not always up-to-date with code in the commit! Only trust in that for files mentioned here. Look for the diffs if you _really_ want to know whether the results.md of a commit is stale.

Raw data from the individual commits:
```
161381278fc4a9438e5c479d83fc863e21702ece: the question is asked after the input
.venvname@name llm_tracing_test % 
Progress: 100.0% | Running: 0 | Success: 299 | Issues: 1
All evaluations completed!
Issues: 1 timeouts, 0 API errors

===== EVALUATION RESULTS =====
Parameters: num_symbols=5, num_vars=20, initializations_per_symbol=1, 100 evaluations per mode

Success Rates:
  normal: 46/100 (46.0%) | Errors: 1 (1.0%) | Incorrect: 53 (53.0%)
  inverse: 39/100 (39.0%) | Errors: 0 (0.0%) | Incorrect: 61 (61.0%)
  random: 49/100 (49.0%) | Errors: 0 (0.0%) | Incorrect: 51 (51.0%)

Overall: 134/300 (44.7%) | Errors: 1 (0.3%) | Incorrect: 165 (55.0%)

Error Examples:

Error 1: Task timed out after 10.0 seconds
Mode: normal, num_symbols=5, num_vars=20, initializations_per_symbol=1

fea7ca67a9d55a7f6ceae550fdf0f605dc6d5453: the question is asked before and after the input
.venvname@name llm_tracing_test % tail -n 18 results.md                                
Progress: 100.0% | Running: 0 | Success: 299 | Issues: 1
All evaluations completed!
Issues: 0 timeouts, 1 API errors

===== EVALUATION RESULTS =====
Parameters: num_symbols=5, num_vars=20, initializations_per_symbol=1, 100 evaluations per mode

Success Rates:
  normal: 94/100 (94.0%) | Errors: 0 (0.0%) | Incorrect: 6 (6.0%)
  inverse: 48/100 (48.0%) | Errors: 1 (1.0%) | Incorrect: 51 (51.0%)
  random: 69/100 (69.0%) | Errors: 0 (0.0%) | Incorrect: 31 (31.0%)

Overall: 211/300 (70.3%) | Errors: 1 (0.3%) | Incorrect: 88 (29.3%)

Error Examples:

Error 1: Expecting value: line 1 column 1 (char 0)
Mode: inverse, num_symbols=5, num_vars=20, initializations_per_symbol=1

cff30ae07783647e84319fc616d12424b1b05629: the question is asked before the input.
.venvname@name llm_tracing_test % tail -n 10 results.md

===== EVALUATION RESULTS =====
Parameters: num_symbols=5, num_vars=20, initializations_per_symbol=1, 100 evaluations per mode

Success Rates:
  normal: 84/100 (84.0%) | Errors: 0 (0.0%) | Incorrect: 16 (16.0%)
  inverse: 47/100 (47.0%) | Errors: 0 (0.0%) | Incorrect: 53 (53.0%)
  random: 80/100 (80.0%) | Errors: 0 (0.0%) | Incorrect: 20 (20.0%)

Overall: 211/300 (70.3%) | Errors: 0 (0.0%) | Incorrect: 89 (29.7%)
```