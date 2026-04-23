#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>

#include "generator.hpp"
#include "transport_problem.hpp"

using transport::TransportProblem;

static double cpuSeconds() {
    return static_cast<double>(std::clock()) / static_cast<double>(CLOCKS_PER_SEC);
}

int main(int argc, char** argv) {
    int repetitions = 100;
    int nMax = 10000;
    if (argc >= 2) {
        repetitions = std::stoi(argv[1]);
    }
    if (argc >= 3) {
        nMax = std::stoi(argv[2]);
    }

    const std::vector<int> nValues = {10, 40, 100, 400, 1000, 4000, 10000};

    std::filesystem::create_directories("results/etude10");
    std::ofstream out("results/etude10/resultats_etude10_cpp.csv");
    out << "n,repetition,theta_NO_s,theta_BH_s,t_NO_s,t_BH_s,theta_plus_t_NO_s,theta_plus_t_BH_s\n";

    for (int n : nValues) {
        if (n > nMax) {
            continue;
        }
        std::cout << "\n--- n=" << n << " ---\n";

        for (int rep = 1; rep <= repetitions; ++rep) {
            TransportProblem base = transport::generateSquareStudyProblem(n);

            TransportProblem p = base;
            double t0 = cpuSeconds();
            p.northWest();
            double thetaNO = cpuSeconds() - t0;

            p = base;
            t0 = cpuSeconds();
            p.balasHammer();
            double thetaBH = cpuSeconds() - t0;

            p = base;
            p.northWest();
            t0 = cpuSeconds();
            p.steppingStonePotentials("north_west", 5000, true);
            double tNO = cpuSeconds() - t0;

            p = base;
            p.balasHammer();
            t0 = cpuSeconds();
            p.steppingStonePotentials("balas_hammer", 5000, true);
            double tBH = cpuSeconds() - t0;

            out << n << ","
                << rep << ","
                << std::fixed << std::setprecision(8)
                << thetaNO << ","
                << thetaBH << ","
                << tNO << ","
                << tBH << ","
                << (thetaNO + tNO) << ","
                << (thetaBH + tBH) << "\n";

            if (rep % 10 == 0) {
                std::cout << "  progression " << rep << "/" << repetitions << "\n";
            }
        }
    }

    std::cout << "\nResultats sauvegardes: results/etude10/resultats_etude10_cpp.csv\n";
    return 0;
}
