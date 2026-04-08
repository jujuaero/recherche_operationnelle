#pragma once

#include <cstdint>
#include <optional>
#include <ostream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace transport {

struct Cell {
    int i;
    int j;

    bool operator==(const Cell& other) const noexcept {
        return i == other.i && j == other.j;
    }

    bool operator!=(const Cell& other) const noexcept {
        return !(*this == other);
    }
};

struct CellHash {
    std::size_t operator()(const Cell& c) const noexcept;
};

struct SolveResult {
    int iterations = 0;
    bool hitMaxIterations = false;
};

class TransportProblem {
public:
    int n = 0;
    int m = 0;
    std::vector<std::vector<int>> costs;
    std::vector<int> supplies;
    std::vector<int> demands;
    std::vector<std::vector<int>> transport;
    std::unordered_set<Cell, CellHash> basis;

    TransportProblem() = default;
    TransportProblem(int rows, int cols);

    static TransportProblem loadFromFile(const std::string& path);

    std::int64_t totalCost() const;
    bool validate(std::string* errorMessage = nullptr) const;

    void northWest();
    void balasHammer();
    SolveResult steppingStonePotentials(
        const std::string& initialMethod = "north_west",
        int maxIterations = 1000,
        bool initializationDone = false
    );
    SolveResult steppingStoneWithTrace(
        std::ostream& trace,
        const std::string& initialMethod = "north_west",
        int maxIterations = 1000,
        bool initializationDone = false
    );

private:
    std::pair<std::vector<int>, std::vector<int>> computePotentials() const;
    std::unordered_map<Cell, int, CellHash> computeMarginals(
        const std::vector<int>& u,
        const std::vector<int>& v
    ) const;
    std::vector<Cell> findCycle(const Cell& entering) const;
    std::vector<Cell> findAnyBasisCycle() const;
    int countBasisComponents() const;
    std::vector<Cell> addCheapestConnectingEdges(
        const std::optional<Cell>& protectedEdge,
        const std::unordered_set<Cell, CellHash>& excludedEdges
    );
    void enforceAcyclicThenConnected(
        const std::optional<Cell>& protectedEdge,
        std::vector<Cell>* addedForConnectivity,
        const std::unordered_set<Cell, CellHash>& excludedEdges
    );
};

}  // namespace transport
