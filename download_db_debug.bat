@echo off

:: Check for --release flag
set "BUILD_TYPE=Debug"
for %%A in (%*) do (
    if "%%A"=="--release" set "BUILD_TYPE=Release"
)

:: Set PATH based on BUILD_TYPE
SET PATH=%PATH%;%cd%\x64\%BUILD_TYPE%;
echo Using build type: %BUILD_TYPE%

:: Ensure data directory exists
if not exist data (
    mkdir data
    echo Created "data" directory.
) else (
    echo "data" directory already exists.
)

cd data

:: Download sift.tar.gz if it doesn't already exist
if not exist sift.tar.gz (
    echo Downloading sift.tar.gz...
    curl -o sift.tar.gz ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz
) else (
    echo sift.tar.gz already exists, skipping download.
)

:: Extract sift.tar.gz if not already extracted
if not exist sift\ (
    echo Extracting sift.tar.gz...
    tar -xf sift.tar.gz
) else (
    echo sift directory already exists, skipping extraction.
)

cd ..

:: Convert fvecs to bin only if the output files don't already exist
if not exist data/sift/sift_learn.fbin (
    echo Converting sift_learn.fvecs to sift_learn.fbin...
    fvecs_to_bin float data/sift/sift_learn.fvecs data/sift/sift_learn.fbin
) else (
    echo sift_learn.fbin already exists, skipping conversion.
)

if not exist data/sift/sift_query.fbin (
    echo Converting sift_query.fvecs to sift_query.fbin...
    fvecs_to_bin float data/sift/sift_query.fvecs data/sift/sift_query.fbin
) else (
    echo sift_query.fbin already exists, skipping conversion.
)

:: Compute groundtruth if the output file doesn't already exist
if not exist data/sift/sift_query_learn_gt100 (
    echo Computing groundtruth...
    compute_groundtruth --data_type float --dist_fn l2 --base_file data/sift/sift_learn.fbin --query_file data/sift/sift_query.fbin --gt_file data/sift/sift_query_learn_gt100 --K 100
) else (
    echo sift_query_learn_gt100 already exists, skipping groundtruth computation.
)

:: Uncomment the following lines to build or search memory index
:: Ensure the relevant files are created if not already present
if not exist data/sift/index_sift_learn_R32_L50_A1.2 (
    build_memory_index --data_type float --dist_fn l2 --data_path data/sift/sift_learn.fbin --index_path_prefix data/sift/index_sift_learn_R32_L50_A1.2 -R 32 -L 50 --alpha 1.2
) else (
    echo index_sift_learn_R32_L50_A1.2 already exists, skipping index build.
)

:: Uncomment to run search memory index
:: search_memory_index --data_type float --dist_fn l2 --index_path_prefix data/sift/index_sift_learn_R32_L50_A1.2 --query_file data/sift/sift_query.fbin --gt_file data/sift/sift_query_learn_gt100 -K 10 -L 10 20 30 40 50 100 --result_path data/sift/res
