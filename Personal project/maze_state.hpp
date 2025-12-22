#pragma once
#include "setup.hpp"

const int MAXN = 100;
const int INF  = 1e9;

extern int n, m;
extern int Map[MAXN][MAXN];
extern int sx, sy, ex, ey;

extern int dx4[4];
extern int dy4[4];

extern bool vis[MAXN][MAXN];
extern int bestLen;

extern std::vector<std::pair<int,int>> curPath, bestPath;

struct point{int x,y,step;};
extern std::queue<point> q;

inline bool inBounds(int x, int y){ //use inline to prevent duplicate symbols
    return (0 <= x && x < n && 0 <= y && y < m);
}

void init();
void readMaze();
