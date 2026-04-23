#include "../include/transport_core.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

#ifdef _WIN32
#include <direct.h>
#define MKDIR(path) _mkdir(path)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(path) mkdir(path, 0755)
#endif

enum {
    MAX_ITERATIONS_MARCHE_PIED = 5000,
};

typedef struct {
    int n;
    int repetitions;
} SizeConfig;

typedef struct {
    int n;
    int repetition;
    double theta_NO_s;
    double theta_BH_s;
    double t_NO_s;
    double t_BH_s;
    double theta_plus_t_NO_s;
    double theta_plus_t_BH_s;
} ResultRow;

typedef struct {
    ResultRow* data;
    size_t size;
    size_t capacity;
} ResultTable;

static const SizeConfig CONFIG_SIZES[] = {
    {10, 100},
    {40, 100},
    {100, 100},
    {400, 100},
};

static const size_t CONFIG_SIZES_COUNT = sizeof(CONFIG_SIZES) / sizeof(CONFIG_SIZES[0]);

static double cpu_seconds(void) {
    return (double)clock() / (double)CLOCKS_PER_SEC;
}

static int append_result(ResultTable* table, const ResultRow* row) {
    if (table->size == table->capacity) {
        size_t new_capacity = (table->capacity == 0) ? 64 : table->capacity * 2;
        ResultRow* resized = (ResultRow*)realloc(table->data, new_capacity * sizeof(ResultRow));
        if (resized == NULL) {
            return -1;
        }
        table->data = resized;
        table->capacity = new_capacity;
    }

    table->data[table->size++] = *row;
    return 0;
}

static void free_results(ResultTable* table) {
    free(table->data);
    table->data = NULL;
    table->size = 0;
    table->capacity = 0;
}

static int ensure_directory_recursive(const char* path) {
    char buffer[512];
    size_t len = strlen(path);

    if (len == 0 || len >= sizeof(buffer)) {
        return -1;
    }

    memcpy(buffer, path, len + 1);

    for (size_t i = 0; i < len; ++i) {
        if (buffer[i] == '\\') {
            buffer[i] = '/';
        }
    }

    for (size_t i = 1; i < len; ++i) {
        if (buffer[i] == '/') {
            char saved = buffer[i];
            buffer[i] = '\0';
            if (strlen(buffer) > 0) {
                if (MKDIR(buffer) != 0 && errno != EEXIST) {
                    return -1;
                }
            }
            buffer[i] = saved;
        }
    }

    if (MKDIR(buffer) != 0 && errno != EEXIST) {
        return -1;
    }

    return 0;
}

static int measure_one_realization(
    const TransportProblemC* base,
    TransportProblemC* work_no,
    TransportProblemC* work_bh,
    TransportProblemC* work_no_opt,
    TransportProblemC* work_bh_opt,
    ResultRow* out
) {
    double t0;

    if (tp_copy_problem_data_reset(work_no, base) != 0) {
        return -1;
    }
    t0 = cpu_seconds();
    if (tp_north_west(work_no) != 0) {
        return -1;
    }
    out->theta_NO_s = cpu_seconds() - t0;

    if (tp_copy_problem_data_reset(work_bh, base) != 0) {
        return -1;
    }
    t0 = cpu_seconds();
    if (tp_balas_hammer(work_bh) != 0) {
        return -1;
    }
    out->theta_BH_s = cpu_seconds() - t0;

    if (tp_copy_problem_data_reset(work_no_opt, base) != 0) {
        return -1;
    }
    if (tp_north_west(work_no_opt) != 0) {
        return -1;
    }
    t0 = cpu_seconds();
    if (tp_stepping_stone_potentials(
            work_no_opt,
            "nord_ouest",
            MAX_ITERATIONS_MARCHE_PIED,
            1,
            NULL
        ) != 0) {
        return -1;
    }
    out->t_NO_s = cpu_seconds() - t0;

    if (tp_copy_problem_data_reset(work_bh_opt, base) != 0) {
        return -1;
    }
    if (tp_balas_hammer(work_bh_opt) != 0) {
        return -1;
    }
    t0 = cpu_seconds();
    if (tp_stepping_stone_potentials(
            work_bh_opt,
            "balas_hammer",
            MAX_ITERATIONS_MARCHE_PIED,
            1,
            NULL
        ) != 0) {
        return -1;
    }
    out->t_BH_s = cpu_seconds() - t0;

    out->theta_plus_t_NO_s = out->theta_NO_s + out->t_NO_s;
    out->theta_plus_t_BH_s = out->theta_BH_s + out->t_BH_s;
    return 0;
}

static int write_results_csv(const char* path, const ResultTable* table) {
    FILE* f = fopen(path, "w");
    if (f == NULL) {
        return -1;
    }

    fprintf(f, "n,repetition,theta_NO_s,theta_BH_s,t_NO_s,t_BH_s,theta_plus_t_NO_s,theta_plus_t_BH_s\n");
    for (size_t i = 0; i < table->size; ++i) {
        const ResultRow* row = &table->data[i];
        fprintf(
            f,
            "%d,%d,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f\n",
            row->n,
            row->repetition,
            row->theta_NO_s,
            row->theta_BH_s,
            row->t_NO_s,
            row->t_BH_s,
            row->theta_plus_t_NO_s,
            row->theta_plus_t_BH_s
        );
    }

    fclose(f);
    return 0;
}

static int find_unique_sizes(const ResultTable* table, int* out_sizes, int max_out) {
    int count = 0;
    for (size_t i = 0; i < table->size; ++i) {
        int n = table->data[i].n;
        int exists = 0;
        for (int j = 0; j < count; ++j) {
            if (out_sizes[j] == n) {
                exists = 1;
                break;
            }
        }
        if (!exists) {
            if (count >= max_out) {
                return -1;
            }
            out_sizes[count++] = n;
        }
    }
    return count;
}

static double get_measure_value(const ResultRow* row, int measure_index) {
    switch (measure_index) {
        case 0: return row->theta_NO_s;
        case 1: return row->theta_BH_s;
        case 2: return row->t_NO_s;
        case 3: return row->t_BH_s;
        case 4: return row->theta_plus_t_NO_s;
        case 5: return row->theta_plus_t_BH_s;
        default: return 0.0;
    }
}

static int write_maxima_csv_and_summary(const char* csv_path, const ResultTable* table) {
    static const char* names[] = {
        "theta_NO_s",
        "theta_BH_s",
        "t_NO_s",
        "t_BH_s",
        "theta_plus_t_NO_s",
        "theta_plus_t_BH_s",
    };

    int sizes[64];
    int size_count = find_unique_sizes(table, sizes, 64);
    if (size_count < 0) {
        return -1;
    }

    FILE* f = fopen(csv_path, "w");
    if (f == NULL) {
        return -1;
    }

    fprintf(f, "n,mesure,temps_max_s\n");

    printf("\nRESUME DES MAXIMA\n");
    printf("================================================================================\n");

    for (int m = 0; m < 6; ++m) {
        double global_best = -1.0;
        int global_n = -1;

        for (int s = 0; s < size_count; ++s) {
            int n = sizes[s];
            double best = -1.0;

            for (size_t i = 0; i < table->size; ++i) {
                if (table->data[i].n == n) {
                    double v = get_measure_value(&table->data[i], m);
                    if (v > best) {
                        best = v;
                    }
                }
            }

            if (best >= 0.0) {
                fprintf(f, "%d,%s,%.8f\n", n, names[m], best);
                if (best > global_best) {
                    global_best = best;
                    global_n = n;
                }
            }
        }

        if (global_best >= 0.0) {
            printf("%s: max=%.6f s pour n=%d\n", names[m], global_best, global_n);
        }
    }

    fclose(f);
    return 0;
}

int main(int argc, char** argv) {
    int quick_mode = 0;
    uint64_t rng_state = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--quick") == 0) {
            quick_mode = 1;
        } else if (strncmp(argv[i], "--seed=", 7) == 0) {
            rng_state = (uint64_t)strtoull(argv[i] + 7, NULL, 10);
        }
    }

    if (rng_state == 0) {
        rng_state = ((uint64_t)time(NULL) << 32) ^ (uint64_t)clock();
    }

    if (ensure_directory_recursive("results") != 0 || ensure_directory_recursive("results/etude_10_c") != 0) {
        fprintf(stderr, "Erreur: impossible de creer le dossier de sortie.\n");
        return 1;
    }

    ResultTable results = {0};

    printf("\n================================================================================\n");
    printf("ETUDE DE COMPLEXITE PROGRESSIVE (VERSION C)\n");
    printf("================================================================================\n");

    for (size_t idx = 0; idx < CONFIG_SIZES_COUNT; ++idx) {
        TransportProblemC base = {0};
        TransportProblemC work_no = {0};
        TransportProblemC work_bh = {0};
        TransportProblemC work_no_opt = {0};
        TransportProblemC work_bh_opt = {0};
        int n = CONFIG_SIZES[idx].n;
        int repetitions = CONFIG_SIZES[idx].repetitions;

        if (quick_mode && n > 500) {
            continue;
        }

        if (tp_init(&base, n, n) != 0 ||
            tp_init(&work_no, n, n) != 0 ||
            tp_init(&work_bh, n, n) != 0 ||
            tp_init(&work_no_opt, n, n) != 0 ||
            tp_init(&work_bh_opt, n, n) != 0) {
            fprintf(stderr, "Erreur initialisation n=%d: %s\n", n, tp_last_error());
            tp_free(&base);
            tp_free(&work_no);
            tp_free(&work_bh);
            tp_free(&work_no_opt);
            tp_free(&work_bh_opt);
            free_results(&results);
            return 1;
        }

        printf("\n[%zu/%zu] Taille n = %5d (%d repetitions)\n", idx + 1, CONFIG_SIZES_COUNT, n, repetitions);

        for (int rep = 1; rep <= repetitions; ++rep) {
            if (tp_generate_square_problem(&base, n, &rng_state) != 0) {
                fprintf(stderr, "  [ERREUR] Generation probleme n=%d, rep=%d: %s\n", n, rep, tp_last_error());
                continue;
            }

            ResultRow row;
            memset(&row, 0, sizeof(row));
            row.n = n;
            row.repetition = rep;

            if (measure_one_realization(
                    &base,
                    &work_no,
                    &work_bh,
                    &work_no_opt,
                    &work_bh_opt,
                    &row
                ) != 0) {
                fprintf(stderr, "  [ERREUR] Mesure n=%d, rep=%d: %s\n", n, rep, tp_last_error());
                continue;
            }

            if (append_result(&results, &row) != 0) {
                fprintf(stderr, "Erreur memoire: impossible de stocker un resultat.\n");
                tp_free(&base);
                tp_free(&work_no);
                tp_free(&work_bh);
                tp_free(&work_no_opt);
                tp_free(&work_bh_opt);
                free_results(&results);
                return 1;
            }

            {
                int progress_step = repetitions / 5;
                if (progress_step <= 0) {
                    progress_step = 1;
                }
                if (rep % progress_step == 0 || rep == repetitions) {
                    int pct = (int)((100.0 * rep) / repetitions);
                    printf("  Progression: %d/%d (%d%%)\n", rep, repetitions, pct);
                }
            }
        }

        tp_free(&base);
        tp_free(&work_no);
        tp_free(&work_bh);
        tp_free(&work_no_opt);
        tp_free(&work_bh_opt);
    }

    if (write_results_csv("results/etude_10_c/resultats_etude_10_c.csv", &results) != 0) {
        fprintf(stderr, "Erreur: impossible d'ecrire resultats_etude_10_c.csv\n");
        free_results(&results);
        return 1;
    }

    if (write_maxima_csv_and_summary("results/etude_10_c/maxima_temps.csv", &results) != 0) {
        fprintf(stderr, "Erreur: impossible d'ecrire maxima_temps.csv\n");
        free_results(&results);
        return 1;
    }

    printf("\n[OK] %zu resultats exportes vers results/etude_10_c/resultats_etude_10_c.csv\n", results.size);
    printf("[OK] Maxima exportes vers results/etude_10_c/maxima_temps.csv\n");

    free_results(&results);
    return 0;
}
