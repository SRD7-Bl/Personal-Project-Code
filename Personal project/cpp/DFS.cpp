/*
 
 t：动画步数（每输出一个事件就 +1，保证你 GUI 的 step label 每帧都涨）
 op：事件类型（先用这几个就够了）
     meta：迷宫基本信息（只写一次）
     frontier_add：加入待探索（队列里）
     set_current：当前处理的格子
     visited_add：处理完/确认探索过
     found：到达终点
     done：结束（可选）
 x,y：格子坐标（行列）
 dist：从起点到这个格子的 BFS 距离（不是动画步数）
 
 */

#include "setup.hpp"
#include "maze_state.hpp"
using namespace std;


static void emit_event(ofstream& out, int& tick, const string& op, int x,int y,int dist){
    ++tick;
    out << "{\"t\":" << tick
    << ",\"op\":\"" << op << "\""
        << ",\"x\":" << x
        << ",\"y\":" << y
        << ",\"dist\":" << dist
        << "}\n";
}

void dfs(int x, int y, int dist, ofstream& out, int& tick){
    
    if (!inBounds(x, y)) return; //out of bound
    if (Map[x][y] == 1) return; //wall
    if (vis[x][y]) return; //already been

    if (dist >= bestLen) return;

    vis[x][y] = true;
    curPath.push_back({x, y});
    emit_event(out, tick, "set_current", x, y, dist);
    emit_event(out, tick, "path_push", x, y, dist);
    emit_event(out, tick, "visited_add", x, y, dist);

    // at the endpoint
    if (x == ex && y == ey){
        bestLen = dist;
        bestPath = curPath;
        
        emit_event(out, tick, "found", x, y, dist);
        
        emit_event(out, tick, "path_pop", x, y, dist);
        vis[x][y] = false;
        curPath.pop_back();
        return;
    }
    
    for (int k = 0; k < 4; ++k){
        int nx = x + dx4[k];
        int ny = y + dy4[k];
        dfs(nx, ny, dist + 1,out,tick);
        //emit_event(out, tick, "frontier_add", nx, ny, dist + 1);
    }
        
    emit_event(out, tick, "path_pop", x, y, dist);
    vis[x][y] = false;
    curPath.pop_back();
}

void DFS_for_maze(string out_dir){
    init();
    
    filesystem::path out_path = filesystem::path(out_dir) / "dfs_events.jsonl";
    ofstream out(out_path,ios::out|ios::trunc);
    int tick = 0;
    
    //initial state (Meta)
    ++tick;
        out << "{\"t\":" << tick
            << ",\"op\":\"meta\""
            << ",\"n\":" << n
            << ",\"m\":" << m
            << ",\"sx\":" << sx
            << ",\"sy\":" << sy
            << ",\"ex\":" << ex
            << ",\"ey\":" << ey
            << "}\n";
    
    dfs(sx, sy, 0,out,tick);
    emit_event(out, tick, "done", -1, -1, bestLen == INF ? -1 : bestLen);
    out.close();
    if (bestLen == INF){
        cout << "No path\n";
    } else {
        cout << "Shortest length(DFS) = " << bestLen << "\n";
    }
}

