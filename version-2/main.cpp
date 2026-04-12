#include <iostream>
#include <vector>
#include <fstream>
#include <iomanip>
#include <string>
#include <algorithm>
#include <queue>
#include <limits>
#include <chrono>
#include <ctime>

using namespace std;

const double INF = numeric_limits<double>::infinity();

struct Problem
{
    int n, m;
    vector<vector<double>> costs;
    vector<double> provisions;
    vector<double> commands;
};

Problem readProblem(const string &filename)
{
    ifstream file(filename);
    Problem p;
    if (!file.is_open())
    {
        return p;
    }
    file >> p.n >> p.m;
    p.costs.resize(p.n, vector<double>(p.m));
    p.provisions.resize(p.n);
    p.commands.resize(p.m);
    for (int i = 0; i < p.n; ++i)
    {
        for (int j = 0; j < p.m; ++j)
            file >> p.costs[i][j];
        file >> p.provisions[i];
    }
    for (int j = 0; j < p.m; ++j)
        file >> p.commands[j];
    return p;
}

void displayTable(const string &title, const vector<vector<double>> &table, const vector<double> &rowLabels, const vector<double> &colLabels)
{
    cout << "\n--- " << title << " ---\n";
    cout << setw(10) << " ";
    for (int j = 0; j < colLabels.size(); ++j)
        cout << setw(10) << "C" + to_string(j + 1);
    cout << setw(10) << "Prov." << endl;
    for (int i = 0; i < table.size(); ++i)
    {
        cout << setw(10) << "P" + to_string(i + 1);
        for (int j = 0; j < table[i].size(); ++j)
        {
            if (table[i][j] == INF)
                cout << setw(10) << "X";
            else
                cout << setw(10) << table[i][j];
        }
        cout << setw(10) << rowLabels[i] << endl;
    }
}

vector<vector<double>> northwestCorner(const Problem &p)
{
    vector<vector<double>> flow(p.n, vector<double>(p.m, 0));
    vector<double> prov = p.provisions;
    vector<double> cmd = p.commands;
    int i = 0, j = 0;
    while (i < p.n && j < p.m)
    {
        double quantity = min(prov[i], cmd[j]);
        flow[i][j] = quantity;
        prov[i] -= quantity;
        cmd[j] -= quantity;
        if (prov[i] == 0)
            i++;
        else
            j++;
    }
    return flow;
}

vector<vector<double>> balasHammer(const Problem &p)
{
    vector<vector<double>> flow(p.n, vector<double>(p.m, 0));
    vector<double> prov = p.provisions;
    vector<double> cmd = p.commands;
    vector<bool> rowDone(p.n, false), colDone(p.m, false);
    for (int k = 0; k < p.n + p.m - 1; ++k)
    {
        int bestI = -1;
        double maxPenalty = -1;
        for (int i = 0; i < p.n; ++i)
        {
            if (rowDone[i])
                continue;
            vector<double> active;
            for (int j = 0; j < p.m; ++j)
                if (!colDone[j])
                    active.push_back(p.costs[i][j]);
            if (active.empty())
                continue;
            sort(active.begin(), active.end());
            double penalty = (active.size() > 1) ? active[1] - active[0] : active[0];
            if (penalty > maxPenalty)
            {
                maxPenalty = penalty;
                bestI = i;
            }
        }
        if (bestI != -1)
        {
            int targetJ = -1;
            double minC = INF;
            for (int j = 0; j < p.m; ++j)
                if (!colDone[j] && p.costs[bestI][j] < minC)
                {
                    minC = p.costs[bestI][j];
                    targetJ = j;
                }
            if (targetJ != -1)
            {
                double q = min(prov[bestI], cmd[targetJ]);
                flow[bestI][targetJ] = q;
                prov[bestI] -= q;
                cmd[targetJ] -= q;
                if (prov[bestI] == 0)
                    rowDone[bestI] = true;
                else
                    colDone[targetJ] = true;
            }
        }
    }
    return flow;
}

bool findCycle(int si, int sj,
               const vector<vector<double>> &flow,
               vector<pair<int, int>> &cycle,
               vector<vector<bool>> &visited,
               bool horizontal)
{
    int n = flow.size();
    int m = flow[0].size();

    if (horizontal)
    {
        for (int j = 0; j < m; ++j)
        {
            if (j == sj)
                continue;

            if (flow[si][j] > 0 || (si == cycle[0].first && j == cycle[0].second))
            {
                if (visited[si][j])
                    continue;

                cycle.push_back({si, j});
                visited[si][j] = true;

                if (j == cycle[0].second && cycle.size() >= 4)
                    return true;

                if (findCycle(si, j, flow, cycle, visited, !horizontal))
                    return true;

                cycle.pop_back();
                visited[si][j] = false;
            }
        }
    }
    else
    {
        for (int i = 0; i < n; ++i)
        {
            if (i == si)
                continue;

            if (flow[i][sj] > 0 || (i == cycle[0].first && sj == cycle[0].second))
            {
                if (visited[i][sj])
                    continue;

                cycle.push_back({i, sj});
                visited[i][sj] = true;

                if (i == cycle[0].first && cycle.size() >= 4)
                    return true;

                if (findCycle(i, sj, flow, cycle, visited, !horizontal))
                    return true;

                cycle.pop_back();
                visited[i][sj] = false;
            }
        }
    }
    return false;
}

bool hasCycleBFS(const vector<vector<double>> &flow)
{
    int n = flow.size();
    int m = flow[0].size();

    vector<vector<int>> adj(n + m);

    // Construire le graphe biparti
    for (int i = 0; i < n; ++i)
    {
        for (int j = 0; j < m; ++j)
        {
            if (flow[i][j] > 0)
            {
                adj[i].push_back(n + j);
                adj[n + j].push_back(i);
            }
        }
    }

    vector<bool> visited(n + m, false);
    vector<int> parent(n + m, -1);

    for (int start = 0; start < n + m; ++start)
    {
        if (visited[start])
            continue;

        queue<int> q;
        q.push(start);
        visited[start] = true;

        while (!q.empty())
        {
            int u = q.front();
            q.pop();

            for (int v : adj[u])
            {
                if (!visited[v])
                {
                    visited[v] = true;
                    parent[v] = u;
                    q.push(v);
                }
                else if (parent[u] != v)
                {
                    cout << "Cycle détecté !" << endl;
                    return true;
                }
            }
        }
    }
    return false;
}

bool isConnected(const vector<vector<double>> &flow)
{
    int n = flow.size();
    int m = flow[0].size();

    vector<vector<int>> adj(n + m);

    for (int i = 0; i < n; ++i)
        for (int j = 0; j < m; ++j)
            if (flow[i][j] > 0)
            {
                adj[i].push_back(n + j);
                adj[n + j].push_back(i);
            }

    vector<bool> visited(n + m, false);
    queue<int> q;
    q.push(0);
    visited[0] = true;
    while (!q.empty())
    {
        int u = q.front();
        q.pop();
        for (int v : adj[u])
        {
            if (!visited[v])
            {
                visited[v] = true;
                q.push(v);
            }
        }
    }

    for (bool v : visited)
        if (!v)
            return false;
    return true;
}

void computePotentials(const Problem &p,
                       const vector<vector<double>> &flow,
                       vector<double> &u,
                       vector<double> &v)
{

    int n = p.n, m = p.m;
    u.assign(n, INF);
    v.assign(m, INF);
    u[0] = 0;
    bool updated = true;
    while (updated)
    {
        updated = false;
        for (int i = 0; i < n; ++i)
        {
            for (int j = 0; j < m; ++j)
            {
                if (flow[i][j] > 0)
                {
                    if (u[i] != INF && v[j] == INF)
                    {
                        v[j] = p.costs[i][j] - u[i];
                        updated = true;
                    }
                    else if (v[j] != INF && u[i] == INF)
                    {
                        u[i] = p.costs[i][j] - v[j];
                        updated = true;
                    }
                }
            }
        }
    }
}

double findBestImprovement(const Problem &p,
                           const vector<vector<double>> &flow,
                           const vector<double> &u,
                           const vector<double> &v,
                           int &bestI, int &bestJ)
{

    double minDelta = 0;
    for (int i = 0; i < p.n; ++i)
    {
        for (int j = 0; j < p.m; ++j)
        {
            if (flow[i][j] == 0)
            {
                double delta = p.costs[i][j] - (u[i] + v[j]);
                if (delta < minDelta)
                {
                    minDelta = delta;
                    bestI = i;
                    bestJ = j;
                }
            }
        }
    }
    return minDelta;
}

void fixDegeneracy(vector<vector<double>> &flow)
{
    int n = flow.size();
    int m = flow[0].size();
    auto countArcs = [&]()
    {
        int count = 0;
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < m; ++j)
                if (flow[i][j] > 0)
                    count++;
        return count;
    };

    int required = n + m - 1;
    while (countArcs() < required)
    {
        bool added = false;
        for (int i = 0; i < n && !added; ++i)
        {
            for (int j = 0; j < m && !added; ++j)
            {
                if (flow[i][j] == 0)
                {
                    flow[i][j] = 1e-9;
                    if (!hasCycleBFS(flow))
                    {
                        cout << "Ajout d'un zero artificiel en (" << i << "," << j << ")\n";
                        added = true;
                    }
                    else
                    {
                        flow[i][j] = 0;
                    }
                }
            }
        }

        if (!added)
        {
            cout << "Impossible de corriger la degenerescence proprement.\n";
            break;
        }
    }
}

void solveSteppingStone(const Problem &p, vector<vector<double>> &flow)
{
    int n = p.n, m = p.m;

    while (true)
    {
        fixDegeneracy(flow);
        vector<double> u(n, INF), v(m, INF);
        u[0] = 0;
        bool updated = true;
        while (updated)
        {
            updated = false;
            for (int i = 0; i < n; ++i)
            {
                for (int j = 0; j < m; ++j)
                {
                    if (flow[i][j] > 0)
                    {
                        if (u[i] != INF && v[j] == INF)
                        {
                            v[j] = p.costs[i][j] - u[i];
                            updated = true;
                        }
                        else if (v[j] != INF && u[i] == INF)
                        {
                            u[i] = p.costs[i][j] - v[j];
                            updated = true;
                        }
                    }
                }
            }
        }

        /*
        cout << "\nPotentiels u : ";
        for (double x : u) cout << x << " ";
        cout << "\nPotentiels v : ";
        for (double x : v) cout << x << " ";
        cout << endl;
        */

        double bestDelta = 0;
        int bestI = -1, bestJ = -1;

        for (int i = 0; i < n; ++i)
        {
            for (int j = 0; j < m; ++j)
            {
                if (flow[i][j] == 0)
                {
                    if (u[i] == INF || v[j] == INF)
                        continue;

                    double delta = p.costs[i][j] - (u[i] + v[j]);

                    if (delta < bestDelta)
                    {
                        bestDelta = delta;
                        bestI = i;
                        bestJ = j;
                    }
                }
            }
        }

        if (bestDelta >= 0)
        {
            cout << "\nSolution optimale atteinte.\n";
            break;
        }

        /*
        cout << "\nArête améliorante : (" << bestI << "," << bestJ << ")"
             << " avec delta = " << bestDelta << endl;
        */
 
        vector<pair<int, int>> cycle;
        vector<vector<bool>> visited(n, vector<bool>(m, false));

        cycle.push_back({bestI, bestJ});
        visited[bestI][bestJ] = true;

        if (!findCycle(bestI, bestJ, flow, cycle, visited, true))
        {
            cout << "Erreur : cycle introuvable\n";
            break;
        }

        double theta = INF;
        for (int k = 1; k < cycle.size(); k += 2)
        {
            int i = cycle[k].first;
            int j = cycle[k].second;
            theta = min(theta, flow[i][j]);
        }

        cout << "Theta = " << theta << endl;

        for (int k = 0; k < cycle.size(); ++k)
        {
            int i = cycle[k].first;
            int j = cycle[k].second;

            if (k % 2 == 0)
                flow[i][j] += theta;
            else
                flow[i][j] -= theta;
        }

        for (int i = 0; i < n; ++i)
        {
            for (int j = 0; j < m; ++j)
            {
                if (flow[i][j] < 1e-10)
                    flow[i][j] = 0;
            }
        }

        cout << "Iteration suivante...\n";
    }
}

Problem generateRandomProblem(int n)
{
    Problem p;
    p.n = n;
    p.m = n;
    p.costs.resize(n, vector<double>(n));
    p.provisions.assign(n, 0);
    p.commands.assign(n, 0);
    for (int i = 0; i < n; ++i)
    {
        for (int j = 0; j < n; ++j)
        {
            p.costs[i][j] = rand() % 100 + 1;
            int q = rand() % 50 + 1;
            p.provisions[i] += q;
            p.commands[j] += q;
        }
    }
    return p;
}

void runComplexityStudy()
{
    vector<int> values_n = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100};
    ofstream results("complexite_stats.csv");
    results << "n,tGen,thetaNO,thetaBH,tNO,tBH\n";

    cout << fixed << setprecision(6);
    for (int n : values_n)
    {
        cout << "\n>>> TEST POUR n = " << n << endl;

        for (int iter = 0; iter < 20; ++iter)
        {
            // 1. Temps Génération
            auto s1 = chrono::high_resolution_clock::now();
            Problem p = generateRandomProblem(n);
            auto e1 = chrono::high_resolution_clock::now();
            double tGen = chrono::duration<double>(e1 - s1).count();

            // 2. Temps Nord-Ouest (thetaNO)
            auto s2 = chrono::high_resolution_clock::now();
            vector<vector<double>> fNO = northwestCorner(p);
            auto e2 = chrono::high_resolution_clock::now();
            double thetaNO = chrono::duration<double>(e2 - s2).count();

            // 3. Temps Balas-Hammer (thetaBH)
            auto s3 = chrono::high_resolution_clock::now();
            vector<vector<double>> fBH = balasHammer(p);
            auto e3 = chrono::high_resolution_clock::now();
            double thetaBH = chrono::duration<double>(e3 - s3).count();

            // 4. Temps Marche-pied depuis NO (tNO)
            auto s4 = chrono::high_resolution_clock::now();
            solveSteppingStone(p, fNO);
            auto e4 = chrono::high_resolution_clock::now();
            double tNO = chrono::duration<double>(e4 - s4).count();

            // 5. Temps Marche-pied depuis BH (tBH)
            auto s5 = chrono::high_resolution_clock::now();
            solveSteppingStone(p, fBH);
            auto e5 = chrono::high_resolution_clock::now();
            double tBH = chrono::duration<double>(e5 - s5).count();

            results << n << "," << tGen << "," << thetaNO << "," << thetaBH << "," << tNO << "," << tBH << "\n";
        }
    }
    results.close();
}

int main()
{
    srand(time(NULL));
    int choice;
    cout << "--- MENU PROJET TRANSPORT ---\n1. Resoudre un fichier .txt\n2. Etude de complexite\nChoix: ";
    cin >> choice;

    if (choice == 1)
    {
        string fn;
        cout << "Nom fichier: ";
        cin >> fn;
        Problem p = readProblem(fn);
        if (p.n == 0)
            return 0;
        vector<vector<double>> flow = balasHammer(p);
        displayTable("Flux Balas-Hammer", flow, p.provisions, p.commands);
        solveSteppingStone(p, flow);
    }
    else if (choice == 2)
    {
        runComplexityStudy();
        cout << "\nFichier 'complexite_stats.csv' cree.\n";
    }
    return 0;
}
