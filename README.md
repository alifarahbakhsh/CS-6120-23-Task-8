# CS-6120-23-Task-8
This repo contains the code for loop-invariant code motion. The experiments cover the benchmarks from the `core` and `float` folders in the canonical Bril repository.
The experiments are conducted via `brench`. Note that you should probably change the benchmark directory in the `.toml` files.
The measured metric is the number of `dyn_inst`s, which is automatically collected by `brench`.

I did not cover the `long` and `mem` benchmarks because they either take a long time and thus output `timeout`, or throw memory management errors because
I have not considered pointer instructions in my code.
Note that some of the core and float benchmarks also result in a `timeout`, but I have manually checked them and the results are correct.

I have reported the statistics of the relative and absolute improvements for the two experiments, where improvement is equal to `(before - after) / before`.
For core the mean relative and absolute improvements are `0.02` and `1457`, with standard deviations of `0.03` and `6797`, respectively.
For float the mean relative and absolute improvements are `0.01` and `390`, with standard deviations of `0.01` and `1016`, respectively.

An interesting point was seeing a degradation of performance for one of the `mem` benchmarks, even though the output was correct. I did not investigate the reason due to a lack of time.
