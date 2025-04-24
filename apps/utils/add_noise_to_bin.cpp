#include <iostream>
#include <fstream>
#include <vector>
#include <random>
#include <cmath>
#include <cstring>

void read_bin_header(std::ifstream &infile, uint32_t &npts, uint32_t &ndims) {
    infile.read((char *)&npts, sizeof(uint32_t));
    infile.read((char *)&ndims, sizeof(uint32_t));
}

void write_bin_header(std::ofstream &outfile, uint32_t npts, uint32_t ndims) {
    outfile.write((char *)&npts, sizeof(uint32_t));
    outfile.write((char *)&ndims, sizeof(uint32_t));
}

void normalize_vector(std::vector<float> &vec) {
    float norm = 0.0f;
    for (float x : vec) norm += x * x;
    norm = std::sqrt(norm);
    if (norm > 0.0f) {
        for (float &x : vec) x /= norm;
    }
}

int add_noise_to_bin(const std::string &input_file, const std::string &output_file, float noise_scale, bool normalize) {
    std::ifstream infile(input_file, std::ios::binary);
    if (!infile) {
        std::cerr << "Failed to open input file." << std::endl;
        return -1;
    }

    uint32_t npts, ndims;
    read_bin_header(infile, npts, ndims);

    std::ofstream outfile(output_file, std::ios::binary);
    if (!outfile) {
        std::cerr << "Failed to open output file." << std::endl;
        return -1;
    }

    write_bin_header(outfile, npts, ndims);

    std::vector<float> vec(ndims);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);

    for (size_t i = 0; i < npts; ++i) {
        infile.read((char *)vec.data(), ndims * sizeof(float));

        for (size_t d = 0; d < ndims; ++d) {
            vec[d] += noise_scale * dist(gen);
        }

        if (normalize) {
            normalize_vector(vec);
        }

        outfile.write((char *)vec.data(), ndims * sizeof(float));
    }

    infile.close();
    outfile.close();
    std::cout << "Finished writing noisy data to " << output_file << std::endl;
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <input_file> <output_file> <noise_scale> <normalize:0|1>" << std::endl;
        return -1;
    }

    std::string input_file = argv[1];
    std::string output_file = argv[2];
    float noise_scale = std::stof(argv[3]);
    bool normalize = std::stoi(argv[4]) != 0;

    return add_noise_to_bin(input_file, output_file, noise_scale, normalize);
}
