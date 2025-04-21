#include <iostream>
#include <fstream>
#include <vector>
#include <random>
#include <cstring>
#include <algorithm>
#include "utils.h"

void read_bin_header(std::ifstream &in, uint32_t &npts, uint32_t &ndims) {
    in.read((char *)&npts, sizeof(uint32_t));
    in.read((char *)&ndims, sizeof(uint32_t));
}

template <typename T>
void split_bin(const std::string &input_file, const std::string &out1, const std::string &out2, float percentage) {
    std::ifstream fin(input_file, std::ios::binary);
    if (!fin) {
        std::cerr << "Failed to open " << input_file << std::endl;
        return;
    }

    uint32_t npts, ndims;
    read_bin_header(fin, npts, ndims);
    size_t vec_size = ndims * sizeof(T);

    std::vector<std::vector<T>> data(npts, std::vector<T>(ndims));
    for (uint32_t i = 0; i < npts; ++i) {
        fin.read((char *)data[i].data(), vec_size);
    }

    // Shuffle and split
    std::vector<uint32_t> indices(npts);
    std::iota(indices.begin(), indices.end(), 0);
    std::random_device rd;
    std::mt19937 g(rd());
    std::shuffle(indices.begin(), indices.end(), g);

    size_t split_idx = static_cast<size_t>((percentage / 100.0f) * npts);
    std::vector<uint32_t> part1(indices.begin(), indices.begin() + split_idx);
    std::vector<uint32_t> part2(indices.begin() + split_idx, indices.end());

    // Helper to write a bin file
    auto write_bin = [&](const std::string &filename, const std::vector<uint32_t> &ids) {
        std::ofstream fout(filename, std::ios::binary);
        uint32_t count = static_cast<uint32_t>(ids.size());
        fout.write((char *)&count, sizeof(uint32_t));
        fout.write((char *)&ndims, sizeof(uint32_t));
        for (uint32_t i : ids) {
            fout.write((char *)data[i].data(), vec_size);
        }
        fout.close();
    };

    write_bin(out1, part1);
    write_bin(out2, part2);

    std::cout << "Wrote " << part1.size() << " vectors to " << out1 << std::endl;
    std::cout << "Wrote " << part2.size() << " vectors to " << out2 << std::endl;
}

int main(int argc, char **argv) {
    if (argc != 6) {
        std::cout << "Usage: " << argv[0] << " <float/int8/uint8> <input_bin> <output1> <output2> <percentage>\n";
        return 1;
    }

    std::string dtype = argv[1];
    std::string input = argv[2];
    std::string out1 = argv[3];
    std::string out2 = argv[4];
    float pct = std::stof(argv[5]);

    if (pct < 0.0f || pct > 100.0f) {
        std::cerr << "Invalid percentage. Must be between 0 and 100.\n";
        return 1;
    }

    if (dtype == "float") {
        split_bin<float>(input, out1, out2, pct);
    } else if (dtype == "int8" || dtype == "uint8") {
        split_bin<uint8_t>(input, out1, out2, pct);
    } else {
        std::cerr << "Unsupported type. Use float/int8/uint8\n";
        return 1;
    }

    return 0;
}
