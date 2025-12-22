
#include "setup.hpp"
#include "mazecode.hpp"
#include "maze_state.hpp"

using namespace std;

int main(){
    readMaze();
    DFS_for_maze();
    BFS_for_maze();
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
