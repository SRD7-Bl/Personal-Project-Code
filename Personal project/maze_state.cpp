#include "maze_state.hpp"

int n, m;
int Map[MAXN][MAXN];
int sx, sy, ex, ey;

int dx4[4] = {1, 0, -1, 0};
int dy4[4] = {0, 1, 0, -1};

bool vis[MAXN][MAXN];
int bestLen = INF;

std::vector<std::pair<int,int>> curPath, bestPath;
std::queue<point> q;
//std::vector<std::pair<int,int>> AStar_shortest_path();

void init(){
    memset(vis,0,sizeof(vis));
    bestLen = INF;
    curPath.clear();
    bestPath.clear();
    while(!q.empty())q.pop();
}
void readMaze(){
    std::cin>>n>>m;
    for(int i=0;i<n;i++){
           for(int j=0;j<m;j++){
               std::cin >> Map[i][j];
               if(Map[i][j] == 4){ sx=i; sy=j; }
               if(Map[i][j] == 3){ ex=i; ey=j; }
           }
       }
}
