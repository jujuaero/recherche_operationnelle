#include "../include/transport_core.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define COST_AT(p, i, j) ((p)->costs[(i) * (p)->m + (j)])
#define TRANS_AT(p, i, j) ((p)->transport[(i) * (p)->m + (j)])
#define BASIS_AT(p, i, j) ((p)->basis[(i) * (p)->m + (j)])

static char g_last_error[256] = "";

static int set_error(const char* msg) {
    size_t len = strlen(msg);
    if (len >= sizeof(g_last_error)) {
        len = sizeof(g_last_error) - 1;
    }
    memcpy(g_last_error, msg, len);
    g_last_error[len] = '\0';
    return -1;
}

static void clear_error(void) {
    g_last_error[0] = '\0';
}

const char* tp_last_error(void) {
    return g_last_error;
}

static uint64_t next_u64(uint64_t* state) {
    uint64_t x = *state;
    if (x == 0) {
        x = 0x9E3779B97F4A7C15ULL ^ (uint64_t)clock();
    }

    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;

    *state = x;
    return x * 2685821657736338717ULL;
}

static int rand_range(uint64_t* state, int lo, int hi) {
    uint64_t span = (uint64_t)(hi - lo + 1);
    uint64_t rnd = next_u64(state);
    return lo + (int)(rnd % span);
}

static int cell_count(const TransportProblemC* p) {
    return p->n * p->m;
}

static int idx_of(const TransportProblemC* p, int i, int j) {
    return i * p->m + j;
}

static int row_of(const TransportProblemC* p, int idx) {
    return idx / p->m;
}

static int col_of(const TransportProblemC* p, int idx) {
    return idx % p->m;
}

static void basis_add_idx(TransportProblemC* p, int idx) {
    if (!p->basis[idx]) {
        p->basis[idx] = 1;
        p->basis_count += 1;
    }
}

static void basis_remove_idx(TransportProblemC* p, int idx) {
    if (p->basis[idx]) {
        p->basis[idx] = 0;
        p->basis_count -= 1;
    }
}

static void trim_basis_to_expected(TransportProblemC* p) {
    int expected = p->n + p->m - 1;
    if (p->basis_count <= expected) {
        return;
    }

    int kept = 0;
    int total = cell_count(p);
    for (int idx = 0; idx < total; ++idx) {
        if (!p->basis[idx]) {
            continue;
        }

        kept += 1;
        if (kept > expected) {
            p->basis[idx] = 0;
            p->basis_count -= 1;
        }
    }
}

int tp_init(TransportProblemC* p, int n, int m) {
    clear_error();

    if (p == NULL || n <= 0 || m <= 0) {
        return set_error("tp_init: invalid argument");
    }

    tp_free(p);

    p->n = n;
    p->m = m;
    p->basis_count = 0;

    p->costs = (int*)calloc((size_t)n * (size_t)m, sizeof(int));
    p->supplies = (int*)calloc((size_t)n, sizeof(int));
    p->demands = (int*)calloc((size_t)m, sizeof(int));
    p->transport = (int*)calloc((size_t)n * (size_t)m, sizeof(int));
    p->basis = (unsigned char*)calloc((size_t)n * (size_t)m, sizeof(unsigned char));

    if (p->costs == NULL || p->supplies == NULL || p->demands == NULL || p->transport == NULL || p->basis == NULL) {
        tp_free(p);
        return set_error("tp_init: out of memory");
    }

    return 0;
}

void tp_free(TransportProblemC* p) {
    if (p == NULL) {
        return;
    }

    free(p->costs);
    free(p->supplies);
    free(p->demands);
    free(p->transport);
    free(p->basis);

    p->costs = NULL;
    p->supplies = NULL;
    p->demands = NULL;
    p->transport = NULL;
    p->basis = NULL;
    p->n = 0;
    p->m = 0;
    p->basis_count = 0;
}

void tp_reset_solution(TransportProblemC* p) {
    if (p == NULL || p->transport == NULL || p->basis == NULL) {
        return;
    }

    memset(p->transport, 0, (size_t)cell_count(p) * sizeof(int));
    memset(p->basis, 0, (size_t)cell_count(p) * sizeof(unsigned char));
    p->basis_count = 0;
}

int tp_generate_square_problem(TransportProblemC* p, int n, uint64_t* rng_state) {
    clear_error();

    if (p == NULL || rng_state == NULL || n <= 0) {
        return set_error("tp_generate_square_problem: invalid argument");
    }

    if (p->n != n || p->m != n || p->costs == NULL) {
        if (tp_init(p, n, n) != 0) {
            return -1;
        }
    }

    memset(p->costs, 0, (size_t)n * (size_t)n * sizeof(int));
    memset(p->supplies, 0, (size_t)n * sizeof(int));
    memset(p->demands, 0, (size_t)n * sizeof(int));

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int index = idx_of(p, i, j);
            int cost = rand_range(rng_state, 1, 100);
            int val = rand_range(rng_state, 1, 100);
            p->costs[index] = cost;
            p->supplies[i] += val;
            p->demands[j] += val;
        }
    }

    tp_reset_solution(p);
    return 0;
}

int tp_copy_problem_data_reset(TransportProblemC* dst, const TransportProblemC* src) {
    clear_error();

    if (dst == NULL || src == NULL || src->n <= 0 || src->m <= 0) {
        return set_error("tp_copy_problem_data_reset: invalid argument");
    }

    if (dst->n != src->n || dst->m != src->m || dst->costs == NULL) {
        if (tp_init(dst, src->n, src->m) != 0) {
            return -1;
        }
    }

    memcpy(dst->costs, src->costs, (size_t)cell_count(src) * sizeof(int));
    memcpy(dst->supplies, src->supplies, (size_t)src->n * sizeof(int));
    memcpy(dst->demands, src->demands, (size_t)src->m * sizeof(int));
    tp_reset_solution(dst);
    return 0;
}

int64_t tp_total_cost(const TransportProblemC* p) {
    int total_cells;
    int64_t total = 0;

    if (p == NULL) {
        return 0;
    }

    total_cells = cell_count(p);
    for (int idx = 0; idx < total_cells; ++idx) {
        total += (int64_t)p->costs[idx] * (int64_t)p->transport[idx];
    }

    return total;
}

int tp_north_west(TransportProblemC* p) {
    int* s;
    int* d;
    int i = 0;
    int j = 0;

    clear_error();

    if (p == NULL || p->n <= 0 || p->m <= 0 || p->costs == NULL) {
        return set_error("tp_north_west: invalid problem");
    }

    tp_reset_solution(p);

    s = (int*)malloc((size_t)p->n * sizeof(int));
    d = (int*)malloc((size_t)p->m * sizeof(int));
    if (s == NULL || d == NULL) {
        free(s);
        free(d);
        return set_error("tp_north_west: out of memory");
    }

    memcpy(s, p->supplies, (size_t)p->n * sizeof(int));
    memcpy(d, p->demands, (size_t)p->m * sizeof(int));

    while (i < p->n && j < p->m) {
        int q = (s[i] < d[j]) ? s[i] : d[j];
        int index = idx_of(p, i, j);

        p->transport[index] = q;
        basis_add_idx(p, index);

        s[i] -= q;
        d[j] -= q;

        if (s[i] == 0 && d[j] == 0) {
            if (i + 1 < p->n) {
                basis_add_idx(p, idx_of(p, i + 1, j));
            } else if (j + 1 < p->m) {
                basis_add_idx(p, idx_of(p, i, j + 1));
            }
            i += 1;
            j += 1;
        } else if (s[i] == 0) {
            i += 1;
        } else {
            j += 1;
        }
    }

    trim_basis_to_expected(p);

    free(s);
    free(d);
    return 0;
}

int tp_balas_hammer(TransportProblemC* p) {
    int* s;
    int* d;
    unsigned char* active_row;
    unsigned char* active_col;
    int active_rows;
    int active_cols;

    clear_error();

    if (p == NULL || p->n <= 0 || p->m <= 0 || p->costs == NULL) {
        return set_error("tp_balas_hammer: invalid problem");
    }

    tp_reset_solution(p);

    s = (int*)malloc((size_t)p->n * sizeof(int));
    d = (int*)malloc((size_t)p->m * sizeof(int));
    active_row = (unsigned char*)malloc((size_t)p->n * sizeof(unsigned char));
    active_col = (unsigned char*)malloc((size_t)p->m * sizeof(unsigned char));

    if (s == NULL || d == NULL || active_row == NULL || active_col == NULL) {
        free(s);
        free(d);
        free(active_row);
        free(active_col);
        return set_error("tp_balas_hammer: out of memory");
    }

    memcpy(s, p->supplies, (size_t)p->n * sizeof(int));
    memcpy(d, p->demands, (size_t)p->m * sizeof(int));
    memset(active_row, 1, (size_t)p->n * sizeof(unsigned char));
    memset(active_col, 1, (size_t)p->m * sizeof(unsigned char));

    active_rows = p->n;
    active_cols = p->m;

    while (active_rows > 0 && active_cols > 0) {
        int best_is_row = 1;
        int best_idx = -1;
        int best_pair = -1;
        int best_penalty = INT_MIN;
        int best_min_cost = INT_MAX;
        int best_q = -1;

        for (int i = 0; i < p->n; ++i) {
            if (!active_row[i]) {
                continue;
            }

            int best1 = INT_MAX;
            int best2 = INT_MAX;
            int best_j = -1;

            for (int j = 0; j < p->m; ++j) {
                if (!active_col[j]) {
                    continue;
                }

                int c = COST_AT(p, i, j);
                if (c < best1) {
                    best2 = best1;
                    best1 = c;
                    best_j = j;
                } else if (c < best2) {
                    best2 = c;
                }
            }

            if (best_j < 0) {
                continue;
            }

            {
                int penalty = (best2 == INT_MAX) ? best1 : (best2 - best1);
                int q = (s[i] < d[best_j]) ? s[i] : d[best_j];
                int better = 0;

                if (penalty > best_penalty) {
                    better = 1;
                } else if (penalty == best_penalty && best1 < best_min_cost) {
                    better = 1;
                } else if (penalty == best_penalty && best1 == best_min_cost && q > best_q) {
                    better = 1;
                }

                if (better) {
                    best_is_row = 1;
                    best_idx = i;
                    best_pair = best_j;
                    best_penalty = penalty;
                    best_min_cost = best1;
                    best_q = q;
                }
            }
        }

        for (int j = 0; j < p->m; ++j) {
            if (!active_col[j]) {
                continue;
            }

            int best1 = INT_MAX;
            int best2 = INT_MAX;
            int best_i = -1;

            for (int i = 0; i < p->n; ++i) {
                if (!active_row[i]) {
                    continue;
                }

                int c = COST_AT(p, i, j);
                if (c < best1) {
                    best2 = best1;
                    best1 = c;
                    best_i = i;
                } else if (c < best2) {
                    best2 = c;
                }
            }

            if (best_i < 0) {
                continue;
            }

            {
                int penalty = (best2 == INT_MAX) ? best1 : (best2 - best1);
                int q = (s[best_i] < d[j]) ? s[best_i] : d[j];
                int better = 0;

                if (penalty > best_penalty) {
                    better = 1;
                } else if (penalty == best_penalty && best1 < best_min_cost) {
                    better = 1;
                } else if (penalty == best_penalty && best1 == best_min_cost && q > best_q) {
                    better = 1;
                }

                if (better) {
                    best_is_row = 0;
                    best_idx = j;
                    best_pair = best_i;
                    best_penalty = penalty;
                    best_min_cost = best1;
                    best_q = q;
                }
            }
        }

        if (best_idx < 0) {
            break;
        }

        {
            int i = best_is_row ? best_idx : best_pair;
            int j = best_is_row ? best_pair : best_idx;
            int q = (s[i] < d[j]) ? s[i] : d[j];
            int index = idx_of(p, i, j);

            p->transport[index] += q;
            basis_add_idx(p, index);

            s[i] -= q;
            d[j] -= q;

            if (s[i] == 0 && d[j] == 0) {
                active_row[i] = 0;
                active_col[j] = 0;
                active_rows -= 1;
                active_cols -= 1;

                {
                    int i_alt = -1;
                    int j_alt = -1;
                    for (int r = 0; r < p->n; ++r) {
                        if (active_row[r]) {
                            i_alt = r;
                            break;
                        }
                    }
                    for (int c = 0; c < p->m; ++c) {
                        if (active_col[c]) {
                            j_alt = c;
                            break;
                        }
                    }

                    if (i_alt >= 0) {
                        basis_add_idx(p, idx_of(p, i_alt, j));
                    } else if (j_alt >= 0) {
                        basis_add_idx(p, idx_of(p, i, j_alt));
                    }
                }
            } else if (s[i] == 0) {
                active_row[i] = 0;
                active_rows -= 1;
            } else if (d[j] == 0) {
                active_col[j] = 0;
                active_cols -= 1;
            }
        }
    }

    trim_basis_to_expected(p);

    free(s);
    free(d);
    free(active_row);
    free(active_col);
    return 0;
}

static void compute_potentials(
    const TransportProblemC* p,
    int* u,
    int* v,
    unsigned char* known_u,
    unsigned char* known_v
) {
    int changed = 1;

    memset(u, 0, (size_t)p->n * sizeof(int));
    memset(v, 0, (size_t)p->m * sizeof(int));
    memset(known_u, 0, (size_t)p->n * sizeof(unsigned char));
    memset(known_v, 0, (size_t)p->m * sizeof(unsigned char));

    if (p->n > 0) {
        known_u[0] = 1;
        u[0] = 0;
    }

    while (changed) {
        changed = 0;

        for (int idx = 0; idx < cell_count(p); ++idx) {
            if (!p->basis[idx]) {
                continue;
            }

            {
                int i = row_of(p, idx);
                int j = col_of(p, idx);
                int c = p->costs[idx];

                if (known_u[i] && !known_v[j]) {
                    v[j] = c - u[i];
                    known_v[j] = 1;
                    changed = 1;
                } else if (known_v[j] && !known_u[i]) {
                    u[i] = c - v[j];
                    known_u[i] = 1;
                    changed = 1;
                }
            }
        }

        if (!changed) {
            for (int i = 0; i < p->n; ++i) {
                if (!known_u[i]) {
                    known_u[i] = 1;
                    u[i] = 0;
                    changed = 1;
                    break;
                }
            }
        }
    }
}

static int dfs_cycle(
    const TransportProblemC* p,
    int entering_idx,
    const int* nodes,
    int node_count,
    int current_idx,
    int move_row,
    int* path,
    int* path_len,
    unsigned char* visited
) {
    int cur_row = row_of(p, current_idx);
    int cur_col = col_of(p, current_idx);

    for (int k = 0; k < node_count; ++k) {
        int nxt = nodes[k];

        if (nxt == current_idx) {
            continue;
        }

        if (move_row) {
            if (row_of(p, nxt) != cur_row) {
                continue;
            }
        } else if (col_of(p, nxt) != cur_col) {
            continue;
        }

        if (nxt == entering_idx && *path_len >= 4) {
            path[*path_len] = entering_idx;
            *path_len += 1;
            return 1;
        }

        if (nxt == entering_idx) {
            continue;
        }

        if (!p->basis[nxt] || visited[nxt]) {
            continue;
        }

        visited[nxt] = 1;
        path[*path_len] = nxt;
        *path_len += 1;

        if (dfs_cycle(
                p,
                entering_idx,
                nodes,
                node_count,
                nxt,
                !move_row,
                path,
                path_len,
                visited
            )) {
            return 1;
        }

        *path_len -= 1;
        visited[nxt] = 0;
    }

    return 0;
}

static int find_cycle(
    const TransportProblemC* p,
    int entering_idx,
    int* nodes,
    int* path,
    unsigned char* visited,
    int* out_len
) {
    int node_count = 0;
    int total = cell_count(p);
    int path_len = 1;

    for (int idx = 0; idx < total; ++idx) {
        if (p->basis[idx]) {
            nodes[node_count++] = idx;
        }
    }
    nodes[node_count++] = entering_idx;

    memset(visited, 0, (size_t)total * sizeof(unsigned char));
    path[0] = entering_idx;

    if (dfs_cycle(p, entering_idx, nodes, node_count, entering_idx, 1, path, &path_len, visited)) {
        *out_len = path_len;
        return 1;
    }

    path_len = 1;
    memset(visited, 0, (size_t)total * sizeof(unsigned char));
    path[0] = entering_idx;

    if (dfs_cycle(p, entering_idx, nodes, node_count, entering_idx, 0, path, &path_len, visited)) {
        *out_len = path_len;
        return 1;
    }

    return 0;
}

int tp_stepping_stone_potentials(
    TransportProblemC* p,
    const char* initial_method,
    int max_iterations,
    int initialization_done,
    SolveResultC* out_result
) {
    int* u = NULL;
    int* v = NULL;
    unsigned char* known_u = NULL;
    unsigned char* known_v = NULL;
    int* nodes = NULL;
    int* path = NULL;
    unsigned char* visited = NULL;
    int iteration;
    int optimal = 0;
    int total_cells;

    clear_error();

    if (p == NULL || initial_method == NULL || max_iterations <= 0) {
        return set_error("tp_stepping_stone_potentials: invalid argument");
    }

    if (!initialization_done) {
        if (strcmp(initial_method, "nord_ouest") == 0 || strcmp(initial_method, "north_west") == 0) {
            if (tp_north_west(p) != 0) {
                return -1;
            }
        } else if (strcmp(initial_method, "balas_hammer") == 0) {
            if (tp_balas_hammer(p) != 0) {
                return -1;
            }
        } else {
            return set_error("tp_stepping_stone_potentials: unknown initial method");
        }
    } else if (p->basis_count <= 0) {
        return set_error("tp_stepping_stone_potentials: empty basis with initialization_done=1");
    }

    total_cells = cell_count(p);

    u = (int*)malloc((size_t)p->n * sizeof(int));
    v = (int*)malloc((size_t)p->m * sizeof(int));
    known_u = (unsigned char*)malloc((size_t)p->n * sizeof(unsigned char));
    known_v = (unsigned char*)malloc((size_t)p->m * sizeof(unsigned char));
    nodes = (int*)malloc((size_t)total_cells * sizeof(int));
    path = (int*)malloc((size_t)(total_cells + 2) * sizeof(int));
    visited = (unsigned char*)malloc((size_t)total_cells * sizeof(unsigned char));

    if (u == NULL || v == NULL || known_u == NULL || known_v == NULL || nodes == NULL || path == NULL || visited == NULL) {
        free(u);
        free(v);
        free(known_u);
        free(known_v);
        free(nodes);
        free(path);
        free(visited);
        return set_error("tp_stepping_stone_potentials: out of memory");
    }

    for (iteration = 1; iteration <= max_iterations; ++iteration) {
        int entering_idx = -1;
        int best_delta = 0;
        int cycle_len = 0;

        compute_potentials(p, u, v, known_u, known_v);

        for (int idx = 0; idx < total_cells; ++idx) {
            if (!p->basis[idx]) {
                int i = row_of(p, idx);
                int j = col_of(p, idx);
                int delta = p->costs[idx] - (u[i] + v[j]);

                if (delta < best_delta) {
                    best_delta = delta;
                    entering_idx = idx;
                }
            }
        }

        if (entering_idx < 0) {
            optimal = 1;
            break;
        }

        if (!find_cycle(p, entering_idx, nodes, path, visited, &cycle_len)) {
            free(u);
            free(v);
            free(known_u);
            free(known_v);
            free(nodes);
            free(path);
            free(visited);
            return set_error("tp_stepping_stone_potentials: unable to find cycle");
        }

        {
            int theta = INT_MAX;
            int leaving_idx = -1;

            for (int k = 1; k < cycle_len - 1; k += 2) {
                int idx = path[k];
                int value = p->transport[idx];
                if (value < theta) {
                    theta = value;
                }
            }

            if (theta == INT_MAX) {
                free(u);
                free(v);
                free(known_u);
                free(known_v);
                free(nodes);
                free(path);
                free(visited);
                return set_error("tp_stepping_stone_potentials: invalid cycle");
            }

            for (int k = 0; k < cycle_len - 1; ++k) {
                int idx = path[k];
                if ((k & 1) == 0) {
                    p->transport[idx] += theta;
                } else {
                    p->transport[idx] -= theta;
                }
            }

            basis_add_idx(p, entering_idx);

            for (int k = 1; k < cycle_len - 1; k += 2) {
                int idx = path[k];
                if (p->transport[idx] == 0 && p->basis[idx]) {
                    leaving_idx = idx;
                    break;
                }
            }

            if (leaving_idx >= 0) {
                basis_remove_idx(p, leaving_idx);
            }

            trim_basis_to_expected(p);
        }
    }

    if (out_result != NULL) {
        out_result->iterations = optimal ? (iteration - 1) : max_iterations;
        out_result->hit_max_iterations = optimal ? 0 : 1;
    }

    free(u);
    free(v);
    free(known_u);
    free(known_v);
    free(nodes);
    free(path);
    free(visited);
    return 0;
}
