
#include "setup.hpp"
#include "mazecode.hpp"
#include "maze_state.hpp"

using namespace std;

int main(){
    readMaze();
    DFS_for_maze();
    BFS_for_maze();

    
    auto path = AStar_shortest_path();
        if (path.empty()) {
            std::cout << "A*: No path\n";
        } else {
            std::cout << "A*: shortest length = " << (int)path.size() - 1 << "\n";
            for (auto [x,y] : path) {
                std::cout << "(" << x << ", " << y << ")\n";
            }
        }
    return 0;
}

/*
 
 7 7
 4 0 0 0 1 0 0
 1 1 1 0 1 0 1
 0 0 0 0 0 0 0
 0 1 1 1 1 1 0
 0 0 0 0 0 1 0
 1 1 1 1 0 1 0
 0 0 0 0 0 0 3

 */
