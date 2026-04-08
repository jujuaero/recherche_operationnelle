#pragma once

#include <string>

#include "transport_problem.hpp"

namespace transport {

TransportProblem generateBalancedProblem(int n, int m, int minValue = 1, int maxValue = 100);
TransportProblem generateSquareStudyProblem(int n, int minValue = 1, int maxValue = 100);
void writeProblemFile(const TransportProblem& p, const std::string& filePath);

}  // namespace transport
