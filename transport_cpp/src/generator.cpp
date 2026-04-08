#include "generator.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <numeric>
#include <random>
#include <stdexcept>

namespace transport {

namespace {

std::mt19937& rng() {
    static thread_local std::mt19937 gen(std::random_device{}());
    return gen;
}

int randInt(int lo, int hi) {
    std::uniform_int_distribution<int> dist(lo, hi);
    return dist(rng());
}

}  // namespace

TransportProblem generateBalancedProblem(int n, int m, int minValue, int maxValue) {
    TransportProblem p(n, m);

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            p.costs[i][j] = randInt(minValue, maxValue);
        }
    }

    std::vector<std::vector<int>> temp(n, std::vector<int>(m, 0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            temp[i][j] = randInt(minValue, maxValue);
        }
    }

    for (int i = 0; i < n; ++i) {
        p.supplies[i] = std::accumulate(temp[i].begin(), temp[i].end(), 0);
    }

    for (int j = 0; j < m; ++j) {
        int sumCol = 0;
        for (int i = 0; i < n; ++i) {
            sumCol += temp[i][j];
        }
        p.demands[j] = sumCol;
    }

    return p;
}

TransportProblem generateSquareStudyProblem(int n, int minValue, int maxValue) {
    return generateBalancedProblem(n, n, minValue, maxValue);
}

void writeProblemFile(const TransportProblem& p, const std::string& filePath) {
    auto parent = std::filesystem::path(filePath).parent_path();
    if (!parent.empty()) {
        std::filesystem::create_directories(parent);
    }

    std::ofstream out(filePath);
    if (!out) {
        throw std::runtime_error("Impossible d'ouvrir le fichier en ecriture: " + filePath);
    }

    out << p.n << " " << p.m << "\n";
    for (int i = 0; i < p.n; ++i) {
        for (int j = 0; j < p.m; ++j) {
            out << p.costs[i][j] << " ";
        }
        out << p.supplies[i] << "\n";
    }

    for (int j = 0; j < p.m; ++j) {
        out << p.demands[j];
        if (j + 1 < p.m) {
            out << " ";
        }
    }
    out << "\n";
}

}  // namespace transport
