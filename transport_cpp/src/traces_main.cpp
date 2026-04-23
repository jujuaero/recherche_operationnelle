#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include "transport_problem.hpp"

using transport::TransportProblem;

int main(int argc, char** argv) {
    try {
        int groupId = 2;
        int teamId = 4;
        std::string outputDir = "results/traces";

        if (argc >= 2) {
            groupId = std::stoi(argv[1]);
        }
        if (argc >= 3) {
            teamId = std::stoi(argv[2]);
        }
        if (argc >= 4) {
            outputDir = argv[3];
        }

        std::filesystem::create_directories(outputDir);

        for (int problemId = 1; problemId <= 12; ++problemId) {
            std::string inputPath = "../data/input/transport" + std::to_string(problemId) + ".txt";
            if (!std::filesystem::exists(inputPath)) {
                // fallback when launched from workspace root
                inputPath = "data/input/transport" + std::to_string(problemId) + ".txt";
            }

            TransportProblem original = TransportProblem::loadFromFile(inputPath);

            for (const auto& init : {std::string("north_west"), std::string("balas_hammer")}) {
                TransportProblem p = original;
                std::string initTag = (init == "north_west") ? "no" : "bh";
                std::string outName = std::to_string(groupId) + "-" + std::to_string(teamId)
                    + "-trace" + std::to_string(problemId) + "-" + initTag + ".txt";
                std::filesystem::path outPath = std::filesystem::path(outputDir) / outName;

                std::ofstream trace(outPath.string());
                if (!trace) {
                    throw std::runtime_error("Impossible d'ecrire le fichier de trace: " + outPath.string());
                }

                trace << "Groupe " << groupId << " - Equipe " << teamId << " - Probleme " << problemId
                      << " - Init " << init << "\n";
                trace << "Fichier source: " << inputPath << "\n";
                trace << "Dimensions: " << p.n << "x" << p.m << "\n\n";

                if (init == "north_west") {
                    p.northWest();
                } else {
                    p.balasHammer();
                }

                trace << "Cout initial: " << p.totalCost() << "\n";
                auto result = p.steppingStoneWithTrace(trace, init, 10000, true);

                trace << "\n============================================================\n";
                trace << "RESULTAT FINAL\n";
                trace << "Cout final: " << p.totalCost() << "\n";
                trace << "Iterations: " << result.iterations << "\n";
                trace << "Hit max iterations: " << (result.hitMaxIterations ? "oui" : "non") << "\n";
                std::string err;
                bool ok = p.validate(&err);
                trace << "Validation: " << (ok ? "OK" : ("ECHEC - " + err)) << "\n";

                std::cout << "Trace generee: " << outPath.string() << "\n";
            }
        }

        std::cout << "\nToutes les traces ont ete generees dans: " << outputDir << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Erreur: " << e.what() << "\n";
        return 1;
    }
}
