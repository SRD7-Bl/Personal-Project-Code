#include "setup.hpp"
#include "maze_state.hpp"
using namespace std;

void BFS_for_maze(){
    init();
    
    
    q.push({sx,sy,0});
    //BFS
    while(!q.empty()){
        point tmp = q.front();
        q.pop();
        int x = tmp.x;
        int y = tmp.y;
        int step = tmp.step;
        
        if(!inBounds(x, y)) continue;
        if(Map[x][y] == 1) continue;
        if(vis[x][y]) continue;
        
        if(step >= bestLen) continue;
        
        if(x == ex && y == ey){
            bestLen = step;
            continue;
        }
        
        vis[x][y] = 1;
        
        for(int i=0;i<4;i++){
            int dx,dy;
            dx = x+dx4[i];
            dy = y+dy4[i];
            q.push({dx,dy,step+1});
        }
        
        //vis[x][y] = 0;
        
    }
    if (bestLen == INF){
        cout << "No path\n";
    } else {
        cout << "Shortest length(BFS) = " << bestLen << "\n";
    }
}
