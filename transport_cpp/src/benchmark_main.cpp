#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>

#include "generator.hpp"
#include "transport_problem.hpp"

using transport::TransportProblem;

struct Row {
    int testId;
    int n;
    int m;
    std::string algorithm;
    std::string initialization;
    double timeMs;
    long long totalCost;
    int basisSize;
    int valid;
};

int main(int argc, char** argv) {
    int repetitions = 100;
    if (argc >= 2) {
        repetitions = std::stoi(argv[1]);
    }

    std::vector<std::pair<int, int>> configs = {
        {5, 5}, {5, 10}, {10, 5}, {10, 10}, {15, 15}, {20, 20}
    };

    std::filesystem::create_directories("results/benchmark");
    std::ofstream out("results/benchmark/resultats_benchmark_cpp.csv");
    out << "test_id,n,m,algorithme,initialisation,temps_ms,cout_total,base_size,validations_ok\n";

    int testId = 0;
    for (const auto& cfg : configs) {
        int n = cfg.first;
        int m = cfg.second;

        std::cout << "Configuration " << n << "x" << m << " ...\n";
        for (int rep = 0; rep < repetitions; ++rep) {
            auto p = transport::generateBalancedProblem(n, m);

            auto run = [&](const std::string& algo, const std::string& init) {
                TransportProblem work = p;
                auto t0 = std::chrono::high_resolution_clock::now();

                if (algo == "north_west") {
                    work.northWest();
                } else if (algo == "balas_hammer") {
                    work.balasHammer();
                } else if (algo == "stepping_stone") {
                    if (init == "balas_hammer") {
                        work.balasHammer();
                    } else {
                        work.northWest();
                    }
                    work.steppingStonePotentials(init, std::max(1000, n * m * 20), true);
                }

                auto t1 = std::chrono::high_resolution_clock::now();
                double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
                std::string err;
                bool ok = work.validate(&err);

                out << testId++ << ","
                    << n << ","
                    << m << ","
                    << algo << ","
                    << init << ","
                    << std::fixed << std::setprecision(6) << ms << ","
                    << work.totalCost() << ","
                    << work.basis.size() << ","
                    << (ok ? 1 : 0) << "\n";
            };

            run("north_west", "");
            run("balas_hammer", "");
            run("stepping_stone", "north_west");
            run("stepping_stone", "balas_hammer");

            if ((rep + 1) % 10 == 0) {
                std::cout << "  progression " << (rep + 1) << "/" << repetitions << "\n";
            }
        }
    }

    std::cout << "Resultats sauvegardes: results/benchmark/resultats_benchmark_cpp.csv\n";
    return 0;
}
