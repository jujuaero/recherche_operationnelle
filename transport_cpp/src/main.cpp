#include <iostream>
#include <string>

#include "../include/generator.hpp"
#include "../include/transport_problem.hpp"

using transport::TransportProblem;

namespace {

void printSummary(const TransportProblem& p, const std::string& algo) {
    std::cout << "Algorithme: " << algo << "\n";
    std::cout << "Cout total: " << p.totalCost() << "\n";
    std::cout << "Base size: " << p.basis.size() << " (attendu: " << (p.n + p.m - 1) << ")\n";
    std::string err;
    const bool ok = p.validate(&err);
    std::cout << "Validation: " << (ok ? "OK" : ("ECHEC - " + err)) << "\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            std::cout << "Usage:\n";
            std::cout << "  transport_cli file <chemin_fichier>\n";
            std::cout << "  transport_cli random <n> <m>\n";
            return 0;
        }

        TransportProblem p;
        std::string mode = argv[1];

        if (mode == "file") {
            if (argc < 3) {
                throw std::runtime_error("Mode file: chemin manquant");
            }
            p = TransportProblem::loadFromFile(argv[2]);
        } else if (mode == "random") {
            if (argc < 4) {
                throw std::runtime_error("Mode random: n et m manquants");
            }
            int n = std::stoi(argv[2]);
            int m = std::stoi(argv[3]);
            p = transport::generateBalancedProblem(n, m);
        } else {
            throw std::runtime_error("Mode inconnu: " + mode);
        }

        std::cout << "Probleme charge: " << p.n << "x" << p.m << "\n\n";

        auto p1 = p;
        p1.northWest();
        printSummary(p1, "north_west");
        std::cout << "\n";

        auto p2 = p;
        p2.balasHammer();
        printSummary(p2, "balas_hammer");
        std::cout << "\n";

        auto p3 = p;
        p3.northWest();
        auto r3 = p3.steppingStonePotentials("north_west", 5000, true);
        printSummary(p3, "stepping_stone(init=north_west)");
        std::cout << "Iterations: " << r3.iterations << ", hitMax=" << (r3.hitMaxIterations ? "yes" : "no") << "\n\n";

        auto p4 = p;
        p4.balasHammer();
        auto r4 = p4.steppingStonePotentials("balas_hammer", 5000, true);
        printSummary(p4, "stepping_stone(init=balas_hammer)");
        std::cout << "Iterations: " << r4.iterations << ", hitMax=" << (r4.hitMaxIterations ? "yes" : "no") << "\n";

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Erreur: " << e.what() << "\n";
        return 1;
    }
}
