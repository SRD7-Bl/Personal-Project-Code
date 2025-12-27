
#include "setup.hpp"
#include "mazecode.hpp"
#include "maze_state.hpp"

using namespace std;

static string Q(const string& s){
    return "\"" + s + "\"";
}

void launch_gui(){
    const string py = "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3";
    
    filesystem::path gui = filesystem::path("python") / "GUI_Animation.py";
    //filesystem::path events = filesystem::path("out") / (algo + "_events.jsonl");
    
    filesystem::path bfs = filesystem::path("out") / "bfs_events.jsonl";
    filesystem::path dfs = filesystem::path("out") / "dfs_events.jsonl";
    filesystem::path astar = filesystem::path("out") / "astar_events.jsonl";
    
    
    if(!filesystem::exists(gui)){cerr<<"GUI script not found: "<<gui<<endl;return ;}
    if(!filesystem::exists(bfs)){cerr<<"Events not found: "<<bfs<<endl;return ;}
    if(!filesystem::exists(dfs)){cerr<<"Events not found: "<<dfs<<endl;return ;}
    if(!filesystem::exists(astar)){cerr<<"Events not found: "<<astar<<endl;return ;}
    
    string cmd = Q(py)+" "+Q(gui.string())+
                " --maze "+Q("data/ScannedMaze.txt")+
                " --pane "+Q("BFS:"+bfs.string())+
                " --pane "+Q("ASTAR:"+astar.string())+
                " --pane "+Q("DFS:"+dfs.string());
    
    int rc = system(cmd.c_str());
    if(rc != 0) cerr<<"Failed to launch GUI, rc= "<<rc<<endl;
}

int main(int argc, char* argv[]){
    char buf[PATH_MAX];
    getcwd(buf, sizeof(buf));
    std::cout << "CWD = " << buf << "\n";
    
    for (auto& p : std::filesystem::directory_iterator(".")) {
        std::cout << " - " << p.path().filename().string() << "\n";
    }
    
    string maze = (argc >= 2) ? argv[1] : "data/ScannedMaze.txt";
    string outp = (argc >= 3) ? argv[2] : "out";
    
    //string maze_path = "./ScannedMaze.txt";
    if(!readMazeFromFile(maze)){
        return 1;
    }
    
    std::filesystem::create_directories(outp);
    
    
    DFS_for_maze(outp);
    BFS_for_maze(outp);
    auto path = AStar_shortest_path(outp);
    if (path.empty()) {
        std::cout << "A*: No path\n";
    } else {
        std::cout << "A*: shortest length = " << (int)path.size() - 1 << "\n";
    }
    
    launch_gui();

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
