#include "maze_state.hpp"
#include "setup.hpp"
using namespace std;

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

vector<pair<int,int>> AStar_shortest_path(){
    init();
    
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
    
    while(!pq.empty()){
        node cur = pq.top();
        pq.pop();
        
        int x = cur.x;
        int y = cur.y;
        
        if(!inBounds(x,y)) continue;
        if(Map[x][y] == 1) continue;
        
        if(vis[x][y]) continue;
        vis[x][y] = 1;
        
        if(x == ex && y == ey){
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
    return path;
    
};
