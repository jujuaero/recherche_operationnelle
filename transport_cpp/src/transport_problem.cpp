#include "transport_problem.hpp"

#include <algorithm>
#include <array>
#include <deque>
#include <fstream>
#include <functional>
#include <iomanip>
#include <limits>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>

namespace transport {

std::size_t CellHash::operator()(const Cell& c) const noexcept {
    const std::size_t h1 = static_cast<std::size_t>(c.i);
    const std::size_t h2 = static_cast<std::size_t>(c.j);
    return h1 * 1315423911u ^ (h2 + 0x9e3779b9 + (h1 << 6) + (h1 >> 2));
}

TransportProblem::TransportProblem(int rows, int cols)
    : n(rows), m(cols),
      costs(rows, std::vector<int>(cols, 0)),
      supplies(rows, 0),
      demands(cols, 0),
      transport(rows, std::vector<int>(cols, 0)) {}

TransportProblem TransportProblem::loadFromFile(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Impossible d'ouvrir le fichier: " + path);
    }

    int rows = 0;
    int cols = 0;
    in >> rows >> cols;
    if (!in || rows <= 0 || cols <= 0) {
        throw std::runtime_error("Entete invalide dans le fichier: " + path);
    }

    TransportProblem p(rows, cols);
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            in >> p.costs[i][j];
        }
        in >> p.supplies[i];
    }

    for (int j = 0; j < cols; ++j) {
        in >> p.demands[j];
    }

    const int sumSupply = std::accumulate(p.supplies.begin(), p.supplies.end(), 0);
    const int sumDemand = std::accumulate(p.demands.begin(), p.demands.end(), 0);
    if (sumSupply != sumDemand) {
        throw std::runtime_error("Probleme non equilibre: sum(supplies) != sum(demands)");
    }

    return p;
}

std::int64_t TransportProblem::totalCost() const {
    std::int64_t total = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            total += static_cast<std::int64_t>(costs[i][j]) * transport[i][j];
        }
    }
    return total;
}

bool TransportProblem::validate(std::string* errorMessage) const {
    auto fail = [&](const std::string& msg) {
        if (errorMessage != nullptr) {
            *errorMessage = msg;
        }
        return false;
    };

    const int expectedBasisSize = n + m - 1;
    if (static_cast<int>(basis.size()) != expectedBasisSize) {
        return fail("Taille de base invalide");
    }

    for (int i = 0; i < n; ++i) {
        int sumRow = 0;
        for (int j = 0; j < m; ++j) {
            if (transport[i][j] < 0) {
                return fail("Valeur de transport negative");
            }
            sumRow += transport[i][j];
        }
        if (sumRow != supplies[i]) {
            return fail("Contrainte de provision non respectee");
        }
    }

    for (int j = 0; j < m; ++j) {
        int sumCol = 0;
        for (int i = 0; i < n; ++i) {
            sumCol += transport[i][j];
        }
        if (sumCol != demands[j]) {
            return fail("Contrainte de commande non respectee");
        }
    }

    return true;
}

void TransportProblem::northWest() {
    transport.assign(n, std::vector<int>(m, 0));
    basis.clear();

    std::vector<int> s = supplies;
    std::vector<int> d = demands;

    int i = 0;
    int j = 0;

    while (i < n && j < m) {
        const int q = std::min(s[i], d[j]);
        transport[i][j] = q;
        basis.insert({i, j});

        s[i] -= q;
        d[j] -= q;

        if (s[i] == 0 && d[j] == 0) {
            if (i + 1 < n) {
                basis.insert({i + 1, j});
            } else if (j + 1 < m) {
                basis.insert({i, j + 1});
            }
            ++i;
            ++j;
        } else if (s[i] == 0) {
            ++i;
        } else {
            ++j;
        }
    }

    if (static_cast<int>(basis.size()) > n + m - 1) {
        std::vector<Cell> vec(basis.begin(), basis.end());
        std::sort(vec.begin(), vec.end(), [](const Cell& a, const Cell& b) {
            return (a.i < b.i) || (a.i == b.i && a.j < b.j);
        });
        basis.clear();
        for (int k = 0; k < n + m - 1; ++k) {
            basis.insert(vec[k]);
        }
    }
}

void TransportProblem::balasHammer() {
    transport.assign(n, std::vector<int>(m, 0));
    basis.clear();

    std::vector<int> s = supplies;
    std::vector<int> d = demands;
    std::vector<bool> activeRow(n, true);
    std::vector<bool> activeCol(m, true);

    auto penaltyRow = [&](int i) {
        std::vector<int> vals;
        vals.reserve(m);
        for (int j = 0; j < m; ++j) {
            if (activeCol[j]) {
                vals.push_back(costs[i][j]);
            }
        }
        if (vals.empty()) {
            return -1;
        }
        std::sort(vals.begin(), vals.end());
        if (vals.size() == 1) {
            return vals[0];
        }
        return vals[1] - vals[0];
    };

    auto penaltyCol = [&](int j) {
        std::vector<int> vals;
        vals.reserve(n);
        for (int i = 0; i < n; ++i) {
            if (activeRow[i]) {
                vals.push_back(costs[i][j]);
            }
        }
        if (vals.empty()) {
            return -1;
        }
        std::sort(vals.begin(), vals.end());
        if (vals.size() == 1) {
            return vals[0];
        }
        return vals[1] - vals[0];
    };

    auto bestColOfRow = [&](int i) {
        int bestJ = -1;
        int bestCost = std::numeric_limits<int>::max();
        for (int j = 0; j < m; ++j) {
            if (activeCol[j] && costs[i][j] < bestCost) {
                bestCost = costs[i][j];
                bestJ = j;
            }
        }
        return bestJ;
    };

    auto bestRowOfCol = [&](int j) {
        int bestI = -1;
        int bestCost = std::numeric_limits<int>::max();
        for (int i = 0; i < n; ++i) {
            if (activeRow[i] && costs[i][j] < bestCost) {
                bestCost = costs[i][j];
                bestI = i;
            }
        }
        return bestI;
    };

    while (true) {
        int activeRows = 0;
        int activeCols = 0;
        for (bool b : activeRow) {
            activeRows += b ? 1 : 0;
        }
        for (bool b : activeCol) {
            activeCols += b ? 1 : 0;
        }
        if (activeRows == 0 || activeCols == 0) {
            break;
        }

        struct Candidate {
            bool isRow;
            int idx;
            int penalty;
            int pairIdx;
            int minCost;
            int possibleQ;
        };

        std::vector<Candidate> cands;
        cands.reserve(activeRows + activeCols);

        for (int i = 0; i < n; ++i) {
            if (!activeRow[i]) {
                continue;
            }
            const int j = bestColOfRow(i);
            const int p = penaltyRow(i);
            const int minC = costs[i][j];
            const int q = std::min(s[i], d[j]);
            cands.push_back({true, i, p, j, minC, q});
        }

        for (int j = 0; j < m; ++j) {
            if (!activeCol[j]) {
                continue;
            }
            const int i = bestRowOfCol(j);
            const int p = penaltyCol(j);
            const int minC = costs[i][j];
            const int q = std::min(s[i], d[j]);
            cands.push_back({false, j, p, i, minC, q});
        }

        auto best = *std::max_element(
            cands.begin(), cands.end(),
            [](const Candidate& a, const Candidate& b) {
                const auto ka = std::array<int, 3>{a.penalty, -a.minCost, a.possibleQ};
                const auto kb = std::array<int, 3>{b.penalty, -b.minCost, b.possibleQ};
                return ka < kb;
            }
        );

        int i = 0;
        int j = 0;
        if (best.isRow) {
            i = best.idx;
            j = best.pairIdx;
        } else {
            i = best.pairIdx;
            j = best.idx;
        }

        const int q = std::min(s[i], d[j]);
        transport[i][j] += q;
        basis.insert({i, j});
        s[i] -= q;
        d[j] -= q;

        const bool rowDone = (s[i] == 0);
        const bool colDone = (d[j] == 0);

        if (rowDone && colDone) {
            activeRow[i] = false;
            activeCol[j] = false;

            int iAlt = -1;
            for (int r = 0; r < n; ++r) {
                if (activeRow[r]) {
                    iAlt = r;
                    break;
                }
            }
            int jAlt = -1;
            for (int c = 0; c < m; ++c) {
                if (activeCol[c]) {
                    jAlt = c;
                    break;
                }
            }

            if (iAlt >= 0) {
                basis.insert({iAlt, j});
            } else if (jAlt >= 0) {
                basis.insert({i, jAlt});
            }
        } else if (rowDone) {
            activeRow[i] = false;
        } else if (colDone) {
            activeCol[j] = false;
        }
    }

    if (static_cast<int>(basis.size()) > n + m - 1) {
        std::vector<Cell> vec(basis.begin(), basis.end());
        std::sort(vec.begin(), vec.end(), [](const Cell& a, const Cell& b) {
            return (a.i < b.i) || (a.i == b.i && a.j < b.j);
        });
        basis.clear();
        for (int k = 0; k < n + m - 1; ++k) {
            basis.insert(vec[k]);
        }
    }
}

std::pair<std::vector<int>, std::vector<int>> TransportProblem::computePotentials() const {
    std::vector<int> u(n, std::numeric_limits<int>::max());
    std::vector<int> v(m, std::numeric_limits<int>::max());
    if (n > 0) {
        u[0] = 0;
    }

    std::vector<Cell> baseList(basis.begin(), basis.end());
    bool changed = true;
    while (changed) {
        changed = false;
        for (const Cell& c : baseList) {
            if (u[c.i] != std::numeric_limits<int>::max() && v[c.j] == std::numeric_limits<int>::max()) {
                v[c.j] = costs[c.i][c.j] - u[c.i];
                changed = true;
            } else if (v[c.j] != std::numeric_limits<int>::max() && u[c.i] == std::numeric_limits<int>::max()) {
                u[c.i] = costs[c.i][c.j] - v[c.j];
                changed = true;
            }
        }

        if (!changed) {
            bool missing = false;
            for (int val : u) {
                if (val == std::numeric_limits<int>::max()) {
                    missing = true;
                    break;
                }
            }
            if (!missing) {
                for (int val : v) {
                    if (val == std::numeric_limits<int>::max()) {
                        missing = true;
                        break;
                    }
                }
            }

            if (missing) {
                for (int i = 0; i < n; ++i) {
                    if (u[i] == std::numeric_limits<int>::max()) {
                        u[i] = 0;
                        changed = true;
                        break;
                    }
                }
            }
        }
    }

    for (int& x : u) {
        if (x == std::numeric_limits<int>::max()) {
            x = 0;
        }
    }
    for (int& x : v) {
        if (x == std::numeric_limits<int>::max()) {
            x = 0;
        }
    }

    return {u, v};
}

std::unordered_map<Cell, int, CellHash> TransportProblem::computeMarginals(
    const std::vector<int>& u,
    const std::vector<int>& v
) const {
    std::unordered_map<Cell, int, CellHash> marginals;
    marginals.reserve(static_cast<std::size_t>(n) * static_cast<std::size_t>(m));

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            Cell c{i, j};
            if (basis.find(c) == basis.end()) {
                marginals[c] = costs[i][j] - (u[i] + v[j]);
            }
        }
    }
    return marginals;
}

std::vector<Cell> TransportProblem::findCycle(const Cell& entering) const {
    std::vector<Cell> nodes;
    nodes.reserve(basis.size() + 1);
    for (const Cell& c : basis) {
        nodes.push_back(c);
    }
    nodes.push_back(entering);

    std::unordered_map<int, std::vector<Cell>> byRow;
    std::unordered_map<int, std::vector<Cell>> byCol;

    for (const Cell& c : nodes) {
        byRow[c.i].push_back(c);
        byCol[c.j].push_back(c);
    }

    enum class Move { Row, Col };

    std::vector<Cell> path;
    path.push_back(entering);

    std::unordered_set<Cell, CellHash> visited;

    std::function<std::optional<std::vector<Cell>>(const Cell&, Move)> dfs;
    dfs = [&](const Cell& cur, Move move) -> std::optional<std::vector<Cell>> {
        const auto& neigh = (move == Move::Row) ? byRow[cur.i] : byCol[cur.j];
        for (const Cell& nxt : neigh) {
            if (nxt == cur) {
                continue;
            }

            if (nxt == entering && path.size() >= 4) {
                auto out = path;
                out.push_back(entering);
                return out;
            }

            if (nxt == entering) {
                continue;
            }

            if (visited.find(nxt) != visited.end()) {
                continue;
            }

            if (basis.find(nxt) == basis.end()) {
                continue;
            }

            visited.insert(nxt);
            path.push_back(nxt);
            auto res = dfs(nxt, move == Move::Row ? Move::Col : Move::Row);
            if (res.has_value()) {
                return res;
            }
            path.pop_back();
            visited.erase(nxt);
        }
        return std::nullopt;
    };

    if (auto res = dfs(entering, Move::Row); res.has_value()) {
        return *res;
    }
    if (auto res = dfs(entering, Move::Col); res.has_value()) {
        return *res;
    }

    return {};
}

std::vector<Cell> TransportProblem::findAnyBasisCycle() const {
    for (const Cell& c : basis) {
        auto cycle = findCycle(c);
        if (!cycle.empty()) {
            return cycle;
        }
    }
    return {};
}

int TransportProblem::countBasisComponents() const {
    const int nodes = n + m;
    if (nodes == 0) {
        return 0;
    }

    std::vector<std::vector<int>> adj(nodes);
    for (const Cell& c : basis) {
        int u = c.i;
        int v = n + c.j;
        adj[u].push_back(v);
        adj[v].push_back(u);
    }

    std::vector<char> visited(nodes, 0);
    int components = 0;
    for (int s = 0; s < nodes; ++s) {
        if (visited[s]) {
            continue;
        }
        ++components;
        std::deque<int> q;
        q.push_back(s);
        visited[s] = 1;
        while (!q.empty()) {
            int cur = q.front();
            q.pop_front();
            for (int nxt : adj[cur]) {
                if (!visited[nxt]) {
                    visited[nxt] = 1;
                    q.push_back(nxt);
                }
            }
        }
    }
    return components;
}

std::vector<Cell> TransportProblem::addCheapestConnectingEdges(
    const std::optional<Cell>& protectedEdge,
    const std::unordered_set<Cell, CellHash>& excludedEdges
) {
    std::vector<Cell> added;

    while (countBasisComponents() > 1) {
        struct DSU {
            std::vector<int> p;
            explicit DSU(int n) : p(n) {
                std::iota(p.begin(), p.end(), 0);
            }
            int find(int x) {
                if (p[x] == x) {
                    return x;
                }
                p[x] = find(p[x]);
                return p[x];
            }
            bool unite(int a, int b) {
                a = find(a);
                b = find(b);
                if (a == b) {
                    return false;
                }
                p[b] = a;
                return true;
            }
        };

        DSU dsu(n + m);
        for (const Cell& e : basis) {
            dsu.unite(e.i, n + e.j);
        }

        bool found = false;
        Cell best{-1, -1};
        int bestCost = std::numeric_limits<int>::max();

        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < m; ++j) {
                Cell c{i, j};
                if (basis.find(c) != basis.end()) {
                    continue;
                }
                if (excludedEdges.find(c) != excludedEdges.end()) {
                    continue;
                }
                if (protectedEdge.has_value() && c == *protectedEdge) {
                    continue;
                }

                int a = dsu.find(i);
                int b = dsu.find(n + j);
                if (a == b) {
                    continue;
                }

                if (costs[i][j] < bestCost) {
                    bestCost = costs[i][j];
                    best = c;
                    found = true;
                }
            }
        }

        if (!found) {
            break;
        }

        basis.insert(best);
        added.push_back(best);
    }

    return added;
}

void TransportProblem::enforceAcyclicThenConnected(
    const std::optional<Cell>& protectedEdge,
    std::vector<Cell>* addedForConnectivity,
    const std::unordered_set<Cell, CellHash>& excludedEdges
) {
    // 1) Supprimer les cycles de manière répétée jusqu'à acyclicité.
    for (int guard = 0; guard < n + m + 32; ++guard) {
        auto cycle = findAnyBasisCycle();
        if (cycle.empty()) {
            break;
        }

        std::vector<Cell> minusCells;
        minusCells.reserve(cycle.size() / 2);
        for (std::size_t k = 1; k + 1 < cycle.size(); k += 2) {
            minusCells.push_back(cycle[k]);
        }

        int theta = std::numeric_limits<int>::max();
        for (const Cell& c : minusCells) {
            theta = std::min(theta, transport[c.i][c.j]);
        }

        if (theta > 0 && theta < std::numeric_limits<int>::max()) {
            for (std::size_t k = 0; k + 1 < cycle.size(); ++k) {
                const Cell& c = cycle[k];
                if ((k % 2) == 0) {
                    transport[c.i][c.j] += theta;
                } else {
                    transport[c.i][c.j] -= theta;
                }
            }

            bool removed = false;
            for (const Cell& c : minusCells) {
                if (transport[c.i][c.j] == 0) {
                    if (protectedEdge.has_value() && c == *protectedEdge) {
                        continue;
                    }
                    basis.erase(c);
                    removed = true;
                    break;
                }
            }

            if (!removed) {
                for (const Cell& c : minusCells) {
                    if (!(protectedEdge.has_value() && c == *protectedEdge)) {
                        basis.erase(c);
                        removed = true;
                        break;
                    }
                }
            }

            if (!removed) {
                for (std::size_t k = 1; k + 1 < cycle.size(); k += 2) {
                    const Cell& c = cycle[k];
                    basis.erase(c);
                    break;
                }
            }
        } else {
            // delta=0: casser explicitement le cycle en retirant une arête non protégée.
            bool removed = false;
            for (std::size_t k = 1; k + 1 < cycle.size(); k += 2) {
                const Cell& c = cycle[k];
                if (protectedEdge.has_value() && c == *protectedEdge) {
                    continue;
                }
                basis.erase(c);
                removed = true;
                break;
            }
            if (!removed) {
                for (std::size_t k = 0; k + 1 < cycle.size(); ++k) {
                    const Cell& c = cycle[k];
                    if (protectedEdge.has_value() && c == *protectedEdge) {
                        continue;
                    }
                    basis.erase(c);
                    removed = true;
                    break;
                }
            }
            if (!removed) {
                throw std::runtime_error("Impossible de casser un cycle sans retirer l'arete protegee.");
            }
        }
    }

    // 2) Une fois acyclique, compléter pour rendre connexe avec coûts croissants.
    auto added = addCheapestConnectingEdges(protectedEdge, excludedEdges);
    if (addedForConnectivity != nullptr) {
        *addedForConnectivity = added;
    }
}

SolveResult TransportProblem::steppingStonePotentials(
    const std::string& initialMethod,
    int maxIterations,
    bool initializationDone
) {
    std::ostringstream sink;
    return steppingStoneWithTrace(sink, initialMethod, maxIterations, initializationDone);
}

SolveResult TransportProblem::steppingStoneWithTrace(
    std::ostream& trace,
    const std::string& initialMethod,
    int maxIterations,
    bool initializationDone
) {
    if (!initializationDone) {
        if (initialMethod == "north_west") {
            northWest();
        } else if (initialMethod == "balas_hammer") {
            balasHammer();
        } else {
            throw std::runtime_error("Initialisation inconnue: " + initialMethod);
        }
    } else if (basis.empty()) {
        throw std::runtime_error("Initialisation deja faite, mais base vide.");
    }

    SolveResult result;
    std::vector<Cell> lastConnectivityAdded;
    std::unordered_set<Cell, CellHash> excludedConnectivityEdges;

    auto printTransportTable = [&]() {
        trace << "\nMatrice transport\n";
        trace << std::setw(8) << "F/C";
        for (int j = 0; j < m; ++j) {
            trace << std::setw(8) << ("C" + std::to_string(j));
        }
        trace << std::setw(10) << "Provision" << "\n";

        for (int i = 0; i < n; ++i) {
            trace << std::setw(8) << ("F" + std::to_string(i));
            for (int j = 0; j < m; ++j) {
                trace << std::setw(8) << transport[i][j];
            }
            trace << std::setw(10) << supplies[i] << "\n";
        }

        trace << std::setw(8) << "Demandes";
        for (int j = 0; j < m; ++j) {
            trace << std::setw(8) << demands[j];
        }
        trace << "\n";
    };

    auto printPotentialsTable = [&](const std::vector<int>& u, const std::vector<int>& v) {
        trace << "\nPotentiels u(i) / v(j)\n";
        for (int i = 0; i < n; ++i) {
            trace << "u(" << i << ")=" << u[i] << (i + 1 < n ? ", " : "\n");
        }
        for (int j = 0; j < m; ++j) {
            trace << "v(" << j << ")=" << v[j] << (j + 1 < m ? ", " : "\n");
        }
    };

    auto printMarginalsTable = [&](const std::unordered_map<Cell, int, CellHash>& marginals) {
        trace << "\nTable des couts marginaux (hors base)\n";
        trace << std::setw(8) << "F/C";
        for (int j = 0; j < m; ++j) {
            trace << std::setw(8) << ("C" + std::to_string(j));
        }
        trace << "\n";

        for (int i = 0; i < n; ++i) {
            trace << std::setw(8) << ("F" + std::to_string(i));
            for (int j = 0; j < m; ++j) {
                Cell c{i, j};
                if (basis.find(c) != basis.end()) {
                    trace << std::setw(8) << "BASE";
                } else {
                    auto it = marginals.find(c);
                    if (it != marginals.end()) {
                        trace << std::setw(8) << it->second;
                    } else {
                        trace << std::setw(8) << "-";
                    }
                }
            }
            trace << "\n";
        }
    };

    trace << "MARCHE-PIED + POTENTIELS\n";
    trace << "Initialisation: " << initialMethod << "\n";

    for (int iter = 1; iter <= maxIterations; ++iter) {
        trace << "\n============================================================\n";
        trace << "Iteration " << iter << "\n";
        printTransportTable();
        trace << "Cout courant: " << totalCost() << "\n";
        trace << "Taille base: " << basis.size() << " (attendu: " << (n + m - 1) << ")\n";

        auto cycleBefore = findAnyBasisCycle();
        trace << "Test cycle (BFS/structure): " << (cycleBefore.empty() ? "acyclique" : "cycle detecte") << "\n";
        if (!cycleBefore.empty()) {
            trace << "Cycle detecte: ";
            for (std::size_t k = 0; k < cycleBefore.size(); ++k) {
                trace << "(" << cycleBefore[k].i << "," << cycleBefore[k].j << ")";
                if (k + 1 < cycleBefore.size()) {
                    trace << " -> ";
                }
            }
            trace << "\n";
        }

        const int componentsBefore = countBasisComponents();
        trace << "Test connexite (BFS/structure): composantes=" << componentsBefore << "\n";

        auto [u, v] = computePotentials();
        auto marginals = computeMarginals(u, v);
        printPotentialsTable(u, v);
        printMarginalsTable(marginals);

        bool hasNegative = false;
        Cell entering{-1, -1};
        int bestDelta = std::numeric_limits<int>::max();

        for (const auto& kv : marginals) {
            if (kv.second < 0 && kv.second < bestDelta) {
                hasNegative = true;
                entering = kv.first;
                bestDelta = kv.second;
            }
        }

        result.iterations = iter;
        if (!hasNegative) {
            result.hitMaxIterations = false;
            trace << "Aucune arete ameliorante detectee: solution optimale.\n";
            return result;
        }

        trace << "Arete ameliorante choisie: (" << entering.i << "," << entering.j << ") delta=" << bestDelta << "\n";

        const auto cycle = findCycle(entering);
        if (cycle.empty()) {
            throw std::runtime_error("Cycle introuvable pour cellule entrante.");
        }

        trace << "Cycle pour maximisation: ";
        for (std::size_t k = 0; k < cycle.size(); ++k) {
            trace << "(" << cycle[k].i << "," << cycle[k].j << ")";
            if (k + 1 < cycle.size()) {
                trace << " -> ";
            }
        }
        trace << "\n";

        std::vector<Cell> minusCells;
        for (std::size_t k = 1; k + 1 < cycle.size(); k += 2) {
            minusCells.push_back(cycle[k]);
        }

        int theta = std::numeric_limits<int>::max();
        for (const Cell& c : minusCells) {
            theta = std::min(theta, transport[c.i][c.j]);
        }
        trace << "Theta (maximisation sur cycle): " << theta << "\n";

        basis.insert(entering);

        if (theta > 0 && theta < std::numeric_limits<int>::max()) {
            for (std::size_t k = 0; k + 1 < cycle.size(); ++k) {
                const Cell& c = cycle[k];
                if ((k % 2) == 0) {
                    transport[c.i][c.j] += theta;
                } else {
                    transport[c.i][c.j] -= theta;
                }
            }

            for (const Cell& c : minusCells) {
                if (transport[c.i][c.j] == 0) {
                    basis.erase(c);
                    trace << "Arete supprimee apres maximisation: (" << c.i << "," << c.j << ")\n";
                    break;
                }
            }

            excludedConnectivityEdges.clear();
        } else {
            // Cas delta=0: conserver l'arête améliorante et retirer les arêtes
            // ajoutées lors du dernier test de connexité pour forcer un autre choix.
            for (const Cell& e : lastConnectivityAdded) {
                if (e == entering) {
                    continue;
                }
                basis.erase(e);
                excludedConnectivityEdges.insert(e);
                trace << "Delta=0: retrait arete ajoutee lors de la derniere connexite: ("
                      << e.i << "," << e.j << ")\n";
            }
            lastConnectivityAdded.clear();
        }

        enforceAcyclicThenConnected(entering, &lastConnectivityAdded, excludedConnectivityEdges);
        if (!lastConnectivityAdded.empty()) {
            trace << "Aretes ajoutees pour connexite: ";
            for (std::size_t k = 0; k < lastConnectivityAdded.size(); ++k) {
                const auto& c = lastConnectivityAdded[k];
                trace << "(" << c.i << "," << c.j << ")";
                if (k + 1 < lastConnectivityAdded.size()) {
                    trace << ", ";
                }
            }
            trace << "\n";
        }

        trace << "Etat post-reparation: cycle=" << (findAnyBasisCycle().empty() ? "non" : "oui")
              << ", composantes=" << countBasisComponents() << "\n";
    }

    result.hitMaxIterations = true;
    trace << "Arret: max_iterations atteint (" << maxIterations << ").\n";
    return result;
}

}  // namespace transport
