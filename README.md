# When talking with an LLM, think about the order in which you present information, and where to put the prompt!
### TL;DR  
**On this variable resolution challenge, placing prompts before input data boosted GPT-4o-mini's accuracy by 25-100% in variable resolution tasks compared to placing them afterwards.**  
- Input ordering (**normal/reverse/random**) significantly impacts performance.

It is well-known that it is important to optimize _what_ to put into an LLM's input, and not to overload it. But maybe the _arrangement_ of the information is underrated.
This is a simple eval of LLM ability to follow and resolve references, made to understand the impact of rearranging the information and prompt placement on the LLM's abilities.

Hoping to understand how to make LLMs work better with large codebases.

## Task description
A sample input to the LLM (before changing the line ordering and prompt arrangement) looks like this:
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
Note that "Output only the result" prevents explicit chain-of-thought reasoning, which intentionally hobbles the LLM's abilities so we can see how well it does without. See the [Reproduction](#reproduction) section for variants currently supported by the evaluation script.

In normal mode, variable definitions reference earlier entries. For example, in lines 6-10, variables reference definitions from lines 1-5 in random order; in lines 11-15, they reference definitions from lines 6-10, and so on --- to resolve the final variable, the LLM needs to follow 3 resolution steps. In inverse/random mode, the lines were reversed/randomized. I also evaluated putting the query before or after the prompt, or both. 

## Results: Success Rates by Mode and Prompt Placement relative to input data
| Mode | Prompt after input | Prompt before input | Prompt before and after input |
|------|------------------|-------------------|------------------------|
| Normal | 46 % | 84 % | 94 % |
| Inverse | 39 % | 47 % | 48 % |
| Random | 49 % | 80 % | 69 % |
| **Average** | 45 % | 70 % | 70 % |
| **Commit** | [161381278fc4](https://github.com/L3Gaunt/llm_tracing_test/commit/161381278fc4a9438e5c479d83fc863e21702ece) | [cff30ae0778](https://github.com/L3Gaunt/llm_tracing_test/commit/cff30ae07783647e84319fc616d12424b1b05629) | [fea7ca67a9d](https://github.com/L3Gaunt/llm_tracing_test/commit/fea7ca67a9d55a7f6ceae550fdf0f605dc6d5453) |

(100 attempts per mode and placement, gpt-4o-mini. For some of the entries, 1/100 queries resulted in an API timeout)


The clear result is that putting the prompt before the input data is better than asking it afterwards, though note that the experiment by Lars Wiik [here][wiik-exp] found the opposite for a needle-in-a-haystack benchmark and much longer contexs (see Section [Related](#related) for details). Another result is that the order in which parts of the input (individual definitions) are presented does matter for performance.
The explanation that makes sense to me is that without chains of thought, LLMs have a hard time reading backwards: If they get the prompt first, they can spend all the input processing thinking about how to answer the specific prompt the user is having. If they get it last, they have to guess and keep track of many more things at once.

In contrast to the result I got, I was expecting to see random mode perform worse than inverse mode as well (at least when the prompt is put before the input), as for the latter, there is a strategy to keep track of the first reference whenever we see a new token. The advantage of random mode (from the LLM's perspective) may be that there is a chance that the needed reference resolution chain comes in an early part of the query -- making the task easier in those cases -- while in normal+inverse mode, it is guaranteed that the chain spans the entire input.

# Preliminary conclusion
As in the title: Think about and experiment with where you put your prompts! And about the order in which you present your input code files and similar.

# Related
1. [An experiment regarding instruction placement][wiik-exp] by [Lars Wiik][wiik-gh], for a needle-in-a-haystack problem. This found that putting the prompt after the input is better for long inputs (for Gemini 1.5 Pro), and is worse for not-so-long inputs (like we find in this repo) - but either we are not in that regime yet, or 4o-mini is different than Gemini 1.5 Pro in that regard. It found that the prompt is worse for not-so-long inputs as well. This inspired me to try putting the query before and after the input as well - but I didn't see a statistically significant improvement so far (maybe because the input here is a lot shorter than in Lars' experiments).

[wiik-exp]: https://archive.is/cLoNp
[wiik-gh]: https://github.com/LarsChrWiik

2. The [RULER](https://github.com/NVIDIA/RULER) benchmark is a needle-in-a-haystack like test with more complex tasks, including reference following, though it doesn't seem to explicitly consider ordering.

### Reproduction
1. Clone the [repository](https://github.com/L3Gaunt/llm_tracing_test),
2. `git checkout` the mentioned commits
3. Run `pip3 install -r requirements.txt`
4. Add OPENROUTER_KEY key to `.env` (example.env in the commits mentioned here mistakenly asks for an OPENAI_API_KEY)
5. Run: `python3 evaluate.py --num-symbols 5 --num-vars 20 --initializations-per-symbol 1 --question-padding "" --num-per-mode 100 --verbose > results.md`. This sets
- 5 different words for direct definitions
- 20 lines/variable definitions in total, including direct definitions
- for each word, 1 variable that is directly defined as that word (>1 would reuse words and randomize the order)
- no padding after the input (I wanted to see whether empty "thinking tokens" would improve the result)
- 100 tries per mode (normal/inverse/random). The summary statistics come from `tail -n results.md`

Code is messy/research-grade. Eval result files are not always up-to-date with code in the commit! Only trust in that for files mentioned here. Look for the diffs if you _really_ want to know whether the results.md of a commit is stale.

Raw data from the individual commits:
```
161381278fc4a9438e5c479d83fc863e21702ece: the prompt is put after the input
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

fea7ca67a9d55a7f6ceae550fdf0f605dc6d5453: the prompt is put before and after the input
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

cff30ae07783647e84319fc616d12424b1b05629: the prompt is put before the input.
.venvname@name llm_tracing_test % tail -n 10 results.md

===== EVALUATION RESULTS =====
Parameters: num_symbols=5, num_vars=20, initializations_per_symbol=1, 100 evaluations per mode

Success Rates:
  normal: 84/100 (84.0%) | Errors: 0 (0.0%) | Incorrect: 16 (16.0%)
  inverse: 47/100 (47.0%) | Errors: 0 (0.0%) | Incorrect: 53 (53.0%)
  random: 80/100 (80.0%) | Errors: 0 (0.0%) | Incorrect: 20 (20.0%)

Overall: 211/300 (70.3%) | Errors: 0 (0.0%) | Incorrect: 89 (29.7%)
```
