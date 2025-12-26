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

bool readMazeFromFile(const std::string& path){
    /*
    std::cerr << "PATH(raw) = [" << path << "]\n";
    std::cerr << "PATH(len) = " << path.size() << "\n";
    std::cerr << "PATH(bytes)= ";
    for (unsigned char c : path) {
        std::cerr << std::hex << std::setw(2) << std::setfill('0') << (int)c << " ";
    }
    std::cerr << std::dec << "\n";

    std::error_code ec;
    bool ex = std::filesystem::exists(path, ec);
    std::cerr << "exists? " << ex << "  ec=" << ec.message() << "\n";
    */
    std::ifstream in(path);
    if(!in.is_open()){
        std::cerr<<"[readMazeFromFile]: Cannot open the file: "<<path<<"\n";
        return false;
    }
    
    if(!(in>>n>>m)){
        std::cerr<<"[readMazeFromFile]: Wrong header: "<<n<<","<<m<<"\n";
        return false;
    }
    init();
    
    for(int i=0;i<n;i++){
           for(int j=0;j<m;j++){
               int v;
               if(!(in>>v)){
                   std::cerr<<"[readMazeFromFile]: Wrong cells at ("<<i<<","<<j<<")\n";
                   return false;
               }
               Map[i][j] = v;
               if(Map[i][j] == 4){ sx=i; sy=j; }
               if(Map[i][j] == 3){ ex=i; ey=j; }
           }
       }
    return true;
}

void init(){
    memset(vis,0,sizeof(vis));
    bestLen = INF;
    curPath.clear();
    bestPath.clear();
    while(!q.empty())q.pop();
}

