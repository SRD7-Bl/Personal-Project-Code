#pragma once
#include "setup.hpp"

void DFS_for_maze(std::string out_dir);
void BFS_for_maze(std::string out_dir);
std::vector<std::pair<int,int>> AStar_shortest_path(std::string out_dir);
