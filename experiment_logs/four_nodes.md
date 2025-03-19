# Experiment summary

The "four-nodes" or "N-nodes" method adds N closest nodes as additional edges for every node within the index.

The intuition is to enable a more granular exploration once you've reached the target cluster close to the query vector, for which the Vamana index reaches pretty fast.

# Commands used

The only tweaked value is R (max edge budget per node) from below command. As for the fixed parameters;
- L: 50
- alpha: 1.2

### Index construction

You may remove `gdb --args` as you see fit.

```
gdb --args ./apps/build_memory_index --num_threads 1 --data_type float --dist_fn l2 --data_path /home/kylekim/workspace_back/DiskANN_back/build/data/sift/sift_learn.fbin --index_path_prefix /home/kylekim/file/index/index_sift_learn_R44_L50_A1.2 -R 44 -L 50 --alpha 1.2
```

### Search index

```
./apps/search_memory_index  --data_type float --dist_fn l2 --index_path_prefix /home/kylekim/file/index/index_sift_learn_R36_L50_A1.2 --query_file /home/kylekim/workspace_back/DiskANN_back/build/data/sift/sift_query.fbin --gt_file /home/kylekim/workspace_back/DiskANN_back/build/data/sift/sift_query_gt_l2_100 -K 10 -L 10 20 30 40 50 100 --result_path data/sift/res
```

# Benchmark

The result of `search_memory_index` between 1) four-nodes index vs 2) regular index is detailed further below.

## Four-nodes index, R=32

R = 32 is used. However, the max edges observed is 36 (= 32 + 4), as we unconditionally insert four closest nodes based on the pre-generated ground truth dataset, for every node within the index.

```
Index built with degree: max:36  avg:30.1213  min:7  count(deg<2):0

From graph header, expected_file_size: 12448564, _max_observed_degree: 36, _start: 29429, file_frozen_pts: 0
Loading vamana graph /home/kylekim/file/index/index_sift_learn_R32_L50_A1.2_four_nodes...done. Index has 100000 nodes and 3012135 out-edges, _start is set to 29429
Num frozen points:0 _nd: 100000 _start: 29429 size(_location_to_tag): 0 size(_tag_to_location):0 Max points: 100000
Index loaded
Using 28 threads to search
  Ls         QPS     Avg dist cmps  Mean Latency (mus)   99.9 Latency   Recall@10
=================================================================================
  10    42064.49            386.37              649.27        4753.98       96.81
  20    30870.69            575.17              875.57        8438.70       98.53
  30    23523.33            749.02             1166.29       10151.06       99.11
  40    19913.73            911.28             1379.11        7362.67       99.41
  50    16610.45           1065.05             1665.63       21319.21       99.58
 100     9564.71           1744.45             2892.98       31397.25       99.87
```

## Regular index, R=44

R = 44 is used, such that the average edges per node matches to that of four-nodes variant above.

```
Index built with degree: max:44  avg:30.2499  min:3  count(deg<2):0

From graph header, expected_file_size: 12499976, _max_observed_degree: 44, _start: 29429, file_frozen_pts: 0
Loading vamana graph /home/kylekim/file/index/index_sift_learn_R44_L50_A1.2...done. Index has 100000 nodes and 3024988 out-edges, _start is set to 29429
Num frozen points:0 _nd: 100000 _start: 29429 size(_location_to_tag): 0 size(_tag_to_location):0 Max points: 100000
Index loaded
Using 28 threads to search
  Ls         QPS     Avg dist cmps  Mean Latency (mus)   99.9 Latency   Recall@10
=================================================================================
  10    45186.75            407.03              604.76        4613.30       95.81
  20    33205.48            607.48              827.62        4869.21       98.08
  30    25598.80            790.33             1080.98        5193.05       98.87
  40    20925.16            961.03             1325.13        7390.58       99.27
  50    17784.44           1122.14             1563.08        7539.28       99.46
 100    10299.79           1828.22             2699.81        7663.51       99.85
```

## Regular index, R=64

R = 64 is used, to showcase that doubling the max edge budget still doesn't quite reach the same recall (for lower L values; 10 ~ 30) to that of the four-nodes counterpart.

```
Index built with degree: max:64  avg:34.0557  min:3  count(deg<2):0

From graph header, expected_file_size: 14022296, _max_observed_degree: 64, _start: 29429, file_frozen_pts: 0
Loading vamana graph /home/kylekim/file/index/index_sift_learn_R64_L50_A1.2...done. Index has 100000 nodes and 3405568 out-edges, _start is set to 29429
Num frozen points:0 _nd: 100000 _start: 29429 size(_location_to_tag): 0 size(_tag_to_location):0 Max points: 100000
Index loaded
Using 28 threads to search
  Ls         QPS     Avg dist cmps  Mean Latency (mus)   99.9 Latency   Recall@10
=================================================================================
  10    36260.67            479.31              721.42       10374.57       96.27
  20    27384.54            707.20              987.35       15968.08       98.38
  30    21345.79            913.34             1297.14       11373.59       99.06
  40    17197.80           1105.14             1597.77       19537.65       99.41
  50    15553.99           1285.26             1780.74       11748.87       99.56
 100     9270.17           2068.51             3001.40       10105.67       99.89
```
