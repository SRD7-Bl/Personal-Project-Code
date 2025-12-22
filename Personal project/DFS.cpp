#include "setup.hpp"
#include "maze_state.hpp"
using namespace std;

void dfs(int x, int y, int dist){
    
    if (!inBounds(x, y)) return; //out of bound
    if (Map[x][y] == 1) return; //wall
    if (vis[x][y]) return; //already been

    if (dist >= bestLen) return;

    vis[x][y] = true;
    curPath.push_back({x, y});

    // at the endpoint
    if (x == ex && y == ey){
        bestLen = dist;
        bestPath = curPath;
        vis[x][y] = false;
        curPath.pop_back();
        return;
    }
    
    for (int k = 0; k < 4; ++k){
        int nx = x + dx4[k];
        int ny = y + dy4[k];
        dfs(nx, ny, dist + 1);
    }
    
    vis[x][y] = false;
    curPath.pop_back();
}

void DFS_for_maze(){
    init();
    dfs(sx, sy, 0);
    if (bestLen == INF){
        cout << "No path\n";
    } else {
        cout << "Shortest length(DFS) = " << bestLen << "\n";
    }
}

