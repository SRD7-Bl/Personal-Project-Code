import subprocess, sys, os

CPP_EXE = "/Users/leo/Library/Developer/Xcode/DerivedData/Personal_project-fnyxausvjmzjsyeonbemxfudzrow/Build/Products/Debug/Personal project"

EVENTS_FILE = "./bfs_events.jsonl"

#/Users/leo/Library/Developer/Xcode/DerivedData/Personal_project-fnyxausvjmzjsyeonbemxfudzrow/Build/Products/Debug

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    
    print("Running C++ solver...")
    subprocess.run([CPP_EXE], check=True)
    
    print("Launching GUI...")
    subprocess.run([sys.executable, "GUI_Animation.py", "--events", EVENTS_FILE], check=True)

if __name__ == "__main__":
    main()
    
