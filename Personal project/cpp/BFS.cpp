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

static void emit_event(ofstream& out, int& tick, const string& op, int x,int y,int dist,int px = -1,int py = -1){
    ++tick;
    out << "{\"t\":" << tick
    << ",\"op\":\"" << op << "\""
        << ",\"x\":" << x
        << ",\"y\":" << y
        << ",\"dist\":" << dist
        << ",\"px\":" << px
        << ",\"py\":" << py
        << "}\n";
}

void BFS_for_maze(string out_dir){
    init();
    vector<vector<int>> seen(n,vector<int>(m,0));
    vector<vector<pair<int,int>>> parent(n,vector<pair<int,int>>(m,{-1,-1}));
    
    filesystem::path out_path = filesystem::path(out_dir) / "bfs_events.jsonl";
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
    q.push({sx,sy,0});
    seen[sx][sy] = 1;
    parent[sx][sy] = {sx,sy};
    emit_event(out, tick, "frontier_add", sx,sy,0,sx,sy);
    
    //BFS
    while(!q.empty()){
        point tmp = q.front();
        q.pop();
        int x = tmp.x;
        int y = tmp.y;
        int step = tmp.step;
        
        //if(step >= bestLen) continue;
        
        emit_event(out,tick,"set_current",x,y,step);
        emit_event(out,tick,"visited_add",x,y,step);
        
        if(x == ex && y == ey){
            bestLen = step;
            emit_event(out,tick,"found",x,y,step);
            break;
        }
        
        vis[x][y] = 1;
        
        for(int i=0;i<4;i++){
            int dx,dy;
            dx = x+dx4[i];
            dy = y+dy4[i];
            
            if(!inBounds(dx, dy)) continue;
            if(Map[dx][dy] == 1) continue;
            if(seen[dx][dy]) continue;
            
            seen[dx][dy] = 1;
            parent[dx][dy] = {x,y};
            q.push({dx,dy,step+1});
            
            emit_event(out, tick, "frontier_add", dx, dy, step+1,x,y);
        }
        
        //vis[x][y] = 0;
    }
    emit_event(out, tick, "done", -1, -1, (bestLen == INF ? -1 : bestLen));
    out.close();
    if (bestLen == INF){
        cout << "No path\n";
    } else {
        cout << "Shortest length(BFS) = " << bestLen << "\n";
    }
}
