#include "maze_state.hpp"
#include "setup.hpp"
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

static inline int h_manhattan(int x,int y){ //Cost Function h(x)
    return abs(x - ex) + abs(y - ey);
}

struct node{
    int f,g;
    int x,y;
};

// priority_queue: min-heap
struct Cmp{
    bool operator()(const node& a, const node& b)const {
        if(a.f != b.f) return a.f > b.f;
        return a.g > b.g;
    }
};

vector<pair<int,int>> AStar_shortest_path(string out_dir){
    init();
    
    filesystem::path out_path = filesystem::path(out_dir) / "astar_events.jsonl";
    ofstream out(out_path,ios::out|ios::trunc);
    int tick = 0;

    // meta（一次）
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
    
    static int g[MAXN][MAXN]; //Cost function g(x)
    static pair<int ,int> parent[MAXN][MAXN];
    
    for(int i=0;i<n;i++){
        for(int j=0;j<m;j++){
            g[i][j] = INF;
            parent[i][j] = {1,-1};
        }
    }

    g[sx][sy] = 0;
    parent[sx][sy] = {sx,sy};
    
    priority_queue<node, vector<node>, Cmp> pq;
    pq.push({h_manhattan(sx, sy),0,sx,sy});
    emit_event(out, tick, "frontier_add", sx, sy, 0);
    
    while(!pq.empty()){
        node cur = pq.top();
        pq.pop();
        
        int x = cur.x;
        int y = cur.y;
        
        emit_event(out, tick, "set_current", x, y, cur.g);
        
        if(!inBounds(x,y)) continue;
        if(Map[x][y] == 1) continue;
        
        if(vis[x][y]) continue;
        if(cur.g != g[x][y]) continue;
        vis[x][y] = 1;
        
        emit_event(out, tick, "visited_add", x, y, cur.g);
        
        if(x == ex && y == ey){
            emit_event(out, tick, "found", x, y, cur.g);
            break;
        }
        
        for(int i=0;i<4;i++){
            int nx,ny;
            nx = x+dx4[i];
            ny = y+dy4[i];
            if(!inBounds(nx, ny)) continue;
            if(Map[nx][ny] == 1) continue;
            
            int raw_g = g[x][y] + 1;
            if(raw_g < g[nx][ny]){
                g[nx][ny] = raw_g;
                parent[nx][ny] = {x,y};
                int f = raw_g + h_manhattan(nx,ny);
                pq.push({f,raw_g,nx,ny});
                emit_event(out, tick, "relax", nx, ny, raw_g, x,y);
            }
        }
    }
    
    if(g[ex][ey] == INF) return {};
    
    vector<pair<int,int>> path;
    int cx = ex, cy = ey;
    while(1){
        path.push_back({cx,cy});
        auto p = parent[cx][cy];
        if(p.first == cx && p.second == cy) break;
        cx = p.first;
        cy = p.second;
    }
    reverse(path.begin(), path.end());
    
    emit_event(out, tick, "done", -1, -1, (g[ex][ey] == INF ? -1 : g[ex][ey]));
    out.close();
    
    return path;
    
};
