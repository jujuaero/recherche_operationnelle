#ifndef TRANSPORT_CORE_H
#define TRANSPORT_CORE_H

#include <stdint.h>

typedef struct {
    int iterations;
    int hit_max_iterations;
} SolveResultC;

typedef struct {
    int n;
    int m;
    int* costs;
    int* supplies;
    int* demands;
    int* transport;
    unsigned char* basis;
    int basis_count;
} TransportProblemC;

int tp_init(TransportProblemC* p, int n, int m);
void tp_free(TransportProblemC* p);
void tp_reset_solution(TransportProblemC* p);

int tp_generate_square_problem(TransportProblemC* p, int n, uint64_t* rng_state);
int tp_copy_problem_data_reset(TransportProblemC* dst, const TransportProblemC* src);

int64_t tp_total_cost(const TransportProblemC* p);

int tp_north_west(TransportProblemC* p);
int tp_balas_hammer(TransportProblemC* p);
int tp_stepping_stone_potentials(
    TransportProblemC* p,
    const char* initial_method,
    int max_iterations,
    int initialization_done,
    SolveResultC* out_result
);

const char* tp_last_error(void);

#endif
